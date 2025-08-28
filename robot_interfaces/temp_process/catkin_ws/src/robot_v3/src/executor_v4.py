import time
import threading
import rospy
from robot_v3.msg import Goal_v3
from geometry_msgs.msg import PoseStamped
from tf.transformations import quaternion_from_euler
from std_msgs.msg import String
import uuid
import schedule

import mqttClient
import rosSub
import httpClient
import dataInfo
import httpServer
import encryption
import qrCode
import elevatorFlowGetter

from flask import Flask, jsonify
from werkzeug.serving import make_server
from threading import Thread


class StateThread(threading.Thread):
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

        next_time = time.monotonic()
        while not self.stop_event.is_set() and not rospy.is_shutdown():
            now = time.monotonic()
            if now >= next_time:
                try:
                    self.robot_mqtt.publish_state()
                except Exception as e:
                    rospy.logwarn(f" <executor - 54> MQTT error: {e}\n")
                next_time = now + self.heartbeat
            
            self.stop_event.wait(0.1)


class InteractionThread(threading.Thread):
    def __init__(self, state: dataInfo.StateInfo, statusBackend: dataInfo.StatusBackend, currentOrder: dataInfo.CurrentOrder, elevatorPlan: dataInfo.ElevatorPlan, elevatorControlParams: dataInfo.ElevatorControl, ros_pub_goal, robot_mqtt, http_client, stop_event: threading.Event):
        """
        这个类主要用来控制机器人的执行, 与后台交互, tianxin交互
        参数:
            state: 机器人自身的状态
            statusBackend: 后台分配任务的状态
            currentOrder: 机器人当前执行的任务的详细信息
            ros_pub_goal: ROS publisher for topic "Goal", 用于给tianxin发布目标地址和楼层
            robot_matt: 已初始化并且连接MQTT broker的客户端实例, 用于随时发布更新的状态消息
            http_client: HTTP 客户端实例, 用于调用后台任务相关的接口
            stop_event: 线程终止时间标志
        """
        super().__init__(daemon=True)

        self.state = state
        self.statusBackend = statusBackend
        self.currentOrder = currentOrder
        self.elevatorPlan = elevatorPlan
        self.elevatorControlParams = elevatorControlParams

        self.ros_pub_goal = ros_pub_goal

        self.robot_mqtt = robot_mqtt
        self.http_client = http_client
        
        self.stop_event = stop_event

        self.elevatorStatus = 0
        self.elevatorGettter = None

        self._sched = schedule.Scheduler()
        self._job = None

    def logic(self):
        """
        逻辑执行部分
        """
        if self.stop_event.is_set() and rospy.is_shutdown():
            return schedule.CancelJob

        try:
            # 得到现在后台分配任务的情况
            status = self.statusBackend.get_statusBackend().get("status")
            # 得到现在机器人的状态
            robot_state = self.state.get_state()
            taskStatus = robot_state.get("taskStatus")
            taskId = robot_state.get("taskId")

            # 机器人在 有 [待完成任务] 的时候 
            if taskStatus == "idle" and taskId != 0:

                try:
                    currentOrder_info = self.currentOrder.get_currentOrder()
                    goal_positions = currentOrder_info.get("goal_positions")
                except Exception as e:
                    print(f"\n <executor - 110> Error in READ GOAL: {e}\n")

                for item in goal_positions:
                    robot_floor = self.state.get_state().get("floor")
                    goal_floor = item.get("floor")
                    goal_pos = item.get("dock")
                    
                    if goal_floor != robot_floor:
                        self.state.update_taskStatus("idle_lift_out")
                        self.move(taskId=taskId, robot_floor=robot_floor, goal_pos=goal_pos, goal_floor=goal_floor)
                    else:
                        self.state.update_taskStatus("idle_toGo")
                        self.move(taskId=taskId, robot_floor=robot_floor, goal_pos=goal_pos, goal_floor=goal_floor)

            # 机器人 [arrived]
            if taskStatus == "arrived":
                self.notify_backend(taskId=taskId, taskStatus=dataInfo.TaskStatus.PENDING_RECEIPT.value, elevatorCommand=None)
                
                code = self.currentOrder.get_currentOrder().get("code")
                #qr_check = self.qr_check(code)
                print(" Start checking QR code")
                time.sleep(5)
                #if qr_check:
                if True:
                    #self.door_open()
                    self.notify_backend(taskId=taskId, taskStatus=dataInfo.TaskStatus.DELIVERY_COMPLETE.value , elevatorCommand=None)
                else:
                    self.notify_backend(taskId=taskId, taskStatus=dataInfo.TaskStatus.DELIVERY_FAILED.value , elevatorCommand=None)
                
            # 机器人在 [delivered]/ [delivered_failed]/ [cancel_delivery]/ [restock] 返回原点
            if taskStatus == "delivered" or taskStatus== "delivered_failed" or taskStatus == "cancel_delivery" or taskStatus == "restock":
                currentOrder_info = self.currentOrder.get_currentOrder()
                return_positions = currentOrder_info.get("return_positions")
                
                for item in return_positions:
                    robot_floor = self.state.get_state().get("floor")
                    return_floor = item.get("floor")
                    return_pos = item.get("dock")

                    if return_floor != robot_floor:
                        self.state.update_taskStatus("return_lift_out")
                        self.back(taskId=taskId, robot_floor=robot_floor, return_pos=return_pos, return_floor=return_floor)
                    else:
                        self.state.update_taskStatus("return_toGo")
                        self.back(taskId=taskId, robot_floor=robot_floor, return_pos=return_pos, return_floor=return_floor)
            
            # 机器人执行完整个任务之后清空之前任务的所有数据
            if taskStatus == "idle" and taskId == 0:
                self.finalize_task()
        
        except Exception as e:
            print(f"\n <executor-167> Error happens in the main execution loop as {e}\n")

    def run(self):
        self._job = self._sched.every(2).seconds.do(self.logic)

        while not self.stop_event.is_set() and not rospy.is_shutdown():
            self._sched.run_pending()
            self.stop_event.wait(0.1)

        # 清理
        if self._job:
            try:
                self._sched.cancel_job(self._job)
            except Exception:
                pass
            self._job = None


    def move(self, taskId, robot_floor, goal_pos, goal_floor):
        """
        跟电梯交互的流程
        """
        robot_state = self.state.get_state()
        taskStatus = robot_state.get("taskStatus")

        uuid_str = str(uuid.uuid4())

        rate = rospy.Rate(0.5)
    
        while taskStatus != "arrived":

            if taskStatus == "idle_lift_out":

                self.elevatorControlParams.update_basicInfo(robotId=ROBOTID, taskId=taskId)
                self.elevatorControlParams.update_floorInfo(fromFloor=robot_floor, toFloor=goal_floor)
                self.set_elevatorFlow(flowId=uuid_str, elevatorStatus=0, taskId=taskId, fromFloor=robot_floor, toFloor=goal_floor)

                elevatorControl = self.elevatorControlParams.get_elevatorControl()
                goal_lift_out = elevatorControl.get("fromElevatorOutAddress").get("pose").get("dock")
                goal_lift_floor = elevatorControl.get("fromElevatorOutAddress").get("floor")

                if not self.elevatorGettter:
                    try:
                        self.elevatorGettter = elevatorFlowGetter.ElevatorFlowGetter(owner=self, flow_id=uuid_str, period=5)
                        self.elevatorGettter.start()
                    except Exception as e:
                        rospy.loginfo(f"[move] start ElevatorFlowWatcher failed: {e}")

                try:
                    self.elevatorStatus = 10
                    self.set_elevatorFlow(flowId=uuid_str, elevatorStatus=self.elevatorStatus, taskId=taskId, fromFloor=robot_floor, toFloor=goal_floor)
                    self.publish_goal(goal_pos=goal_lift_out, goal_floor=goal_lift_floor, relocation=False, taskStatus_old=taskStatus)
                except Exception as e:
                    rospy.loginfo(f"\n <executor - 136> Error in PUBLISH GOAL: {e}\n")
                    
            if taskStatus == "idle_lift_in":

                elevatorControl = self.elevatorControlParams.get_elevatorControl()
                goal_lift_in = elevatorControl.get("fromElevatorInAddress").get("pose").get("dock")
                goal_lift_floor = elevatorControl.get("fromElevatorInAddress").get("floor")

                if self.elevatorStatus == 40:
                    try:
                        self.elevatorStatus = 50
                        self.set_elevatorFlow(flowId=uuid_str, elevatorStatus=self.elevatorStatus, taskId=taskId, fromFloor=robot_floor, toFloor=goal_floor)
                        self.publish_goal(goal_pos=goal_lift_in, goal_floor=goal_lift_floor, relocation=False, taskStatus_old=taskStatus)
                    except Exception as e:
                        rospy.loginfo(f"\n <executor - 147> Error in PUBLISH GOAL: {e}\n")
                elif self.elevatorStatus == 10:
                    self.elevatorStatus = 20
                    self.set_elevatorFlow(flowId=uuid_str, elevatorStatus=self.elevatorStatus, taskId=taskId, fromFloor=robot_floor, toFloor=goal_floor)
                

            if taskStatus == "idle_inside_lift" and self.elevatorStatus == 50:
                
                self.elevatorStatus = 60
                self.set_elevatorFlow(flowId=uuid_str, elevatorStatus=self.elevatorStatus, taskId=taskId, fromFloor=robot_floor, toFloor=goal_floor)
                self.state.update_taskStatus("idle_relocation")
                
            if taskStatus == "idle_relocation" and self.elevatorStatus == 80:

                self.state.update_position(floor=goal_floor, building="ntuitive")

                elevatorControl = self.elevatorControlParams.get_elevatorControl()
                goal_relocation = elevatorControl.get("toElevatorInAddress").get("pose").get("dock")
                goal_floor = elevatorControl.get("toElevatorInAddress").get("floor")

                try:
                    self.elevatorStatus = 90
                    self.set_elevatorFlow(flowId=uuid_str, elevatorStatus=self.elevatorStatus, taskId=taskId, fromFloor=robot_floor, toFloor=goal_floor)
                    self.publish_goal(goal_pos=goal_relocation, goal_floor=goal_floor, relocation=True, taskStatus_old=taskStatus)
                except Exception as e:
                    rospy.loginfo(f"\n <executor - 161> Error in PUBLISH GOAL: {e}\n")

            if taskStatus == "idle_toGo":

                if self.elevatorGettter:
                    try:
                        self.elevatorGettter.stop()
                    except Exception:
                        pass
                    finally:
                        self.elevatorGettter = None
                
                if self.elevatorStatus == 90:
                    self.elevatorStatus = 100
                    self.set_elevatorFlow(flowId=uuid_str, elevatorStatus=self.elevatorStatus, taskId=taskId, fromFloor=robot_floor, toFloor=goal_floor)

                try:
                    self.publish_goal(goal_pos=goal_pos, goal_floor=goal_floor, relocation=False, taskStatus_old=taskStatus)
                except Exception as e:
                    rospy.loginfo(f"\n <executor - 167> Error in PUBLISH GOAL: {e}\n")

            robot_state = self.state.get_state()
            taskStatus = robot_state.get("taskStatus")

            rate.sleep()

        if self.elevatorGettter:
            try:
                self.elevatorGettter.stop()
            except Exception:
                pass
            finally:
                self.elevatorGettter = None

    def back(self, taskId, robot_floor, return_pos, return_floor):
        """
        跟电梯交互的流程
        """
        robot_state = self.state.get_state()
        taskStatus = robot_state.get("taskStatus")

        uuid_str = str(uuid.uuid4())

        rate = rospy.Rate(0.5)
    
        while taskStatus != "idle":

            print(f"\n {self.elevatorStatus} \n")

            if taskStatus == "return_lift_out":

                self.elevatorControlParams.update_basicInfo(robotId=ROBOTID, taskId=taskId)
                self.elevatorControlParams.update_floorInfo(fromFloor=robot_floor, toFloor=return_floor)
                self.set_elevatorFlow(flowId=uuid_str, elevatorStatus=0, taskId=taskId, fromFloor=robot_floor, toFloor=return_floor)

                elevatorControl = self.elevatorControlParams.get_elevatorControl()
                return_lift_out = elevatorControl.get("fromElevatorOutAddress").get("pose").get("dock")
                return_lift_floor = elevatorControl.get("fromElevatorOutAddress").get("floor")

                if not self.elevatorGettter:
                    try:
                        self.elevatorGettter = elevatorFlowGetter.ElevatorFlowGetter(owner=self, flow_id=uuid_str, period=5)
                        self.elevatorGettter.start()
                    except Exception as e:
                        rospy.loginfo(f"[move] start ElevatorFlowWatcher failed: {e}")

                try:
                    self.elevatorStatus = 10
                    self.set_elevatorFlow(flowId=uuid_str, elevatorStatus=self.elevatorStatus, taskId=taskId, fromFloor=robot_floor, toFloor=return_floor)
                    self.publish_goal(goal_pos=return_lift_out, goal_floor=return_lift_floor, relocation=False, taskStatus_old=taskStatus)
                except Exception as e:
                    rospy.loginfo(f"\n <executor - 136> Error in PUBLISH GOAL: {e}\n")
                    
            if taskStatus == "return_lift_in":

                elevatorControl = self.elevatorControlParams.get_elevatorControl()
                return_lift_in = elevatorControl.get("fromElevatorInAddress").get("pose").get("dock")
                return_lift_floor = elevatorControl.get("fromElevatorInAddress").get("floor")

                if self.elevatorStatus == 40:
                    try:
                        self.elevatorStatus = 50
                        self.set_elevatorFlow(flowId=uuid_str, elevatorStatus=self.elevatorStatus, taskId=taskId, fromFloor=robot_floor, toFloor=return_floor)
                        self.publish_goal(goal_pos=return_lift_in, goal_floor=return_lift_floor, relocation=False, taskStatus_old=taskStatus)
                    except Exception as e:
                        rospy.loginfo(f"\n <executor - 147> Error in PUBLISH GOAL: {e}\n")

                elif self.elevatorStatus == 10:
                    self.elevatorStatus = 20
                    self.set_elevatorFlow(flowId=uuid_str, elevatorStatus=self.elevatorStatus, taskId=taskId, fromFloor=robot_floor, toFloor=return_floor)

            if taskStatus == "return_inside_lift" and self.elevatorStatus == 50:
                self.elevatorStatus = 60
                self.set_elevatorFlow(flowId=uuid_str, elevatorStatus=self.elevatorStatus, taskId=taskId, fromFloor=robot_floor, toFloor=return_floor)
                self.state.update_taskStatus("return_relocation")
                
            if taskStatus == "return_relocation" and self.elevatorStatus == 80:

                
                self.state.update_position(floor=return_floor, building="ntuitive")

                elevatorControl = self.elevatorControlParams.get_elevatorControl()
                return_relocation = elevatorControl.get("toElevatorInAddress").get("pose").get("dock")
                return_floor = elevatorControl.get("toElevatorInAddress").get("floor")

                try:
                    self.elevatorStatus = 90
                    self.set_elevatorFlow(flowId=uuid_str, elevatorStatus=self.elevatorStatus, taskId=taskId, fromFloor=robot_floor, toFloor=return_floor)
                    self.publish_goal(goal_pos=return_relocation, goal_floor=return_floor, relocation=True, taskStatus_old=taskStatus)
                except Exception as e:
                    rospy.loginfo(f"\n <executor - 161> Error in PUBLISH GOAL: {e}\n")

            if taskStatus == "return_toGo":

                if self.elevatorGettter:
                    try:
                        self.elevatorGettter.stop()
                    except Exception:
                        pass
                    finally:
                        self.elevatorGettter = None
                
                if self.elevatorStatus == 90:
                    self.elevatorStatus = 100
                    self.set_elevatorFlow(flowId=uuid_str, elevatorStatus=self.elevatorStatus, taskId=taskId, fromFloor=robot_floor, toFloor=return_floor)

                try:
                    self.publish_goal(goal_pos=return_pos, goal_floor=return_floor, relocation=False, taskStatus_old=taskStatus)
                except Exception as e:
                    rospy.loginfo(f"\n <executor - 167> Error in PUBLISH GOAL: {e}\n")

            robot_state = self.state.get_state()
            taskStatus = robot_state.get("taskStatus")

            rate.sleep()

        if self.elevatorGettter:
            try:
                self.elevatorGettter.stop()
            except Exception:
                pass
            finally:
                self.elevatorGettter = None

    def set_elevatorFlow(self, flowId, elevatorStatus, taskId, fromFloor, toFloor):

        response = self.http_client.set_elevatorControlFlow(flowId=flowId, elevatorStatus=elevatorStatus, robotId=ROBOTID, taskId=taskId, fromFloor=fromFloor, toFloor=toFloor)
        
        flow_info = response.get("data").get("flowInfo")
        elevatorStatus = flow_info.get("status")

        self.elevatorStatus = elevatorStatus

        fromElevatorOutAddress = flow_info.get("fromElevatorOutAddress")
        fromElevatorInAddress = flow_info.get("fromElevatorInAddress")
        toElevatorOutAddress = flow_info.get("toElevatorOutAddress")
        toElevatorInAddress = flow_info.get("toElevatorInAddress")

        self.elevatorControlParams.update_fromElevatorOutAddress(fromElevatorOutAddress=fromElevatorOutAddress)
        self.elevatorControlParams.update_fromElevatorInAddress(fromElevatorInAddress=fromElevatorInAddress)
        self.elevatorControlParams.update_toElevatorOutAddress(toElevatorOutAddress=toElevatorOutAddress)
        self.elevatorControlParams.update_toElevatorInAddress(toElevatorInAddress=toElevatorInAddress)


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

    def publish_goal(self, goal_pos, goal_floor, relocation, taskStatus_old):
        """
        给tianxin发布他规划路径需要的数据
        参数:
            outside_lift: 电梯外面的坐标
            inside_lift: 电梯内部的坐标
            final_position: 最后机器人需要到达的坐标
            final_floor: 最后机器人需要到达的楼层
        """

        goal = Goal_v3()
        #ps_list = []
        #for item in [outside_lift, inside_lift, final_position]:
            #ps_list.append(self.position_transform(item))
        #goal.pose = ps_list

        goal.pose = self.position_transform(goal_pos)
        goal.floor = goal_floor
        goal.relocation = relocation
        self.ros_pub_goal.publish(goal)
        rospy.loginfo(f"\n Forwarded the goal info to the planning part \n {goal}\n")
        self.publish_goal_wait(taskStatus_old=taskStatus_old)
        
        

    def publish_goal_wait(self, taskStatus_old):
        rate = rospy.Rate(10) #控制每0.1秒检查一次状态
        waited = 0
        while waited < 5.0:
                            
            if self.stop_event.is_set() or rospy.is_shutdown():
                break
                            
            robot_state = self.state.get_state()
            taskStatus_new = robot_state.get("taskStatus")
            if taskStatus_new != taskStatus_old:
                break

            rate.sleep()
            waited += 0.1
    
    def qr_check(self, code):
        """
        核对二维码, 计时核对, 超时还没有核对成功的话就算失败
        return:
            True: 核对成功
            False: 核对失败
        """
        #用两分钟的时间去核对二维码
        qr_scanner = qrCode.QrCode(timeout=60)
        try:
            return qr_scanner.scan(code)
        finally:
            qr_scanner.close()

    
    def door_open(self):
        """
        控制货仓门打开或关闭, 然后判断是否取货成功, 需要拍照估计
        """

    def notify_backend(self, taskId, taskStatus, elevatorCommand):
        """
        这个函数的作用是:
            1. 调用<接口2>, 通知后台机器人的状态
        """
        try:
            response = self.http_client.update_taskStatus(taskId=taskId, taskStatus=taskStatus, elevatorControlCommand=elevatorCommand)
            rospy.loginfo(f"\n notify backend with taskId:{taskId}, taskStatus:{taskStatus}, elevatorCommand:{elevatorCommand}\n")
            rospy.loginfo(f"\n notify backend and get: {response} \n")
        except Exception as e:
            rospy.loginfo(f"\n <executor - 303> error happens: {e}\n")
        
        if taskStatus:
            #配送成功
            if taskStatus == dataInfo.TaskStatus.DELIVERY_COMPLETE.value:
                self.state.update_taskStatus("delivered")
                self.robot_mqtt.publish_state()
                self.state.update_taskId(0)
            #配送失败
            elif taskStatus == dataInfo.TaskStatus.DELIVERY_FAILED.value:
                self.state.update_taskStatus("delivered_failed")
                self.robot_mqtt.publish_state()
                self.state.update_taskId(0)


    def finalize_task(self):
        """
        这个函数的作用就是在正常情况下, 小车完成任务后, 返回原始位置后, 清空数据记录
        """
        self.currentOrder.reset_currentOrder()
        self.state.update_taskId(0)
        self.statusBackend.update_statusBackend(0, 0)
        self.elevatorStatus = 0
        self.elevatorControlParams.reset_elevatorControlParams()


class FetchTaskThread(threading.Thread):
    def __init__(self, http_client, state: dataInfo.StateInfo, statusBackend: dataInfo.StatusBackend, currentOrder: dataInfo.CurrentOrder, period, elevatorPlan: dataInfo.ElevatorPlan , stop_event: threading.Event):
        """
        这个线程用于执行周期性地从后台拉取任务信息, 为了避免因为网络问题没有得到最新的任务状态
        参数:
            http_client: 用来调用机器人客户端接口
            state: 机器人自身的状态
            statusBackend: 后台分配任务的状态
            currentOrder: 机器人当前执行的任务的详细信息
            period:
            elevatorPlan: 
            stop_event: 线程终止时间标志
        """
        super().__init__(daemon=True)
        self.http_client = http_client
        self.state = state
        self.statusBackend = statusBackend
        self.currentOrder = currentOrder
        self.period = period
        self.elevatorPlan = elevatorPlan
        self.stop_event = stop_event

        self.level = {"1": 1, "2m": 2, "3": 3, "4": 4, "5": 5}

    def run(self):
        next_fetch = time.monotonic()

        while not self.stop_event.is_set() and not rospy.is_shutdown():

            now = time.monotonic()  
            if now >= next_fetch:

                status_old = self.statusBackend.get_statusBackend().get("status")
                
                robot_state = self.state.get_state()
                robot_taskId_old = robot_state.get("taskId")
                robot_floor = robot_state.get("floor")
                robot_building = robot_state.get("building")
                
                response = self.http_client.select_taskInfo(taskId=robot_taskId_old, floor=robot_floor, building=robot_building)
                response_code = response.get("code")

                if response_code == 0:
                    data = response.get("data")
                    taskInfo = data.get("taskInfo") or {}

                    if taskInfo != {}:

                        taskId_new = data.get("taskInfo").get("id")
                        status_new = data.get("taskInfo").get("status")
                        robotStatus = self.state.get_state().get("taskStatus")

                        # 如果是不同任务id(也就是机器人执行完了某个任务, 或者根本没执行任何任务)
                        # 收到了来自后台的 response -- 30 or 40 则更新机器人状态, 添加任务信息, 更新后台状态记录
                        if status_old != status_new and robot_taskId_old != taskId_new:
                            #get 相关值
                            code = data.get("code")
                            #配送任务的 Id 和 QR code
                            self.currentOrder.update_deliveryDetails(taskId=taskId_new, code=code)

                            #配送目的地相信信息的 获取&存储&更新
                            goal_addrList = taskInfo.get("addressList")
                            self.store_goalPositions(goal=True, addrList=goal_addrList)

                            #配送完成返回地址信息的 获取&存储&更新
                            return_addrList = data.get("addressList")
                            self.store_goalPositions(goal=False, addrList=return_addrList)

                            #更新后台状态记录
                            self.statusBackend.update_statusBackend(taskId=taskId_new, status=status_new)
                            #然后更新机器人状态 -- 主要是任务id
                            if status_new == 90:
                                self.state.update_taskStatus("restock")
                            elif status_new == 30 or status_new == 40:
                                self.state.update_taskStatus("idle")
                            self.state.update_taskId(taskId_new)
                            
                        # 如果同一个任务id情况下(机器人正在执行某一任务), 收到来自后台的response, 除了60 其他都不用管
                        if status_old != status_new and robot_taskId_old == taskId_new:
                            self.statusBackend.update_statusBackend(taskId=taskId_new, status=status_new)
                            # 是 60 取消任务的话
                            if status_new == 60 and (robotStatus == "delivering" or robotStatus == "arrived"):
                                self.state.update_taskId(0)
                                self.state.update_taskStatus("cancel_delivery")
                    else:
                        #配送完成返回地址信息的 获取&存储&更新
                        return_addrList = data.get("addressList")
                        self.store_goalPositions(goal=False, addrList=return_addrList)
                        
                else:
                    rospy.loginfo(f"Backend response with: {response_code}")

                next_fetch = now + self.period
            
            self.stop_event.wait(0.1)

    def store_goalPositions(self, goal, addrList):
        """
        存储更新订单目的地址以及机器人返回原点的地址详情
        参数:
            goal: bool, 代表当前更新的事配送目的地址(True) 还是 返回原点地址(False).
            addrList: 目标地址的详细信息
        """
        for item in addrList:
            desc = item.get("identity").get("desc")
            dock = item.get("pose").get("dock")
            floor = item.get("floor")
            house = item.get("house")

            pos_dict = {
                "room": desc,
                "dock": dock,
                "floor": floor,
                "house": house
            }

            if goal:
                self.currentOrder.update_goalPositions(goal_pos_dict=pos_dict)
            else:
                self.currentOrder.update_returnPositions(return_pos_dict=pos_dict)
        
    def store_elevatorCommand(self, goal):
        """
        用于更新机器人和电梯交互的指令
        参数:
            goal: True or False, True 代表要更新送货需要的指令, False 代表要更新返回需要的指令
        """
        BUILDING = ""
        ROBOT_FLOOR = ""
        ELEVATOR_NAME_OUT = ""
        ELEVATOR_NAME_IN = ""
        MOVE = ""
        TO = ""

        robot_info = self.state.get_state()

        if goal:
            info = self.currentOrder.get_currentOrder().get("goal_positions")
            TO = info.get("goal_floor")
        else:
            info = self.currentOrder.get_currentOrder().get("return_positions")
            TO = info.get("return_floor")

        ROBOT_FLOOR = robot_info.get("floor")
        ROBOT_FLOOR_int = self.level.get(ROBOT_FLOOR)

        TO_int = self.level.get(TO)

        if ROBOT_FLOOR_int > TO_int:
            MOVE = "d"
        else:
            MOVE = "u"

        ELEVATOR_NAME_OUT = info.get("out_lift_name")
        ELEVATOR_NAME_IN = info.get("in_lift_name")
        BUILDING = info.get("house")

        command_1 = f"{BUILDING}:{ROBOT_FLOOR}:{ELEVATOR_NAME_OUT}:{MOVE}"
        command_2 = f"{BUILDING}:{ROBOT_FLOOR}:{ELEVATOR_NAME_IN}:{TO}"

        if goal:
            self.elevatorPlan.update_deliveringCommand(command_1=command_1, command_2=command_2)
        else:
            self.elevatorPlan.update_returningCommand(command_1=command_1, command_2=command_2)


def create_flask_app(server: httpServer.HttpServer):
    """
    创建一个app
    """
    return server.create_app()

def start_flask_in_thread(flask_app, host, port):
    class ServerThread(Thread):
        def __init__(self):
            super().__init__(daemon=True) #可以试试改为False
            self.srv = make_server(host, port, flask_app)
            self.ctx = flask_app.app_context()
            self.ctx.push()

        def run(self):
            self.srv.serve_forever()

        def shutdown(self):
            self.srv.shutdown()

    thr = ServerThread()
    thr.start()
    return thr


if __name__ == "__main__":
    
    #后台指定的参数
    ROBOTID = "18950214603"
    PRIVATE_KEY = "z/CszPJh61yWfA1eJhmDKg=="
    IV_VECTOR = "tBPz/vp+8x9ps4ikCj6btA=="

    #控制参数
    HEARTBEAT = 5 #控制MQTT 状态话题的周期性发送 & 跟后台发送请求的周期
    TIMEOUT = 120 #限制扫描二维码的时间

    #连接参数
    BROKER_HOST = "10.25.0.2"
    BROKER_PORT = 1883
    HTTP_HEAD = "http"
    BACKEND_HOST = "10.25.0.15"   # "192.168.10.164"
    BACKEND_PORT = "18001"        # "8889"

    #ROS 发布话题名
    TOPIC_GOAL = "/goal_v3"

    #临界资源初始化
    state = dataInfo.StateInfo()
    statusBackend = dataInfo.StatusBackend()
    currentOrder = dataInfo.CurrentOrder()
    elevatorPlan = dataInfo.ElevatorPlan()
    elevatorControlParams = dataInfo.ElevatorControl()

    #加密解密头部鉴权功能初始化
    httpEncryption = encryption.HttpEncryption(robotId=ROBOTID, private_key=PRIVATE_KEY, iv_vector=IV_VECTOR)

    #ros初始化 以及相关的 ros publisher 初始化
    rospy.init_node("robot_comNode", anonymous=False)
    ros_sub = rosSub.RosSub(state)
    ros_pub_goal = rospy.Publisher(TOPIC_GOAL, Goal_v3, queue_size=1)

    #mqtt初始化与连接 -- 成功连接会更新机器人状态为idle
    robot_mqtt = mqttClient.MqttClient(host=BROKER_HOST, port=BROKER_PORT, robot_id=ROBOTID, state=state)
    robot_mqtt.connect()

    #机器人客户端
    http_client = httpClient.HttpClient(head=HTTP_HEAD, host=BACKEND_HOST, port=BACKEND_PORT, httpEncryption=httpEncryption)

    #机器人服务器端
    http_server = httpServer.HttpServer(state=state, statusBackend=statusBackend, currentOrder=currentOrder, elevatorPlan=elevatorPlan)
    flask_app = create_flask_app(http_server)

    #线程启动
    stop_event = threading.Event()
    #MQTT 话题发布线程
    state_thread = StateThread(robot_mqtt, HEARTBEAT, stop_event)
    state_thread.start()
    #http client 线程
    interaction_thread = InteractionThread(state=state, statusBackend=statusBackend, currentOrder=currentOrder, elevatorPlan=elevatorPlan , elevatorControlParams=elevatorControlParams, ros_pub_goal=ros_pub_goal, robot_mqtt=robot_mqtt, http_client=http_client, stop_event=stop_event)
    interaction_thread.start()
    #fetch task info 线程
    fetchTask_thread = FetchTaskThread(http_client=http_client, state=state, statusBackend=statusBackend, currentOrder=currentOrder, period=HEARTBEAT, elevatorPlan=elevatorPlan, stop_event=stop_event)
    fetchTask_thread.start()
    #http server 线程
    flask_thread = start_flask_in_thread(flask_app, "0.0.0.0", 8000)

    rospy.loginfo("Threads start working successfully.")

    try:
        rospy.spin()
    finally:
        #回收线程
        stop_event.set()
        state_thread.join(timeout=1)
        interaction_thread.join(timeout=1)
        fetchTask_thread.join(timeout=1)
        flask_thread.shutdown()
        flask_thread.join(timeout=1)

        #正常退出发布离线消息
        robot_mqtt.publish_connection(status="offline", reason="shutdown")
        robot_mqtt.stop()
        