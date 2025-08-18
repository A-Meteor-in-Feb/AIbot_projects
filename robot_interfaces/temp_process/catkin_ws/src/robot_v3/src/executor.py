import time
import threading
import rospy
from robot_v2.msg import Goal
from geometry_msgs.msg import PoseStamped
from tf.transformations import quaternion_from_euler
from std_msgs.msg import String

import mqttClient
import rosSub
import httpClient
import dataInfo
import httpServer
import encryption


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
                    rospy.logwarn(f"state topic publish error: {e}")
                next_time = now + self.heartbeat
            
            self.stop_event.wait(0.1)


class InteractionThread(threading.Thread):
    def __init__(self, state: dataInfo.StateInfo, statusBackend: dataInfo.StatusBackend, currentOrder: dataInfo.CurrentOrder, ros_pub_goal, ros_pub_returnSignal, robot_mqtt, http_client, stop_event: threading.Event):
        """
        这个类主要用来控制机器人的执行, 与后台交互, tianxin交互
        参数:
            state: 机器人自身的状态
            statusBackend: 后台分配任务的状态
            currentOrder: 机器人当前执行的任务的详细信息
            ros_pub_goal: ROS publisher for topic "Goal", 用于给tianxin发布目标地址和楼层
            ros_pub_returnSignal: ROS publisher for topic "signal/return:, 用来完成任务或取消任务之后, 给tianxin发送让机器人返回的信号
            robot_matt: 已初始化并且连接MQTT broker的客户端实例, 用于随时发布更新的状态消息
            http_client: HTTP 客户端实例, 用于调用后台任务相关的接口
            stop_event: 线程终止时间标志
        """
        super().__init__(daemon=True)

        self.state = state
        self.statusBackend = statusBackend
        self.currentOrder = currentOrder

        self.ros_pub_goal = ros_pub_goal
        self.ros_pub_returnSignal = ros_pub_returnSignal

        self.robot_mqtt = robot_mqtt
        self.http_client = http_client
        
        self.stop_event = stop_event

    def run(self):
        """
        逻辑执行部分
        """
        while not self.stop_event.is_set() and not rospy.is_shutdown():

            try:

                status = self.statusBackend.get_statusBackend().get("status")
                taskStatus = self.state.get_state().get("taskStatus")
                taskId = self.state.get_state().get("taskId")

                # 有任务ID, 则说明在正常配送
                if taskId != 0:
                    
                    #目前机器人空闲且被分配了任务, 规划路径开始delivering
                    if taskStatus == "idle" and status == 20:
                        #为了防止重发 先更新机器人状态为 assigned
                        self.state.update_taskStatus("assigned")

                        goal = self.currentOrder.get_currentOrder().get("goal_position")
                        floor = self.currentOrder.get_currentOrder().get("floor")

                        #给 tianxin 发目标位置, 他规划好会返回信号并更新机器人为delivering
                        try:
                            self.publish_goal(goal, floor)
                        except Exception as e:
                            rospy.loginfo(f"Error happens when PUBLISH GOAL: {e}")

                    #目前机器人到达目的地, 开始送货
                    if taskStatus == "arrived":
                        # step 1 - 核对二维码
                        code = self.currentOrder.get_currentOrder().get("code")
                        qr_check = self.qr_check()
                        # step 2 - 如果二维码核对成功, 控制货仓开关, 取货完成调用接口通知后台, 
                        # 并更新机器人状态为 delivered -- 更新机器人currentOrder 清空, taskId 清空, statusBackend 清空
                        if qr_check:
                            self.door_open()
                            self.notify_complete(taskId=taskId)
                        # step 2 - 如果二维码核对失败, 调用接口通知后台配送失败
                        # 并更新机器人状态为delivered_failed -- 更新机器人currentOrder 清空, taskId 清空, statusBackend 清空
                        else:
                            self.notify_failed(taskId=taskId)
                    
                    #机器人配送完成或者失败
                    if taskStatus == "delivered" or taskStatus == "delivered_failed":
                        #为了防止重发 先更新机器人状态为 returning
                        self.state.update_taskStatus("returning")

                        #给 tianxin 发可以return的信号
                        try:
                            self.publish_returnSignal()
                        except Exception as e:
                            rospy.loginfo(f"Error happens when PUBLISH GOAL: {e}")
                #没有任务ID则说明配送可能是被取消或者已完成
                else:
                    #任务被取消则先发送返回信号, 然后再设置status为0, 等到回到原点机器人会更新状态为idle
                    if taskStatus == "cancel_delivery":
                        #为了防止重发 先更新机器人状态为 returning
                        self.state.update_taskStatus("returning")

                        #给 tianxin 发可以return的信号
                        try:
                            self.publish_returnSignal()
                        except Exception as e:
                            rospy.loginfo(f"Error happens when PUBLISH GOAL: {e}")
                    
            except Exception as e:
                rospy.loginfo(f"Error happens in the main execution loop as {e}")

            self.stop_event.wait(0.1)


    def publish_goal(self, goal, floor):
        """
        给tianxin发布他规划路径需要的数据
        参数:
            goal: dict, 目标位置
            floor: str, 目标楼层
        """
        ps = PoseStamped()
        ps.header.stamp = rospy.Time.now()
        ps.header.frame_id = "map"
        ps.pose.position.x = goal['x']
        ps.pose.position.y = goal['y']
        ps.pose.position.z = 0.0
        
        q = quaternion_from_euler(0.0, 0.0, goal['theta'])
        ps.pose.orientation.x = q[0]
        ps.pose.orientation.y = q[1]
        ps.pose.orientation.z = q[2]
        ps.pose.orientation.w = q[3]

        goal = Goal()
        goal.pose = ps
        goal.floor = floor

        self.ros_pub_goal.publish(goal)
        rospy.loginfo("Forwarded the goal info to the planning part")

    def publish_returnSignal(self):
        """
        给tianxin发送小车可以开回做下一次路径规划的初始化点位
        """
        self.ros_pub_returnSignal.publish("RETURN")
        rospy.loginfo("Forwarded the return signal")
    
    def qr_check(self):
        """
        核对二维码, 计时核对, 超时还没有核对成功的话就算失败
        return:
            True: 核对成功
            False: 核对失败
        """
    
    def door_open(self):
        """
        控制货仓门打开或关闭, 然后判断是否取货成功, 需要拍照估计
        """

    def notify_complete(self, taskId):
        """
        这个函数的作用是:
            1. 调用<接口3>, 通知后台机器人已成功配送订单
            2. 接收响应数据 -- 现在目前不知道响应数据会有什么用
            3. 更新机器人taskStatus 为 delivered, 并立即发送 robots/{robotId}/state 话题
        """
        #调用接口3
        response = self.http_client.update_taskStatus(taskId, dataInfo.TaskStatus.DELIVERY_COMPLETE.value)
        
        if response:
            self.finalize_task()
            
        #更新机器人状态并发布 state 主题
        self.state.update_taskStatus("delivered")
        self.robot_mqtt.publish_state()

    def notify_failed(self, taskId):
        """
        这个函数的作用是:
            1. 调用<接口4>, 通知后台机器人配送订单失败
            2. 接收响应数据 -- 现在目前不知道响应数据会有什么用
            3. 更新机器人taskStatus 为 delivered_failed, 并立即发送 robots/{robotId}/state 话题
        """
        #调用接口4
        response = self.http_client.update_taskStatus(taskId, dataInfo.TaskStatus.DELIVERY_FAILED.value)

        if response:
            self.finalize_task()

        #更新机器人状态并发布 state 主题
        self.state.update_taskStatus("delivered_failed")
        self.robot_mqtt.publish_state()

    def finalize_task(self):
        self.currentOrder.update_currentOrder(0, "", {"x":0.0, "y":0.0, "theta":0.0}, "", "", 0)
        self.state.update_taskId(0)
        self.statusBackend.update_statusBackend(0, 0)


class FetchTaskThread(threading.Thread):
    def __init__(self, http_client, state: dataInfo.StateInfo, statusBackend: dataInfo.StatusBackend, currentOrder: dataInfo.CurrentOrder, period, stop_event: threading.Event):
        """
        这个线程用于执行周期性地从后台拉取任务信息, 为了避免因为网络问题没有得到最新的任务状态
        参数:
            http_client: 用来调用机器人客户端接口
            state: 机器人自身的状态
            statusBackend: 后台分配任务的状态
            currentOrder: 机器人当前执行的任务的详细信息
            period:
            stop_event: 线程终止时间标志
        """
        super().__init__(daemon=True)
        self.http_client = http_client
        self.state = state
        self.statusBackend = statusBackend
        self.currentOrder = currentOrder
        self.period = period
        self.stop_event = stop_event

    def run(self):
        next_fetch = time.monotonic()

        while not self.stop_event.is_set() and not rospy.is_shutdown():

            taskId = self.state.get_state().get("taskId")
            
            if taskId == 0:
                next_fetch = time.monotonic() + self.period
                self.stop_event.wait(0.2)
                continue

            now = time.monotonic()  
            if now >= next_fetch:
                status_old = self.statusBackend.get_statusBackend().get("status")

                response = self.http_client.select_taskInfo()
                if response:
                    taskId = response.get("data").get("taskInfo").get("id")
                    status_new = response.get("data").get("taskInfo").get("status")

                    if status_old != status_new:
                        self.statusBackend.update_statusBackend(taskId=taskId, status=status_new)

                        # 是取消任务的话
                        if status_new == 60:
                            self.currentOrder.update_currentOrder(0,"", {"x":0.0, "y":0.0, "theta":0.0}, "", "", 0)
                            self.state.update_taskId(0)
                            self.state.update_taskStatus("cancel_delivery")
                            self.statusBackend.update_statusBackend(taskId=0, status=0)
                
                next_fetch = now + self.period
            
            self.stop_event.wait(0.1)


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
    HEARTBEAT = 5 #控制MQTT 状态话题的周期性发送

    #连接参数
    BROKER_HOST = "10.25.0.2"
    BROKER_PORT = 1883
    HTTP_HEAD = "http"
    BACKEND_HOST = "10.25.0.15"   # "192.168.10.249"
    BACKEND_PORT = "18001"        # "8889"

    #ROS 发布话题名
    TOPIC_RETURN = "signal/return"
    TOPIC_GOAL = "goal"

    #临界资源初始化
    state = dataInfo.StateInfo()
    statusBackend = dataInfo.StatusBackend()
    currentOrder = dataInfo.CurrentOrder()

    #加密解密头部鉴权功能初始化
    httpEncryption = encryption.HttpEncryption(robotId=ROBOTID, private_key=PRIVATE_KEY, iv_vector=IV_VECTOR)

    #ros初始化 以及相关的 ros publisher 初始化
    rospy.init_node("robot_comNode", anonymous=False)
    ros_sub = rosSub.RosSub(state)
    ros_pub_goal = rospy.Publisher(TOPIC_GOAL, Goal, queue_size=1)
    ros_pub_returnSignal = rospy.Publisher(TOPIC_RETURN, String, queue_size=1)
    

    #mqtt初始化与连接 -- 成功连接会更新机器人状态为idle
    robot_mqtt = mqttClient.MqttClient(host=BROKER_HOST, port=BROKER_PORT, robot_id=ROBOTID, state=state)
    robot_mqtt.connect()

    #机器人客户端
    http_client = httpClient.HttpClient(head=HTTP_HEAD, host=BACKEND_HOST, port=BACKEND_PORT, httpEncryption=httpEncryption)

    #机器人服务器端
    http_server = httpServer.HttpServer(state=state, statusBackend=statusBackend, currentOrder=currentOrder)
    flask_app = create_flask_app(http_server)

    #线程启动
    stop_event = threading.Event()
    #MQTT 话题发布线程
    state_thread = StateThread(robot_mqtt, HEARTBEAT, stop_event)
    state_thread.start()
    #http client 线程
    interaction_thread = InteractionThread(state=state, statusBackend=statusBackend, currentOrder=currentOrder, ros_pub_goal=ros_pub_goal, ros_pub_returnSignal=ros_pub_returnSignal, robot_mqtt=robot_mqtt, http_client=http_client, stop_event=stop_event)
    interaction_thread.start()
    #fetch task info 线程
    fetchTask_thread = FetchTaskThread(http_client=http_client, state=state, statusBackend=statusBackend, currentOrder=currentOrder, period=HEARTBEAT, stop_event=stop_event)
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