import time
import threading
import rospy
from robot_v2.msg import Goal
from geometry_msgs.msg import PoseStamped
from tf.transformations import quaternion_from_euler

import mqttClient
import rosSub
import httpClient
import dataInfo


class StateThread(threading.Thread):
    def __init__(self, robot_mqtt, stop_event: threading.Event):
        """
        这个线程控制机器人持续性向后台上报自己的状态消息
        参数:
            robot_mqtt: 已初始化并且连接 MQTT broker的客户端实例, 用于发布状态消息
            stop_event: 线程终止事件标志
        """
        super().__init__(daemon=True)
        self.robot_mqtt = robot_mqtt
        self.stop_event = stop_event

    def run(self):
        """
        每间隔 HEARTBEAT 时间(5秒) 发布一次 robots/{robotId}/state 主题消息
        """
        next_time = time.monotonic()
        while not self.stop_event.is_set() and not rospy.is_shutdown():
            now = time.monotonic()
            if now >= next_time:
                try:
                    self.robot_mqtt.publish_state()
                except Exception as e:
                    rospy.logwarn(f"state topic publish error:", e)
                next_time = now + HEARTBEAT
            
            self.stop_event.wait(0.1)


class InteractionThread(threading.Thread):
    def __init__(self, state, robot_mqtt, http_client, ros_pub, stop_event: threading.Event):
        """
        这个类主要用来运行与后台通过HTTP交互
        参数:
            state: 用于根据后台的交互更新机器人相应状态
            robot_mqtt: 已初始化并且连接 MQTT broker的客户端实例, 用于随时发布更新的状态消息
            http_client: HTTP 客户端实例, 用于调用后台任务相关的接口
            ros_pub: ROS publisher, 用于向路径规划模块发送 goal & floor 等信息
            stop_event: 线程终止事件标志
        """
        super().__init__(daemon=True)
        self.state = state
        self.robot_mqtt = robot_mqtt
        self.http_client = http_client
        self.ros_pub = ros_pub
        self.stop_event = stop_event

    def run(self):
        while not self.stop_event.is_set() and not rospy.is_shutdown():

            taskStatus = self.state.get_state().get("taskStatus")

            next_fetch = time.monotonic()
            while taskStatus == "idle":
                now = time.monotonic
                if now >= next_fetch:
                    success_fetch = self.fetch_taskInfo()
                    if success_fetch:
                        break
                    else:
                        next_fetch = time.monotonic() + 30
                        continue

            if taskStatus == "arrived":
                success_process = self.delivery_process()

                if success_process:
                    #开启货仓门让用户取货
                    #一定时间后关闭货仓门
                    success_complete = self.notify_deliveryComplete()
                
                else:
                    #通知后台配送失败
                    success_notify = self.notify_deliveryFailed()

    def fetch_taskInfo(self):
        """
        这个函数的作用:
            1. 调用httpClient中的接口1 - 机器人主动从后台拉取任务信息
            2. 得到响应数据之后, 调用publish_goal() 函数 将提取到的 dock & floor 发给tianxin
            3. 更新机器人状态为 delivering 以及 更新state话题中的 taskId 字段 -- (这个功能待定, 先这样写着; 
                之后可以看看能不能在tianxin收到数据之后发给我一个信号我再改状态, 不过这样的话就要考虑是不是机器人会重复拉取任务; 
                所以为了避免这个重复拉取的问题, 要么我直接把状态改成delivering, 要不然我通过taskId的字段去判断是不是要重复拉取.
                总而言之, 现在是由我直接改了 taskStatus 以及 taskId)
            4. 机器人更新完状态之后 直接 发布一次新的 robots/{robotId}/state 话题
        """
        #调用接口1
        response_data = self.http_client.select_taskInfo()

        if response_data:
            taskId = response_data.get("taskInfo").get("id")
            dock = response_data.get("taskInfo").get("addressParams").get("pose").get("dock")
            floor = response_data.get("taskInfo").get("addressParams").get("floor")
            
            #先给tianxin发布话题
            try:
                self.publish_goal(dock, floor)
            except Exception as e:
                rospy.loginfo("Error happens when try to publish Goal topic to tianxin.\n Error:", e)
                return False
            
            #更新机器人相关状态
            self.state.update_taskId(taskId)
            self.state.update_taskStatus("delivering")
            
            #再向后台发布更新过的机器人状态
            try:
                self.robot_mqtt.publish_state()
            except Exception as e:
                rospy.loginfo("Error happens when try to publish state topic to the backend.\n Error:", e)

            rospy.loginfo(f"Assigned task: {taskId}, addr={dock}, floor={floor}")
            return True
        else:
            rospy.loginfo("Did not receive response from the backend")
            return False
    
    def publish_goal(self, dock, floor):
        """
        给tianxin发布他规划路径需要的数据
        参数:
            dock: dict, 目标位置
            floor: str, 目标楼层
        """
        ps = PoseStamped()
        ps.header.stamp = rospy.Time.now()
        ps.header.frame_id = "map"
        ps.pose.position.x = dock['x']
        ps.pose.position.y = dock['y']
        ps.pose.position.z = 0.0
        
        q = quaternion_from_euler(0.0, 0.0, dock['theta'])
        ps.pose.orientation.x = q[0]
        ps.pose.orientation.y = q[1]
        ps.pose.orientation.z = q[2]
        ps.pose.orientation.w = q[3]

        goal = Goal()
        goal.pose = ps
        goal.floor = floor

        self.ros_pub.publish(goal)
        print("Forwarded the goal info to the planning and localization part")

    def delivery_process(self):
        """
        这个函数的作用是:
            1. 调用<接口2>, 通知后台机器人已到达, 不过是否连接成功或者成功响应与否都没关系
            2. 在一定时间内核对二维码, 二维码OK 则返回True
            3. 如果超过deadline还没有成功核对二维码, 则返回False
        """
        #调用接口2
        response = self.http_client.update_taskStatus(dataInfo.TaskStatus.PENDING_RECEIPT.value)
        
        #设置超时时间
        deadline = time.monotonic + TIMEOUT

        while time.monotonic() <= deadline:

            # 核对二维码
            # 核对不成功则一直尝试
            # 核对成功则 改机器人状态为 delivered 然后发布新的 state topic
            # return True 
            return True
            
        # 到时之后机器人状态需要更新为 delivery_failed, 并且发布新的 state topic
        # 然后返回False
        return False
    
    def notify_deliveryComplete(self):
        """
        这个函数的作用是:
            1. 调用<接口3>, 通知后台机器人已成功配送订单
            2. 接收响应数据 -- 现在目前不知道响应数据会有什么用
            3. 更新机器人taskStatus 为 delivered, 并立即发送 robots/{robotId}/state 话题
        """
        #调用接口3
        response = self.http_client.update_taskStatus(dataInfo.TaskStatus.DELIVERY_COMPLETE.value)
        
        #更新机器人状态并发布 state 主题
        self.state.update_taskStatus("delivered")
        self.robot_mqtt.publish_state()

        return True
    
    def notify_deliveryFailed(self):
        """
        这个函数的作用是:
            1. 调用<接口4>, 通知后台机器人配送订单失败
            2. 接收响应数据 -- 现在目前不知道响应数据会有什么用
            3. 更新机器人taskStatus 为 delivered_failed, 并立即发送 robots/{robotId}/state 话题
        """
        #调用接口4
        response = self.http_client.update_taskStatus(dataInfo.TaskStatus.DELIVERY_FAILED.value)

        #更新机器人状态并发布 state 主题
        self.state.update_taskStatus("delivered_failed")
        self.robot_mqtt.publish_state()

        return True

                
if __name__ == "__main__":

    HEARTBEAT = 5
    TIMEOUT = 180
    BROKER_HOST = "10.25.0.2"
    BROKER_PORT = 1883
    BACKEND_HOST = "10.25.0.15"
    BACKEND_PORT = "18001"
    HTTP_HEAD = "http"
    ROBOTID = "18950214603"
    PRIVATE_KEY = "z/CszPJh61yWfA1eJhmDKg=="
    IV_VECTOR = "tBPz/vp+8x9ps4ikCj6btA=="


    rospy.init_node("robot_commNode", anonymous=False)
    ros_pub = rospy.Publisher("goal", Goal, queue_size=1)
    state = dataInfo.StateInfo()
    robot_mqtt = mqttClient.MqttClient(BROKER_HOST, BROKER_PORT, ROBOTID, state)
    robot_mqtt.connect()
    ros_sub = rosSub.RosStateSub(state)
    http_client = httpClient.HttpClient(HTTP_HEAD, BACKEND_HOST, BACKEND_PORT, ROBOTID, PRIVATE_KEY, IV_VECTOR)

    rospy.loginfo("MQTT client and ROS subscribers initialized done.")
    
    stop_event = threading.Event()
    state_thread = StateThread(robot_mqtt, stop_event)
    interaction_thread = InteractionThread(state, robot_mqtt, http_client, ros_pub, stop_event)
    state_thread.start()
    interaction_thread.start()
    
    rospy.loginfo("Threads start working successfully.")

    try:
        rospy.spin()
    finally:
        #回收线程
        stop_event.set()
        state_thread.join(timeout=1)
        interaction_thread.join(timeout=1)
        #正常退出发布离线消息
        robot_mqtt.publish_connection(status="offline", reason="shutdown")
        robot_mqtt.stop()