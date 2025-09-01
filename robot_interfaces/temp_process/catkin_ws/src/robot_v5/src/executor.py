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

import mqttClient
import rosSub
import httpClient
import dataInfo
#import httpServer
import encryption
#import qrCode
import elevatorFlowGetter

from flask import Flask, jsonify
from werkzeug.serving import make_server
from threading import Thread


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
                rospy.logwarn(f" <executor-57> MQTT error: {e}\n")
            
            self.stop_event.wait(self.heartbeat)


class InteractionThread(threading.Thread):
    def __init__(self, robotState: dataInfo.RobotStateInfo, instructionInfo: dataInfo.InstructionInfo, 
                 http_client: httpClient.HttpClient, programStatus: dataInfo.ProgramStatus,
                 elevatorControl: dataInfo.ElevatorControl, ros_pub_goal, stop_event: threading.Event):
        
        super().__init__(daemon=True)

        self.robotState = robotState
        self.instructionInfo = instructionInfo
        self.programStatus = programStatus
        self.elevatorControl = elevatorControl

        self.ros_pub_goal = ros_pub_goal
        self.http_client = http_client
        self.stop_event = stop_event

        self.elevatorGettter = None
        self.elevatorStatus = 0

        self.scheduler = schedule.Scheduler()
        self.job = None

    def logic(self):
        """
        逻辑执行部分
        """
        if self.stop_event.is_set() or rospy.is_shutdown():
            return schedule.CancelJob

        try:
            robotStatus = self.robotState.get_state().get("robotStatus")

            if robotStatus == "rest":
                # TODO 首先清空关于执行任务的任何数据记录, 写个函数 finalize_task()

                programStatus = self.programStatus.get_programStatus()

                if programStatus == "reset_address":
                    self.relocalization_handler(programStatus_old=programStatus)
                    
                elif programStatus == "move":
                    positions = self.instructionInfo.get_movePositions()
                    self.move_handler(positions=positions)
                    
                elif programStatus == "execute_command":
                    self.command_handler()

                elif programStatus == "reset_success" or programStatus == "reset_failure":
                    self.finalize_relocalization_handler()

                elif programStatus == "move_complete":
                    self.finalize_move_handler()

                elif programStatus == "execute_command_complete":
                    self.finalize_command_handler()
        
        except Exception as e:
            rospy.loginfo(f"\n <executor-99> Error in Interaction thread: {e}\n")
                
    def run(self):
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

    def publish_goal(self, goal_pos, goal_floor, goal_house, relocation, programStatus_old):
        """
        给tianxin发布他规划路径需要的数据
        参数:
            outside_lift: 电梯外面的坐标
            inside_lift: 电梯内部的坐标
            final_position: 最后机器人需要到达的坐标
            final_floor: 最后机器人需要到达的楼层
        """
        goal = Goal_v3()

        goal.pose = self.position_transform(goal_pos)
        goal.floor = goal_floor
        goal.house = goal_house
        goal.relocation = relocation
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
        while waited < 5.0:
                            
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
            rospy.loginfo(f"\n <executor-512> error happens: {e}\n")

    def relocalization_handler(self, programStatus_old):
        try:
            relocalization = self.instructionInfo.get_relocalizationInfo()
            relocalization_pos = relocalization.get("relocalization_position")
            relocalization_floor = relocalization.get("floor")
            relocalization_house = relocalization.get("house")
        except Exception as e:
            rospy.loginfo(f"\n <executor-92> Error in READ GOAL: {e}\n")

        try:
            self.publish_goal(goal_pos=relocalization_pos, goal_floor=relocalization_floor , goal_house=relocalization_house , relocation=True, programStatus_old=programStatus_old)
        except Exception as e:
            rospy.loginfo(f"\n <executor-92> Error in PUBLISH GOAL: {e}\n")

    def finalize_relocalization_handler(self):
        self.instructionInfo.reset_relocalizationInfo()

    def move_handler(self, positions):
        for item in positions:
            robot_floor = self.robotState.get_state().get("floor")
            to_floor = item.get("floor")
            to_pos = item.get("dock")
            to_house = item.get("house")

            if robot_floor != to_floor:
                self.elevatorControl.update_elevatorStatus(elevatorStatus=0)
                self.programStatus.update_programStatus(programStatus="to_lift_outside")
                self.move_with_lift(taskId=None, robot_floor=robot_floor, to_pos=to_pos, to_floor=to_floor, to_house=to_house)
            else:
                self.programStatus.update_programStatus(programStatus="ready_move")
                self.move_with_lift(taskId=None, robot_floor=robot_floor, to_pos=to_pos, to_floor=to_floor, to_house=to_house)

    def finalize_move_handler(self):
        self.instructionInfo.reset_movePositions()

    def command_handler(self):
        command = self.instructionInfo.get_command()
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            self.programStatus.update_programStatus("execute_command_complete")

    def finalize_command_handler(self):
        self.instructionInfo.reset_command()

    def move_with_lift(self, taskId, robot_floor, to_pos, to_floor, to_house):
        """
        跟电梯交互
        参数:
            taskId: 正在执行的任务ID, 如果没有在执行任务则为0
            robot_floor: 机器人当前位于的楼层
            to_pos: 机器人要到达的目的地坐标
            to_floor: 机器人要到达的目的地楼层
            to_house: 机器人要到达的目的地建筑
        """
        programStatus = self.programStatus.get_programStatus()
        uuid_str = str(uuid.uuid4())

        rate = rospy.Rate(0.5) #控制两秒执行一次循环

        while programStatus != "moving":

            if programStatus == "to_lift_outside": #准备走向电梯门外的点位

                #初始化使用电梯需要的参数和流程接口
                self.elevatorControl.update_basicInfo(robotId=ROBOTID, taskId=taskId)
                self.elevatorControl.update_floorInfo(fromFloor=robot_floor, toFloor=to_floor)
                
                #向后台发初始化电梯流程请求 并更新 机器人执行任务需要的相关参数 
                self.set_elevatorFlow(flowId=uuid_str, elevatorStatus=self.elevatorStatus, taskId=taskId, fromFloor=robot_floor, toFloor=to_floor)

                elevatorControlParams = self.elevatorControl.get_elevatorControlParams()
                ele_out_pos = elevatorControlParams.get("fromElevatorOutAddress").get("pose").get("dock")
                ele_out_floor = elevatorControlParams.get("fromElevatorOutAddress").get("floor")
                ele_out_house = elevatorControlParams.get("fromElevatorOutAddress").get("house")

                #启动从后台获取电梯状态的进程
                if not self.elevatorGettter:
                    try:
                        self.elevatorGettter = elevatorFlowGetter.ElevatorFlowGetter(owner=self, flow_id=uuid_str, period=5)
                        self.elevatorGettter.start()
                    except Exception as e:
                        rospy.loginfo(f" <executor-224> start ElevatorFlowGetter failed: {e}")

                #向planning部分发目的坐标, 目标接收成功, 机器人改为状态 [moving_lift_outside]-[机器人正在赶往电梯口]
                try:
                    self.publish_goal(goal_pos=ele_in_pos, goal_floor=ele_out_floor, goal_house=ele_out_house, relocation=False, programStatus_old=programStatus)
                except Exception as e:
                    rospy.loginfo(f"\n <executor-230> Error in PUBLISH GOAL: {e}\n")

                programStatus = self.programStatus.get_programStatus()

                #目标接收成功 [机器人正在赶往电梯口](10), 更新电梯状态为[10], 通知后台
                if programStatus == "moving_lift_outside":
                    self.elevatorStatus = 10
                    self.set_elevatorFlow(flowId=uuid_str, elevatorStatus=self.elevatorStatus, taskId=taskId, fromFloor=robot_floor, toFloor=to_floor)

            if programStatus == "to_lift_inside": #到达电梯外部坐标, 准备走进电梯内部

                #到达电梯门口 且 收到 [电梯门打开](40) 的信号
                if self.elevatorStatus == 40:
                    #拍照
                    self.toBackend_photo()
                    
                    elevatorControl = self.elevatorControl.get_elevatorControlParams()
                    ele_in_pos = elevatorControl.get("fromElevatorInAddress").get("pose").get("dock")
                    ele_in_floor = elevatorControl.get("fromElevatorInAddress").get("floor")
                    ele_in_house = elevatorControl.get("fromElevatorInAddress").get("house")

                    #通知planning部分 机器人可以开始向电梯内部走, 待目标接收成功, 机器人状态改为 [delivering_lift_in]-[机器人正在赶往电梯内部]
                    try:
                        self.publish_goal(goal_pos=ele_in_pos, goal_floor=ele_in_floor, goal_house=ele_in_house, relocation=False, programStatus_old=programStatus)
                    except Exception as e:
                        rospy.loginfo(f"\n <executor-249> Error in PUBLISH GOAL: {e}\n")
                    
                    programStatus = self.programStatus.get_programStatus()
                    
                    #目标接收成功 [机器人正在赶往电梯内部](50), 更新电梯状态为[50], 通知后台
                    if programStatus == "moving_lift_inside":
                        self.elevatorStatus = 50
                        self.set_elevatorFlow(flowId=uuid_str, elevatorStatus=self.elevatorStatus, taskId=taskId, fromFloor=robot_floor, toFloor=to_floor)
                
                #到达电梯门口 还没收到 电梯门已开 的信号, 所以要发送 [已到达电梯口](20) 的命令
                elif self.elevatorStatus == 10:
                    self.elevatorStatus = 20
                    self.set_elevatorFlow(flowId=uuid_str, elevatorStatus=self.elevatorStatus, taskId=taskId, fromFloor=robot_floor, toFloor=to_floor)
                    #拍照
                    self.toBackend_photo()

                elif self.elevatorStatus == 20 or self.elevatorStatus == 30:
                    
                    elevatorControl = self.elevatorControl.get_elevatorControlParams()
                    ele_out_pos_new = elevatorControl.get("fromElevatorOutAddress").get("pose").get("dock")

                    if ele_out_pos != ele_out_pos_new:
                        ele_out_pos = ele_out_pos_new

                        if programStatus == "to_lift_inside":
                            self.programStatus.update_programStatus(programStatus="to_another_lift_outside")

                        try:
                            self.publish_goal(goal_pos=ele_out_pos_new, goal_floor=ele_out_floor, goal_house=ele_out_house, relocation=False, programStatus_old=programStatus)
                        except Exception as e:
                            rospy.loginfo(f"\n <executor-230> Error in PUBLISH GOAL: {e}\n")

            if programStatus == "at_lift_inside" and self.elevatorStatus == 50: #机器人在电梯内部并且刚才的状态是[正在赶往电梯]

                #通知后台机器人已到达电梯内部
                self.elevatorStatus = 60
                self.set_elevatorFlow(flowId=uuid_str, elevatorStatus=self.elevatorStatus, taskId=taskId, fromFloor=robot_floor, toFloor=to_floor)
                
                #更新机器人自身的状态为 等待重定位 [idle_relocation] 或者 [return_relocation]
                self.programStatus.update_programStatus("relocalization")

            if programStatus == "relocalization" and self.elevatorStatus == 80: #机器人处于可以发生重定位的状态并且电梯门已开

                #首先更新机器人现在所在的 [楼层] 和 [楼]
                self.robotState.update_position(floor=to_floor, house="ntuitive")
                robot_floor = self.robotState.get_state().get("floor")

                #拿到重定位的坐标
                elevatorControl = self.elevatorControl.get_elevatorControlParams()
                relocalization_pos = elevatorControl.get("toElevatorInAddress").get("pose").get("dock")
                relocalization_floor = elevatorControl.get("toElevatorInAddress").get("floor") 
                relocalization_house = elevatorControl.get("toElevatorInAddress").get("house")

                #拍照
                self.toBackend_photo()   

                #给planning部分发送重定位信息, 待目标接收成功, 机器人状态改为 [idle_inLift]/[return_inLift]-[机器人正在重置地图]
                try:
                    self.publish_goal(goal_pos=relocalization_pos, goal_floor=relocalization_floor, goal_house=relocalization_house, relocation=True, programStatus_old=programStatus)
                except Exception as e:
                    rospy.loginfo(f"\n <executor-294> Error in PUBLISH GOAL: {e}\n")

                programStatus = self.programStatus.get_programStatus()

                #目标接收成功 [机器人正在重置地图](90), 更新电梯状态为[90], 通知后台
                if programStatus == "relocalizing":
                    self.elevatorStatus = 90
                    self.set_elevatorFlow(flowId=uuid_str, elevatorStatus=self.elevatorStatus, taskId=taskId, fromFloor=robot_floor, toFloor=to_floor)
                     #拍照
                    self.toBackend_photo()

            #机器人重置地图成功
            if programStatus == "ready_move":
                
                #用了电梯系统的话, 需要向后台更新电梯状态 [机器人重置地图成功](100)
                if self.elevatorStatus == 90:
                    self.elevatorStatus = 100
                    self.set_elevatorFlow(flowId=uuid_str, elevatorStatus=self.elevatorStatus, taskId=taskId, fromFloor=robot_floor, toFloor=to_floor)

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
                    rospy.loginfo(f"\n <executor-324> Error in PUBLISH GOAL: {e}\n")

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


    def set_elevatorFlow(self, flowId, elevatorStatus, taskId, fromFloor, toFloor):
        """
        用来调用接口, 与后台协调电梯使用流程, 并更新相关电梯使用参数.
        参数:
            flowId: 流程ID, 每次使用电梯固定一个值
            elevatorStatus: 电梯使用状态
            taskId: 正在执行的任务ID
            fromFloor: 机器人出发楼层
            toFloor: 机器人需要到达的楼层
        """
        response = self.http_client.set_elevatorControlFlow(flowId=flowId, elevatorStatus=elevatorStatus, robotId=ROBOTID, taskId=taskId, fromFloor=fromFloor, toFloor=toFloor)
        
        try:
            flow_info = response.get("data").get("flowInfo")
            elevatorStatus = flow_info.get("status")

            fromElevatorOutAddress = flow_info.get("fromElevatorOutAddress")
            fromElevatorInAddress = flow_info.get("fromElevatorInAddress")
            toElevatorOutAddress = flow_info.get("toElevatorOutAddress")
            toElevatorInAddress = flow_info.get("toElevatorInAddress")

        except Exception as e:
            rospy.loginfo(f" <executor-455> fetch elevator info error: {e}")

        self.elevatorStatus = elevatorStatus

        self.elevatorControl.update_fromElevatorOutAddress(fromElevatorOutAddress=fromElevatorOutAddress)
        self.elevatorControl.update_fromElevatorInAddress(fromElevatorInAddress=fromElevatorInAddress)
        self.elevatorControl.update_toElevatorOutAddress(toElevatorOutAddress=toElevatorOutAddress)
        self.elevatorControl.update_toElevatorInAddress(toElevatorInAddress=toElevatorInAddress)





if __name__ == "__main__":

    #后台指定的参数
    ROBOTID = "18950214603"
    PRIVATE_KEY = "z/CszPJh61yWfA1eJhmDKg=="
    IV_VECTOR = "tBPz/vp+8x9ps4ikCj6btA=="

    #控制参数
    HEARTBEAT = 5 #控制MQTT 状态话题的周期性发送 & 跟后台发送请求的周期

    #连接参数
    BROKER_HOST = "10.25.0.2"
    BROKER_PORT = 1883
    HTTP_HEAD = "http"
    BACKEND_HOST = "10.25.0.15"   # "192.168.10.164"
    BACKEND_PORT = "18001"        # "8889"

    #ROS 发布话题名
    TOPIC_GOAL = "/goal_v3"

    #临界资源初始化
    robotState = dataInfo.RobotStateInfo()
    relocalizationInfo = dataInfo.RelocalizationInfo()

    #ros 初始化
    rospy.init_node("executor", anonymous=True)
    ros_sub = rosSub.RosSub(robotState=robotState)
    ros_pub_goal = rospy.Publisher(TOPIC_GOAL, Goal_v3, queue_size=1)
    time.sleep(0.1)

    #加密解密头部鉴权功能初始化
    httpEncryption = encryption.HttpEncryption(robotId=ROBOTID, private_key=PRIVATE_KEY, iv_vector=IV_VECTOR)

    #机器人客户端
    http_client = httpClient.HttpClient(head=HTTP_HEAD, host=BACKEND_HOST, port=BACKEND_PORT, httpEncryption=httpEncryption)

    #mqtt初始化与连接 -- 成功连接会更新机器人状态为idle
    robot_mqtt = mqttClient.MqttClient(host=BROKER_HOST, port=BROKER_PORT, robot_id=ROBOTID, robotState=robotState, relocalizationInfo=relocalizationInfo)
    robot_mqtt.connect()

    #线程启动
    stop_event = threading.Event()
    
    mqtt_thread = MqttThread(robot_mqtt=robot_mqtt, heartbeat=HEARTBEAT, stop_event=stop_event)
    mqtt_thread.start()
    interaction_thread = InteractionThread(robotState=robotState, relocalizationInfo=relocalizationInfo, http_client=http_client, ros_pub_goal=ros_pub_goal, stop_event=stop_event)
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