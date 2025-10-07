import time
import threading
import rospy
from robot_v3.msg import Goal_v3
from geometry_msgs.msg import PoseStamped
from tf.transformations import quaternion_from_euler
from std_msgs.msg import String
import uuid
import schedule
import subprocess
import argparse
from types import SimpleNamespace

from robot_v5 import mqttClient
from robot_v5 import rosSub
from robot_v5 import httpClient
from robot_v5 import dataInfo
#import httpServer
from robot_v5 import encryption
from robot_v5 import qrCode
from robot_v5 import elevatorFlowGetter
from robot_v5 import fetchTask
from robot_v5 import timeoutMonitor
from robot_v5 import vendingMqtt

from flask import Flask, jsonify
from werkzeug.serving import make_server
from threading import Thread


#后台指定的参数
ROBOTID = "18950214603"
PRIVATE_KEY = "z/CszPJh61yWfA1eJhmDKg=="
IV_VECTOR = "tBPz/vp+8x9ps4ikCj6btA=="

#ROBOTID = ""
#PRIVATE_KEY = ""
#IV_VECTOR = ""

STATIONID = "18839843720"

#控制参数
HEARTBEAT = 5 #控制MQTT 状态话题的周期性发送 & 跟后台发送请求的周期

#连接参数
VENDING_BROKER = "192.168.1.5"
BROKER_HOST = "10.25.0.17"
BROKER_PORT = 1883
HTTP_HEAD = "http"
BACKEND_HOST = "10.25.0.17"   # "192.168.10.164"
BACKEND_PORT = "18001"        # "8889"

#ROS 发布话题名
TOPIC_GOAL = "goal_v3"



class MqttThread(threading.Thread):
    def __init__(self, robot_mqtt, heartbeat, stop_event: threading.Event):
        """
        这个线程控制机器人持续性向后台上报自己的状态消息
        参数:
            robot_mqtt: 已初始化并且连接 MQTT broker的客户端实例, 用于发布状态消息
            stop_event: 线程终止事件标志
        """
        super().__init__(daemon=True)
        self.robot_mqtt = robot_mqtt
        self.stop_event = stop_event
        self.heartbeat = heartbeat

    def run(self):
        """
        要先判断MQTTclient有没有成功连接到broker, 然后再开始运行!
        每间隔 HEARTBEAT 时间 发布一次 robots/{robotId}/state 主题消息
        """

        rospy.loginfo("Waiting for MQTT connection...")
        while not self.robot_mqtt.connected and not self.stop_event.is_set() and not rospy.is_shutdown():
            time.sleep(0.1)

        rospy.loginfo("MQTT connected. Starting state publish loop.")

        while not self.stop_event.is_set() and not rospy.is_shutdown():
            try:
                self.robot_mqtt.publish_state()
            except Exception as e:
                rospy.logwarn(f" <executor-87> MQTT error: {e}\n")
            
            self.stop_event.wait(self.heartbeat)


class InteractionThread(threading.Thread):
    def __init__(self, robotState: dataInfo.RobotStateInfo, instructionInfo: dataInfo.InstructionInfo, 
                 http_client: httpClient.HttpClient, programStatus: dataInfo.ProgramStatus,
                 elevatorControl: dataInfo.ElevatorControl, statusBackend: dataInfo.StatusBackend,
                 currentOrder: dataInfo.CurrentOrder, ros_pub_goal, vending_mqtt, stop_event: threading.Event):
        """
        这个线程主要用于逻辑控制和不同系统之间的交互
        """
        super().__init__(daemon=True)

        self.robotState = robotState
        self.instructionInfo = instructionInfo
        self.programStatus = programStatus
        self.elevatorControl = elevatorControl
        self.statusBackend = statusBackend
        self.currentOrder = currentOrder

        self.ros_pub_goal = ros_pub_goal
        self.http_client = http_client
        self.stop_event = stop_event
        self.vending_mqtt = vending_mqtt

        #控制电梯流程需要的参数
        self.elevatorGettter = None
        self.elevatorStatus = 0

        #机器人从后台获取任务需要的参数
        self.fetchTask = None

        #超时计时器需要的参数
        self.timeoutMonitor = timeoutMonitor.TimeoutMonitor(owner=self)
        self.relocalization_timeout = 30
        self.move_timeout = 3000
        self.elevator_timeout = 3000

        self.scheduler = schedule.Scheduler()
        self.job = None

    def logic(self):
        """
        逻辑执行部分
        先看程序状态和机器人状态
        1) 机器人状态为 rest (待机/睡眠状态)
            1-1) 程序状态为 reset_address    #重定位指令
            1-2) 程序状态为 move             #移动指令
            1-3) 程序状态为 execute_command  #执行特殊指令
            1-4) 程序状态为 stop             #停止运动指令
        2) 机器人状态为 idle (空闲状态)
        3) 机器人状态为 task (执行任务状态)
            3-1) 程序状态为 assigned         #有任务要执行
            3-2) 程序状态为 arrived          #到达目的地
            3-3) 程序状态为 cargo_delivery   #要跟vending machine交互来下货
            3-4) 程序状态为 delivered/ delivered_failed     #送完货(成功/失败)
        4) 机器人状态为 back (返回目的地状态)
            程序状态在 ["delivered", "delivered_failed", "restock", "cancel_delivery"]里面才能返回
        5) 机器人状态为 exce (异常状态)
        """
        if self.stop_event.is_set() or rospy.is_shutdown():
            return schedule.CancelJob

        try:
            robotState = self.robotState.get_state()
            if robotState is None:
                rospy.logwarn("<executor-155> robotState is None, skip this tick.")
                return
            
            robotStatus = robotState.get("robotStatus")
            programStatus = self.programStatus.get_programStatus()
            rospy.loginfo(f"\nrobotStatus: {robotStatus}; programStatus: {programStatus}\n")

            if robotStatus == "rest":
                self.finalize_task()

                if programStatus == "reset_address":
                    self.timeoutMonitor.record(startStatus="reset_address", stopStatus="reset_success", timeout=self.relocalization_timeout)
                    self.relocalization_handler(programStatus_old=programStatus)
                    
                elif programStatus == "move":
                    self.timeoutMonitor.record(startStatus="move", stopStatus="move_complete", timeout=self.move_timeout)
                    positions = self.instructionInfo.get_movePositions()
                    self.move_handler(taskId=None, positions=positions)
                    
                elif programStatus == "execute_command":
                    self.command_handler()

                elif programStatus == "reset_success" or programStatus == "reset_failure":
                    self.timeoutMonitor.cancel_record(startStatus="reset_address")
                    self.finalize_relocalization_handler()

                elif programStatus == "move_complete":
                    self.timeoutMonitor.cancel_record(startStatus="move")
                    self.finalize_move_handler()

                elif programStatus == "execute_command_complete":
                    self.finalize_command_handler()
                
                elif programStatus == "stop":
                    self.publish_goal(goal_pos=None, goal_floor="", goal_house="", relocation=False, programStatus_old=programStatus, stop=True)
                    self.instructionInfo.reset_movePositions() #如果触发stop, 则没有执行完的目标点位全都清空.

            if robotStatus == "idle":
                if not self.fetchTask:
                    try:
                        self.fetchTask = fetchTask.FetchTask(owner=self)
                        self.fetchTask.start()
                    except Exception as e:
                        rospy.loginfo(f"\n<executor-198> Error: {e}\n")
            
            if robotStatus == "task":

                try:
                    currentOrder_info = self.currentOrder.get_currentOrder()
                    goal_positions = currentOrder_info.get("goal_positions")
                    taskId = currentOrder_info.get("taskId")
                    code = currentOrder_info.get("code")
                    delivery_info = currentOrder_info.get("delivery_info")
                except Exception as e:
                    rospy.loginfo(f"\n<executor-209> Error in READ GOAL: {e}\n")
                
                if programStatus == "assigned":
                    self.timeoutMonitor.record(startStatus="assigned", stopStatus="arrived", timeout=self.move_timeout)
                    self.move_handler(taskId=taskId, positions=goal_positions)

                if programStatus == "arrived":
                    self.timeoutMonitor.cancel_record(startStatus="assigned")
                    self.arrived_handler(taskId=taskId, code=code)
                    self.robotState.update_robotTaskId(0)

                if programStatus == "cargo_delivery":
                    self.cargoDelivery_handler(delivery_info=delivery_info)
                
                if programStatus == "delivered" or programStatus == "delivered_failed":
                    robot_floor = self.robotState.get_state().get("floor")
                    robot_house = self.robotState.get_state().get("house")
                    self.delivered_handler(taskId=0, robot_floor=robot_floor, robot_house=robot_house)
                    
            if robotStatus == "back":
                programStatus = self.programStatus.get_programStatus()
                startStatus = programStatus

                if programStatus in ["delivered", "delivered_failed", "restock", "cancel_delivery"]:
                    try:
                        currentOrder_info = self.currentOrder.get_currentOrder()
                        return_positions = currentOrder_info.get("return_positions")
                    except Exception as e:
                        rospy.loginfo(f"\n<executor-237> Error in READ GOAL: {e}\n")

                    self.timeoutMonitor.record(startStatus=startStatus, stopStatus="back_arrived", timeout=self.move_timeout)
                    self.move_handler(taskId=None, positions=return_positions)

                if programStatus == "back_arrived":
                    self.timeoutMonitor.cancel_record(startStatus=startStatus)
                    self.robotState.update_robotStatus("idle")

            if robotStatus == "exce":
                programStatus = self.programStatus.get_programStatus()
                taskId = self.robotState.get_state().get("robotTaskId")
                self.toBackend_reportWarn(taskId=taskId, type=programStatus)
                self.timeoutMonitor.clear_record()
                self.instructionInfo.reset_movePositions()
                self.finalize_task()
            
        
        except Exception as e:
            rospy.loginfo(f"\n<executor-256> Error in Interaction thread: {e}\n")
                
    def run(self):
        """
        控制逻辑执行部分定时执行
        """
        self.job = self.scheduler.every(2).seconds.do(self.logic)

        while not self.stop_event.is_set() and not rospy.is_shutdown():
            self.scheduler.run_pending()
            self.stop_event.wait(0.1)

        # 清理
        if self.job:
            try:
                self.scheduler.cancel_job(self.job)
            except Exception:
                pass
            self.job = None

    def position_transform(self, position):
        """
        这个函数用来把普通坐标点转换成tianxin可以直接用的pose
        参数:
            position: {"x": float, "y": float, "theta": float}
        返回:
            一个 PoseStamped 对象
        """
        ps = PoseStamped()
        ps.header.stamp = rospy.Time.now()
        ps.header.frame_id = "map"
        ps.pose.position.x = position["x"]
        ps.pose.position.y = position["y"]
        ps.pose.position.z = 0.0

        q = quaternion_from_euler(0.0, 0.0, position["theta"])
        ps.pose.orientation.x = q[0]
        ps.pose.orientation.y = q[1]
        ps.pose.orientation.z = q[2]
        ps.pose.orientation.w = q[3]

        return ps

    def publish_goal(self, goal_pos, goal_floor, goal_house, relocation, programStatus_old, stop=False):
        """
        给tianxin发布他规划路径需要的数据
        参数:
            outside_lift: 电梯外面的坐标
            inside_lift: 电梯内部的坐标
            final_position: 最后机器人需要到达的坐标
            final_floor: 最后机器人需要到达的楼层
        """
        goal = Goal_v3()
        
        if goal_pos is None:
            goal.pose = PoseStamped()
        else:
            goal.pose = self.position_transform(goal_pos)
        
        goal.floor = goal_floor
        goal.house = goal_house
        goal.relocation = relocation
        goal.stop = stop
        self.ros_pub_goal.publish(goal)
        rospy.loginfo(f"\n Forwarded the goal info to the planning part \n {goal}\n")
        self.publish_goal_wait(programStatus_old=programStatus_old)
        
    def publish_goal_wait(self, programStatus_old):
        """
        控制每0.1秒检查一次状态
        如果tianxin没有给我发接收到目标地址的信号, 则超时后将重发
        """
        rate = rospy.Rate(10) 
        waited = 0
        while waited < 1:
                            
            if self.stop_event.is_set() or rospy.is_shutdown():
                break
                            
            programStatus_new = self.programStatus.get_programStatus()
            if programStatus_new != programStatus_old:
                break

            rate.sleep()
            waited += 0.1

    def toBackend_reportWarn(self, taskId, type):
        """
        机器人遇到各种故障或者错误无法解决, 则上报给后台进行人为处理.
        参数:
            taskId: 当前执行的任务ID.
            type: 遇到的错误/故障类型
        """
        response = self.http_client.report_warn(taskId=taskId, type=type)

    def toBackend_photo(self):
        """
        这个函数的作用是控制机器人在关键节点拍照片, 上传到后台
        """
        try:
            response = self.http_client.report_image()
        except Exception as e:
            rospy.loginfo(f"\n<executor-358> error happens: {e}\n")

    def toBackend_notify(self, taskId, taskStatus):
        """
        这个函数的作用是:
            1. 调用<接口2>, 通知后台机器人的状态
        """
        try:
            response = self.http_client.update_taskStatus(taskId=taskId, taskStatus=taskStatus)
            rospy.loginfo(f"\nnotify backend with {taskStatus} \n get: {response} \n")
        except Exception as e:
            rospy.loginfo(f"\n<executor-369> error happens: {e}\n")
        
        if taskStatus == dataInfo.TaskStatus.DELIVERY_COMPLETE.value:
            self.programStatus.update_programStatus("cargo_delivery")
        elif taskStatus == dataInfo.TaskStatus.DELIVERY_FAILED.value:
            self.programStatus.update_programStatus("delivered_failed")

    def relocalization_handler(self, programStatus_old):
        """
        处理重定位指令
        """
        try:
            relocalization = self.instructionInfo.get_relocalizationInfo()
            relocalization_pos = relocalization.get("relocalization_position")
            relocalization_floor = relocalization.get("floor")
            relocalization_house = relocalization.get("house")
        except Exception as e:
            rospy.loginfo(f"\n<executor-386> Error in READ GOAL: {e}\n")

        try:
            self.publish_goal(goal_pos=relocalization_pos, goal_floor=relocalization_floor , goal_house=relocalization_house , relocation=True, programStatus_old=programStatus_old)
        except Exception as e:
            rospy.loginfo(f"\n<executor-391> Error in PUBLISH GOAL: {e}\n")

    def finalize_relocalization_handler(self):
        """
        重定位指令结束后调用
        """
        self.instructionInfo.reset_relocalizationInfo()

    def move_handler(self, taskId, positions):
        """
        机器人移动调用函数, move, 送货, 返回...
        """
        for item in positions:
            robot_floor = self.robotState.get_state().get("floor")
            robot_house = self.robotState.get_state().get("house")
            to_floor = item.get("floor")
            to_pos = item.get("dock")
            to_house = item.get("house")
            programStatus = self.programStatus.get_programStatus()

            if robot_floor != to_floor or robot_house != to_house:
                self.elevatorStatus = 0
                while programStatus == "moving":
                    programStatus = self.programStatus.get_programStatus()
                self.programStatus.update_programStatus(programStatus="to_lift_outside")
                self.move_with_lift(taskId=taskId, robot_floor=robot_floor, to_pos=to_pos, to_floor=to_floor, to_house=to_house, robot_house=robot_house)
            else:
                while programStatus == "moving":
                    programStatus = self.programStatus.get_programStatus()
                self.programStatus.update_programStatus(programStatus="ready_move")
                self.move_with_lift(taskId=taskId, robot_floor=robot_floor, to_pos=to_pos, to_floor=to_floor, to_house=to_house, robot_house=robot_house)

    def finalize_move_handler(self):
        """
        机器人移动结束后调用函数接口
        """
        self.instructionInfo.reset_movePositions()

    def command_handler(self):
        """
        机器人收到指令后处理接口
        """
        command = self.instructionInfo.get_command()
        print(command)
        
        p = subprocess.Popen([
            "gnome-terminal",
            "--", "bash", "-c", f"{command}; exec bash"
        ])
        
        self.programStatus.update_programStatus("execute_command_complete") 

    def finalize_command_handler(self):
        """
        机器人指令处理完后调用的接口
        """
        self.instructionInfo.reset_command()

    def move_with_lift(self, taskId, robot_floor, to_pos, to_floor, to_house, robot_house):
        """
        跟电梯交互
        参数:
            taskId: 正在执行的任务ID, 如果没有在执行任务则为0
            robot_floor: 机器人当前位于的楼层
            to_pos: 机器人要到达的目的地坐标
            to_floor: 机器人要到达的目的地楼层
            to_house: 机器人要到达的目的地建筑
            robot_house: 机器人目前在的建筑
        """
        programStatus = self.programStatus.get_programStatus()
        uuid_str = str(uuid.uuid4())

        rate = rospy.Rate(1) #控制两秒执行一次循环

        startStatus = programStatus
        self.timeoutMonitor.record(startStatus=startStatus, stopStatus="moving", timeout=self.elevator_timeout)

        #机器人执行电梯/门禁流程的所有状态
        move_status = ["to_lift_outside", "moving_lift_outside", "to_lift_inside", "moving_lift_inside", "to_another_lift_outside", "at_lift_inside", "relocalization", "relocalizing", "ready_move"]
        
        while programStatus in move_status:

            rospy.loginfo(f"\nprogramStatus: {programStatus}; elevatorStatus: {self.elevatorStatus}\n")

            if programStatus == "to_lift_outside": #准备走向电梯门外的点位

                #向后台发初始化电梯流程请求 并更新 机器人执行任务需要的相关参数 
                ok = self.set_elevatorFlow(flowId=uuid_str, elevatorStatus=self.elevatorStatus, taskId=taskId, fromFloor=robot_floor, toFloor=to_floor, fromHouse=robot_house, toHouse=to_house)
                if not ok:
                    rospy.loginfo("\nno response from the backend\n")
                    rate.sleep()
                    continue

                #初始化使用电梯需要的参数和流程接口
                self.elevatorControl.update_basicInfo(robotId=ROBOTID, taskId=taskId)
                self.elevatorControl.update_floorInfo(fromFloor=robot_floor, toFloor=to_floor)
                
                try:
                    elevatorControlParams = self.elevatorControl.get_elevatorControlParams()
                    ele_out_pos = elevatorControlParams.get("fromElevatorOutAddress").get("pose").get("dock")
                    ele_out_floor = elevatorControlParams.get("fromElevatorOutAddress").get("floor")
                    ele_out_house = elevatorControlParams.get("fromElevatorOutAddress").get("house")
                except Exception as e:
                    rospy.loginfo(f"\n <Executor-494> Error in reading 'fromElevatorOutAddress': {e}\n")

                #启动从后台获取电梯状态的进程
                if not self.elevatorGettter:
                    try:
                        self.elevatorGettter = elevatorFlowGetter.ElevatorFlowGetter(owner=self, flow_id=uuid_str, period=5)
                        self.elevatorGettter.start()
                    except Exception as e:
                        rospy.loginfo(f"\n<executor-502> start ElevatorFlowGetter failed: {e}\n")

                #向planning部分发目的坐标, 目标接收成功, 机器人改为状态 [moving_lift_outside]-[机器人正在赶往电梯口]
                try:
                    self.publish_goal(goal_pos=ele_out_pos, goal_floor=ele_out_floor, goal_house=ele_out_house, relocation=False, programStatus_old=programStatus)
                except Exception as e:
                    rospy.loginfo(f"\n<executor-508> Error in PUBLISH GOAL: {e}\n")

                programStatus = self.programStatus.get_programStatus()

                #目标接收成功 [机器人正在赶往电梯口](10), 更新电梯状态为[10], 通知后台
                if programStatus == "moving_lift_outside":
                    self.elevatorStatus = 10
                    self.set_elevatorFlow(flowId=uuid_str, elevatorStatus=self.elevatorStatus, taskId=taskId, fromFloor=robot_floor, toFloor=to_floor, fromHouse=robot_house, toHouse=to_house)

            if programStatus == "to_lift_inside": #到达电梯外部坐标, 准备走进电梯内部

                #到达电梯门口 且 收到 [电梯门打开](40) 的信号
                if self.elevatorStatus == 40:
                    #拍照
                    self.toBackend_photo()
                    
                    try:
                        elevatorControl = self.elevatorControl.get_elevatorControlParams()
                        ele_in_pos = elevatorControl.get("fromElevatorInAddress").get("pose").get("dock")
                        ele_in_floor = elevatorControl.get("fromElevatorInAddress").get("floor")
                        ele_in_house = elevatorControl.get("fromElevatorInAddress").get("house")
                    except:
                        rospy.loginfo(f"\n <executor-530> Error in reading 'fromElevatorInAddress': {e}\n")

                    #通知planning部分 机器人可以开始向电梯内部走, 待目标接收成功, 机器人状态改为 [moving_lift_in]-[机器人正在赶往电梯内部]
                    try:
                        self.publish_goal(goal_pos=ele_in_pos, goal_floor=ele_in_floor, goal_house=ele_in_house, relocation=False, programStatus_old=programStatus)
                    except Exception as e:
                        rospy.loginfo(f"\n<executor-536> Error in PUBLISH GOAL: {e}\n")
                    
                    programStatus = self.programStatus.get_programStatus()
                    
                    #目标接收成功 [机器人正在赶往电梯内部](50), 更新电梯状态为[50], 通知后台
                    if programStatus == "moving_lift_inside":
                        self.elevatorStatus = 50
                        self.set_elevatorFlow(flowId=uuid_str, elevatorStatus=self.elevatorStatus, taskId=taskId, fromFloor=robot_floor, toFloor=to_floor, fromHouse=robot_house, toHouse=to_house)
                
                #到达电梯门口 还没收到 电梯门已开 的信号, 所以要发送 [已到达电梯口](20) 的命令
                elif self.elevatorStatus == 10:
                    self.elevatorStatus = 20
                    self.set_elevatorFlow(flowId=uuid_str, elevatorStatus=self.elevatorStatus, taskId=taskId, fromFloor=robot_floor, toFloor=to_floor, fromHouse=robot_house, toHouse=to_house)
                    #拍照
                    self.toBackend_photo()

                elif self.elevatorStatus == 20 or self.elevatorStatus == 30:
                    
                    elevatorControl = self.elevatorControl.get_elevatorControlParams()
                    ele_out_pos_new = elevatorControl.get("fromElevatorOutAddress").get("pose").get("dock")

                    if ele_out_pos != ele_out_pos_new:
                        ele_out_pos = ele_out_pos_new

                        self.programStatus.update_programStatus(programStatus="to_another_lift_outside")

                        try:
                            self.publish_goal(goal_pos=ele_out_pos_new, goal_floor=ele_out_floor, goal_house=ele_out_house, relocation=False, programStatus_old=programStatus)
                        except Exception as e:
                            rospy.loginfo(f"\n<executor-565> Error in PUBLISH GOAL: {e}\n")

            if programStatus == "at_lift_inside" and self.elevatorStatus == 50: #机器人在电梯内部并且刚才的状态是[正在赶往电梯]

                #通知后台机器人已到达电梯内部
                self.elevatorStatus = 60
                self.set_elevatorFlow(flowId=uuid_str, elevatorStatus=self.elevatorStatus, taskId=taskId, fromFloor=robot_floor, toFloor=to_floor, fromHouse=robot_house, toHouse=to_house)
                
                #更新机器人自身的状态为 等待重定位 [idle_relocation] 或者 [return_relocation]
                self.programStatus.update_programStatus("relocalization")

            if programStatus == "relocalization" and self.elevatorStatus == 80: #机器人处于可以发生重定位的状态并且电梯门已开

                #首先更新机器人现在所在的 [楼层] 和 [楼]
                self.robotState.update_position(floor=to_floor, house=to_house)
                robot_floor = self.robotState.get_state().get("floor")
                robot_house = self.robotState.get_state().get("house")

                try:
                    elevatorControl = self.elevatorControl.get_elevatorControlParams()
                    relocalization_pos = elevatorControl.get("toElevatorInAddress").get("pose").get("dock")
                    relocalization_floor = elevatorControl.get("toElevatorInAddress").get("floor") 
                    relocalization_house = elevatorControl.get("toElevatorInAddress").get("house")
                except Exception as e:
                    rospy.loginfo(f"\n <Executor-589> Error in reading relocalization: {e}\n")
                
                #拍照
                self.toBackend_photo()   

                #给planning部分发送重定位信息, 待目标接收成功, 机器人状态改为 [idle_inLift]/[return_inLift]-[机器人正在重置地图]
                try:
                    self.publish_goal(goal_pos=relocalization_pos, goal_floor=relocalization_floor, goal_house=relocalization_house, relocation=True, programStatus_old=programStatus)
                except Exception as e:
                    rospy.loginfo(f"\n<executor-598> Error in PUBLISH GOAL: {e}\n")
                
                self.timeoutMonitor.record(startStatus="relocalization", stopStatus="ready_move", timeout=self.relocalization_timeout)
                programStatus = self.programStatus.get_programStatus()

                #目标接收成功 [机器人正在重置地图](90), 更新电梯状态为[90], 通知后台
                if programStatus == "relocalizing":
                    self.elevatorStatus = 90
                    self.set_elevatorFlow(flowId=uuid_str, elevatorStatus=self.elevatorStatus, taskId=taskId, fromFloor=robot_floor, toFloor=to_floor, fromHouse=robot_house, toHouse=to_house)
                     #拍照
                    self.toBackend_photo()

            #机器人重置地图成功
            if programStatus == "ready_move":
                
                #用了电梯系统的话, 需要向后台更新电梯状态 [机器人重置地图成功](100)
                if self.elevatorStatus == 90:
                    self.timeoutMonitor.cancel_record(startStatus="relocalization")
                    self.elevatorStatus = 100
                    self.set_elevatorFlow(flowId=uuid_str, elevatorStatus=self.elevatorStatus, taskId=taskId, fromFloor=robot_floor, toFloor=to_floor, fromHouse=robot_house, toHouse=to_house)

                #用了电梯系统的话, 需要把这个[同步更新后台的电梯状态]的线程关掉
                if self.elevatorGettter:
                    try:
                        self.elevatorGettter.stop()
                    except Exception:
                        pass
                    finally:
                        self.elevatorGettter = None

                try:
                    self.publish_goal(goal_pos=to_pos, goal_floor=to_floor, goal_house=to_house, relocation=False, programStatus_old=programStatus)
                except Exception as e:
                    rospy.loginfo(f"\n<executor-631> Error in PUBLISH GOAL: {e}\n")

            programStatus = self.programStatus.get_programStatus()
            rate.sleep()

        #如果 [elevatorFlowGetter线程] 没关就要关掉
        if self.elevatorGettter:
            try:
                self.elevatorGettter.stop()
            except Exception:
                pass
            finally:
                self.elevatorGettter = None

        self.elevatorStatus = 0
        self.timeoutMonitor.cancel_record(startStatus=startStatus)

    def set_elevatorFlow(self, flowId, elevatorStatus, taskId, fromFloor, toFloor, fromHouse, toHouse):
        """
        用来调用接口, 与后台协调电梯使用流程, 并更新相关电梯使用参数.
        参数:
            flowId: 流程ID, 每次使用电梯固定一个值
            elevatorStatus: 电梯使用状态
            taskId: 正在执行的任务ID
            fromFloor: 机器人出发楼层
            toFloor: 机器人需要到达的楼层
        """
        response = self.http_client.set_elevatorControlFlow(flowId=flowId, elevatorStatus=elevatorStatus, robotId=ROBOTID, taskId=taskId, fromFloor=fromFloor, toFloor=toFloor, fromHouse=fromHouse, toHouse=toHouse)
        
        try:
            flow_info = response.get("data").get("flowInfo")
            elevatorStatus = flow_info.get("status")

            fromElevatorOutAddress = flow_info.get("fromElevatorOutAddress")
            fromElevatorInAddress = flow_info.get("fromElevatorInAddress")
            toElevatorOutAddress = flow_info.get("toElevatorOutAddress")
            toElevatorInAddress = flow_info.get("toElevatorInAddress")

        except Exception as e:
            rospy.loginfo(f"\n<executor-670> fetch elevator info error: {e}\n")

        if not flow_info:
            rospy.loginfo("\n no response from backend as flow info\n")
            return False

        self.elevatorStatus = elevatorStatus

        self.elevatorControl.update_fromElevatorOutAddress(fromElevatorOutAddress=fromElevatorOutAddress)
        self.elevatorControl.update_fromElevatorInAddress(fromElevatorInAddress=fromElevatorInAddress)
        self.elevatorControl.update_toElevatorOutAddress(toElevatorOutAddress=toElevatorOutAddress)
        self.elevatorControl.update_toElevatorInAddress(toElevatorInAddress=toElevatorInAddress)

        return True

    def arrived_handler(self, taskId, code):
        """
        机器人配送到达后调用的接口
        """
        self.toBackend_photo()
        self.toBackend_notify(taskId=taskId, taskStatus=dataInfo.TaskStatus.PENDING_RECEIPT.value)
        
        qr_check = self.qrCheck_handler(code)
        self.toBackend_photo()
        if qr_check:
            self.toBackend_notify(taskId=taskId, taskStatus=dataInfo.TaskStatus.DELIVERY_COMPLETE.value)
        else:
            self.toBackend_notify(taskId=taskId, taskStatus=dataInfo.TaskStatus.DELIVERY_FAILED.value)

    
    def qrCheck_handler(self, code):
        """
        核对二维码, 计时核对, 超时还没有核对成功的话就算失败
        return:
            True: 核对成功
            False: 核对失败
        """
        rate = rospy.Rate(10) 
        waited = 0
        cmd = "barcode"

        while waited < 120:
            with self.vending_mqtt.lock:
                code_get = self.vending_mqtt.scanned_code
            if code_get:
                if code == code_get:
                    data = {
                        "r": 0,
                        "c": code_get
                    }
                    self.vending_mqtt.publish_client(cmd=cmd, data=data)
                    return True
            
            rate.sleep()
            waited += 0.1

        data = {
            "r": 1,
            "c": self.vending_mqtt.scanned_code
        }
        self.vending_mqtt.publish_client(cmd=cmd, data=data)
        return False
        
    """   
    def qrCheck_handler(self, code):
    
        核对二维码, 计时核对, 超时还没有核对成功的话就算失败
        return:
            True: 核对成功
            False: 核对失败
    
        #用两分钟的时间去核对二维码
        qr_scanner = qrCode.QrCode(timeout=60)
        try:
            return qr_scanner.scan(code)
        finally:
            qr_scanner.close()
    """

    def cargoDelivery_handler(self, delivery_info):
        """
        这里处理利用MQTT吐货
        """
        
        n = []
        for item in delivery_info:
            binId = item.get("binId")
            number = item.get("number")
            for i in range(number):
                n.append(binId)
        cmd = "shipment"
        data = {
            "n": n
        }
        self.vending_mqtt.publish_client(cmd=cmd, data=data)
        self.cargo_delivery_wait(programStatus_old="cargo_delivery")
        programStatus = self.programStatus.get_programStatus()
        
                
        programStatus = self.programStatus.get_programStatus()
        if programStatus == "cargo_delivery_complete":
            self.programStatus.update_programStatus("delivered")
        else:
            self.http_client.report_image_error(type=programStatus)
            self.programStatus.update_programStatus("delivered")
            
        self.cargo_delivery_wait(programStatus_old=programStatus) # 等待用户拿货

    def cargo_delivery_wait(self, programStatus_old):
        """
        等待售卖机返回吐货结果
        """
        rate = rospy.Rate(10) 
        waited = 0
        while waited < 120:
                            
            if self.stop_event.is_set() or rospy.is_shutdown():
                break
                            
            programStatus_new = self.programStatus.get_programStatus()
            if programStatus_new != programStatus_old:
                break

            rate.sleep()
            waited += 0.1

    def delivered_handler(self, taskId, robot_floor, robot_house):
        """
        配送完成后调用的接口
        """
        response = self.http_client.select_taskInfo(taskId=taskId, floor=robot_floor, building=robot_house)
        response_code = response.get("code")
        
        if response_code == 0:
            data = response.get("data")
            taskInfo = data.get("taskInfo") or {}
            if taskInfo != {}:
                status_new = data.get("taskInfo").get("status")
                if status_new == 30 or status_new == 40 or status_new == 90:
                    self.robotState.update_robotStatus(robotStatus="idle")
            else:
                self.robotState.update_robotStatus(robotStatus="back")

    
    def finalize_task(self):
        """
        清空任务记录.
        """
        self.currentOrder.reset_currentOrder()
        self.robotState.update_robotTaskId(0)
        self.statusBackend.update_statusBackend(0, 0)
        self.elevatorStatus = 0
        self.elevatorControl.reset_elevatorControlParams()

        if self.elevatorGettter:
            try:
                self.elevatorGettter.stop()
            except Exception:
                pass
            finally:
                self.elevatorGettter = None


def main():
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--robot-id", required=True, help="Unique ID of this robot")
    parser.add_argument("--private-key", required=True, help="Encryption private key")
    parser.add_argument("--iv-vector", required=True, help="Encryption IV vector")
    args = parser.parse_args()
    
    global ROBOTID, PRIVATE_KEY, IV_VECTOR
    ROBOTID = args.robot_id
    PRIVATE_KEY = args.private_key
    IV_VECTOR = args.iv_vector
    """


    #临界资源初始化
    robotState = dataInfo.RobotStateInfo()
    instructionInfo = dataInfo.InstructionInfo()
    programStatus = dataInfo.ProgramStatus()
    elevatorControl = dataInfo.ElevatorControl()
    currentOrder = dataInfo.CurrentOrder()
    statusBackend = dataInfo.StatusBackend()
    
    #ros 初始化
    rospy.init_node("executor", anonymous=True)
    ros_pub_goal = rospy.Publisher(TOPIC_GOAL, Goal_v3, queue_size=1)
    time.sleep(0.1)

    #加密解密头部鉴权功能初始化
    httpEncryption = encryption.HttpEncryption(robotId=ROBOTID, private_key=PRIVATE_KEY, iv_vector=IV_VECTOR)

    #机器人客户端
    http_client = httpClient.HttpClient(head=HTTP_HEAD, host=BACKEND_HOST, port=BACKEND_PORT, httpEncryption=httpEncryption)

    #mqtt初始化与连接 -- 成功连接会更新机器人状态为idle
    robot_mqtt = mqttClient.MqttClient(host=BROKER_HOST, port=BROKER_PORT, station_id=STATIONID, robot_id=ROBOTID, robotState=robotState, instructionInfo=instructionInfo, programStatus=programStatus)
    robot_mqtt.connect()

    ros_sub = rosSub.RosSub(robotState=robotState, programStatus=programStatus, robot_mqtt=robot_mqtt)

    vending_mqtt = vendingMqtt.VendingMqtt(host=VENDING_BROKER, port=BROKER_PORT, sn="SN25063001", programStatus=programStatus)
    vending_mqtt.connect()

    #线程启动
    stop_event = threading.Event()
    
    mqtt_thread = MqttThread(robot_mqtt=robot_mqtt, heartbeat=HEARTBEAT, stop_event=stop_event)
    mqtt_thread.start()
    interaction_thread = InteractionThread(robotState=robotState, instructionInfo=instructionInfo, http_client=http_client, programStatus=programStatus, elevatorControl=elevatorControl, statusBackend=statusBackend, currentOrder=currentOrder, ros_pub_goal=ros_pub_goal, vending_mqtt=vending_mqtt, stop_event=stop_event)
    interaction_thread.start()


    try:
        rospy.spin()
    finally:
        #回收线程
        stop_event.set()
        mqtt_thread.join(timeout=1)
        interaction_thread.join(timeout=1)
        
        #正常退出发布离线消息
        robot_mqtt.publish_connection(status="offline", reason="shutdown")
        robot_mqtt.stop()
