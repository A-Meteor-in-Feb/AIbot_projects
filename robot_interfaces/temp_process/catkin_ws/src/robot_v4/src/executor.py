import time
import threading
import rospy
from robot_v3.msg import Goal_v3
from geometry_msgs.msg import PoseStamped
from tf.transformations import quaternion_from_euler
from std_msgs.msg import String

import mqttClient
import rosSub
import httpClient
import dataInfo
import httpServer
import encryption
import qrCode

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
    def __init__(self, state: dataInfo.StateInfo, statusBackend: dataInfo.StatusBackend, currentOrder: dataInfo.CurrentOrder, elevatorPlan: dataInfo.ElevatorPlan, ros_pub_goal, robot_mqtt, http_client, stop_event: threading.Event):
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

        self.ros_pub_goal = ros_pub_goal

        self.robot_mqtt = robot_mqtt
        self.http_client = http_client
        
        self.stop_event = stop_event

    def run(self):
        """
        逻辑执行部分
        """
        while not self.stop_event.is_set() and not rospy.is_shutdown():

            try:
                # 得到现在后台分配任务的情况
                status = self.statusBackend.get_statusBackend().get("status")
                # 得到现在机器人的状态
                robot_state = self.state.get_state()
                taskStatus = robot_state.get("taskStatus")
                taskId = robot_state.get("taskId")
                step = robot_state.get("step")
                #fault = robot_state.get("fault")


                # 机器人在 [idle] 或者 [returning] 的时候 and 有 [待完成任务 (30\40)&(taskId)] 
                if (taskStatus == "idle" or taskStatus == "returning") and (status == 30 or status == 40) and taskId != 0:    
                    try:
                        currentOrder_info = self.currentOrder.get_currentOrder()
                        goal_positions = currentOrder_info.get("goal_positions")
                    except Exception as e:
                        rospy.loginfo(f"\n <executor - 110> Error in READ GOAL: {e}\n")

                    outside_lift = goal_positions.get("outside_lift")
                    inside_lift = goal_positions.get("inside_lift")
                    goal_position = goal_positions.get("goal_position")
                    goal_floor = goal_positions.get("goal_floor")

                    try:
                        self.publish_goal(outside_lift=outside_lift, inside_lift=inside_lift, final_position=goal_position, final_floor=goal_floor)
                        self.publish_goal_wait(taskStatus_old=taskStatus)
                    except Exception as e:
                        rospy.loginfo(f"\n <executor - 121> Error in PUBLISH GOAL: {e}\n")

                if taskStatus == "delivering":
                    elevatorCommand = self.elevatorPlan.get_elevatorPlan().get("delivering")
                    if step == 1:
                        self.state.update_step(0)
                        command_1 = elevatorCommand.get(1)
                        self.notify_backend(taskId=taskId, taskStatus=None, elevatorCommand=command_1)
                    elif step == 2:
                        self.state.update_step(0)
                        command_2 = elevatorCommand.get(2)
                        self.notify_backend(taskId=taskId, taskStatus=None, elevatorCommand=command_2)
                    else:
                        continue

                # 机器人 [arrived]
                if taskStatus == "arrived":
                    self.notify_backend(taskId=taskId, taskStatus=dataInfo.TaskStatus.PENDING_RECEIPT.value, elevatorCommand=None)
                    
                    code = self.currentOrder.get_currentOrder().get("code")
                    qr_check = self.qr_check(code)
                    
                    if qr_check:
                        #self.door_open()
                        self.notify_backend(taskId=taskId, taskStatus=dataInfo.TaskStatus.DELIVERY_COMPLETE.value , elevatorCommand=None)
                    else:
                        self.notify_backend(taskId=taskId, taskStatus=dataInfo.TaskStatus.DELIVERY_FAILED.value , elevatorCommand=None)
                    
                # 机器人在 [delivered] 或者 [delivered_failed] 且 [没有待完成任务] -- 在notify后台取货成功/失败之后 任务就被清空了
                if (taskStatus == "delivered" or taskStatus== "delivered_failed") and (status != 30 or status != 40) and taskId == 0:
                    
                    try:
                        currentOrder_info = self.currentOrder.get_currentOrder()
                        return_positions = currentOrder_info.get("return_positions")
                    except Exception as e:
                        rospy.loginfo(f"\n <executor - 156> Error happens when try to read return details: {e}\n")

                    outside_lift = return_positions.get("outside_lift")
                    inside_lift = return_positions.get("inside_lift")
                    return_position = return_positions.get("return_position")
                    return_floor = return_positions.get("return_floor")
                    
                    try:
                        self.publish_goal(outside_lift=outside_lift, inside_lift=inside_lift, final_position=return_position, final_floor=return_floor)
                        self.publish_goal_wait(taskStatus_old=taskStatus)
                    except Exception as e:
                        rospy.loginfo(f"\n <executor - 167> Error happens when PUBLISH GOAL: {e}\n")

                #取消某个任务 且 没有分配新任务 则 给tianxin发送要返回某个地方的goal
                if taskStatus == "cancel_delivery" and (status != 30 or status != 40) and taskId == 0:
                    
                    try:
                        currentOrder_info = self.currentOrder.get_currentOrder()
                        return_positions = currentOrder_info.get("return_positions")
                    except Exception as e:
                        rospy.loginfo(f"\n <executor - 176> Error happens when try to read return details: {e}\n")

                    outside_lift = return_positions.get("outside_lift")
                    inside_lift = return_positions.get("inside_lift")
                    return_position = return_positions.get("return_position")
                    return_floor = return_positions.get("return_floor")
                    
                    try:
                        self.publish_goal(outside_lift=outside_lift, inside_lift=inside_lift, final_position=return_position, final_floor=return_floor)
                        self.publish_goal_wait(taskStatus_old=taskStatus)
                    except Exception as e:
                        rospy.loginfo(f"\n <executor - 187> Error happens when PUBLISH GOAL: {e}\n")

                #机器人在任何情况下返回 ([配送完毕] 或者 [任务取消]), 清空数据记录
                if taskStatus == "returning":
                    self.finalize_task()
                    elevatorCommand = self.elevatorPlan.get_elevatorPlan().get("returning")
                    if step == 1:
                        self.state.update_step(0)
                        command_1 = elevatorCommand.get(1)
                        self.notify_backend(taskId=taskId, taskStatus=None, elevatorCommand=command_1)
                    elif step == 2:
                        self.state.update_step(0)
                        command_1 = elevatorCommand.get(2)
                        self.notify_backend(taskId=taskId, taskStatus=None, elevatorCommand=command_2)
                    else:
                        continue
                
                if taskStatus == "idle" and taskId == 0:
                    empty_pos = {"x": 0, "y": 0, "theta": 0}
                    self.currentOrder.update_returnPositions(outside_lift=empty_pos, inside_lift=empty_pos, return_position=empty_pos, out_lift_name="", in_lift_name="", return_floor="", return_room="", house="")
        
                    
            except Exception as e:
                rospy.loginfo(f"\n <executor-210> Error happens in the main execution loop as {e}\n")

            self.stop_event.wait(0.1)

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

    def publish_goal(self, outside_lift, inside_lift, final_position, final_floor):
        """
        给tianxin发布他规划路径需要的数据
        参数:
            outside_lift: 电梯外面的坐标
            inside_lift: 电梯内部的坐标
            final_position: 最后机器人需要到达的坐标
            final_floor: 最后机器人需要到达的楼层
        """

        goal = Goal_v3()
        ps_list = []
        for item in [outside_lift, inside_lift, final_position]:
            ps_list.append(self.position_transform(item))
        goal.pose = ps_list
        goal.floor = final_floor

        self.ros_pub_goal.publish(goal)
        rospy.loginfo(f"\n Forwarded the goal info to the planning part \n {goal}\n")

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
            rospy.loginfo(f"\n notify backend and get: {response.get("code")} \n")
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
        这个函数的作用就是在正常情况下, 小车完成任务后, 开始返回原始位置后, 清空数据记录
        """
        empty_pos = {"x": 0, "y": 0, "theta": 0}
        self.currentOrder.update_deliveryDetails(taskId=0, code="")
        self.currentOrder.update_goalPositions(outside_lift=empty_pos, inside_lift=empty_pos, goal_position=empty_pos, out_lift_name="", in_lift_name="", goal_floor="", goal_room="", house="")
        self.state.update_taskId(0)
        self.statusBackend.update_statusBackend(0, 0)


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
            """
            taskId = self.state.get_state().get("taskId")
            
            if taskId == 0:
                next_fetch = time.monotonic() + self.period
                self.stop_event.wait(0.2)
                continue
            """

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

                        # 如果是不同任务id(也就是机器人执行完了某个任务, 或者根本没执行任何任务)
                        # 收到了来自后台的 response -- 30 or 40 则更新机器人状态, 添加任务信息, 更新后台状态记录
                        if status_old != status_new and robot_taskId_old != taskId_new:
                            #get 相关值
                            code = data.get("code")
                            #配送任务的 Id 和 QR code
                            self.currentOrder.update_deliveryDetails(taskId=taskId_new, code=code)

                            #配送目的地相信信息的 获取&存储&更新
                            goal_addrList = taskInfo.get("addressList")
                            len_goal_addrList = len(goal_addrList)
                            self.store_goalPositions(goal=True, addrList=goal_addrList)
                            if len_goal_addrList == 3:
                                self.store_elevatorCommand(goal=True)

                            #配送完成返回地址信息的 获取&存储&更新
                            return_addrList = data.get("addressList")
                            len_return_addrList = len(return_addrList)
                            self.store_goalPositions(goal=False, addrList=return_addrList)
                            if len_return_addrList == 3:
                                self.store_elevatorCommand(goal=False)

                            #更新后台状态记录
                            self.statusBackend.update_statusBackend(taskId=taskId_new, status=status_new)
                            #然后更新机器人状态 -- 主要是任务id
                            self.state.update_taskStatus("idle")
                            self.state.update_taskId(taskId_new)
                            
                        # 如果同一个任务id情况下(机器人正在执行某一任务), 收到来自后台的response, 除了60 其他都不用管
                        if status_old != status_new and robot_taskId_old == taskId_new:
                            self.statusBackend.update_statusBackend(taskId=taskId_new, status=status_new)
                            # 是 60 取消任务的话
                            if status_new == 60:
                                self.state.update_taskId(0)
                                self.state.update_taskStatus("cancel_delivery")
                    else:
                        #配送完成返回地址信息的 获取&存储&更新
                        return_addrList = data.get("addressList")
                        len_return_addrList = len(return_addrList)
                        self.store_goalPositions(goal=False, addrList=return_addrList)
                        if len_return_addrList == 3:
                            self.store_elevatorCommand(goal=False)
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
        addr_len = len(addrList)

        lift_out = {}
        lift_in = {}
        pos = {}
        out_lift_name = ""
        in_lift_name = ""
        flr = ""
        room = ""
        house = ""

        #机器人和目标位置在同一楼层
        if addr_len == 1:
            empty_pos = {"x": 0, "y": 0, "theta": 0}
            lift_out = empty_pos
            lift_in = empty_pos
            pos = addrList[0].get("pose").get("dock")
            flr = addrList[0].get("floor")
            room = addrList[0].get("identity").get("desc")
            house = addrList[0].get("house")

        #机器人和目标位置不在同一楼层
        elif addr_len == 3:
            for item in addrList:
                desc = item.get("identity").get("desc")
                dock = item.get("pose").get("dock")
                if "ELEVATOR_out" in desc:
                    lift_out = dock
                    out_lift_name = desc
                elif "ELEVATOR_in" in desc:
                    lift_in = dock
                    in_lift_name = desc
                else:
                    pos = dock
                    flr = item.get("floor")
                    room = desc
                    house = item.get("house")

        #后台传输参数有错
        else:
            rospy.loginfo("\n <executor - 484> Backend response bad parameters.\n")

        if goal:
            self.currentOrder.update_goalPositions(outside_lift=lift_out, inside_lift=lift_in, goal_position=pos, out_lift_name=out_lift_name, in_lift_name=in_lift_name, goal_floor=flr, goal_room=room, house=house)
        else:
            self.currentOrder.update_returnPositions(outside_lift=lift_out, inside_lift=lift_in, return_position=pos, out_lift_name=out_lift_name, in_lift_name=in_lift_name, return_floor=flr, return_room=room, house=house)

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
    interaction_thread = InteractionThread(state=state, statusBackend=statusBackend, currentOrder=currentOrder, elevatorPlan=elevatorPlan , ros_pub_goal=ros_pub_goal, robot_mqtt=robot_mqtt, http_client=http_client, stop_event=stop_event)
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
        