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

#这里需要修改
class Worker():
    def __init__(self, state, robot_mqtt, http_client, ros_pub):
        """
        这个类主要用来运行与后台通过HTTP交互
        参数:
            state: 用于根据后台的交互更新机器人相应状态
            robot_mqtt: 已初始化并且连接 MQTT broker的客户端实例, 用于随时发布更新的状态消息
            http_client: HTTP 客户端实例, 用于调用后台任务相关的接口
            ros_pub: ROS publisher, 用于向路径规划模块发送 goal & floor 等信息
        """
        self.state = state
        self.robot_mqtt = robot_mqtt
        self.http_client = http_client
        self.ros_pub = ros_pub
        self.stop_event = stop_event
        self.taskId = 0
    
    def run(self):
        taskStatus = self.state.get_state().get("taskStatus")

        if taskStatus == "idle" and self.taskId == 0:
            #调用HTTP接口获得任务信息
            response = self.http_client.select_taskInfo()
                
            taskId = response.get("taskInfo").get("id")
            dock = response.get("taskInfo").get("addressParams").get("pose").get("dock")
            floor = response.get("taskInfo").get("addressParams").get("floor")

            self.taskId = taskId
            self.state.update_taskId(taskId)
            self.state.update_taskStatus("delivering")

            self.robot_mqtt.publish_state()

            self.publish_goal(dock, floor)

            rospy.loginfo(f"Assigned task: {taskId}, addr={dock}, floor={floor}")

        elif taskStatus == "arrived":
            #调用HTTP接口2通知后台机器人已到达
            response = self.http_client.update_taskStatus(dataInfo.TaskStatus.PENDING_RECEIPT.value)
            #然后开始一个计时器
            #在计时器没到时间之前调用核对QR码的接口
            #如果核对成功则调用<接口3>通知后台取货成功, 同时更新机器人的任务状态为 delivered
            #如果计时器到时, 则调用<接口4>通知后台取货失败, 同时更新机器人状态为 delivered_failed (这个状态需要新增)
            #然后等到 机器人 返回可以重新规划下一个路径的 点位, tianxin会发信号, 然后机器人更新状态为idle.
            #记得这个类里的taskId设为0
    
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
    
    http_worker = Worker(state, robot_mqtt, http_client, ros_pub)

    stop_event = threading.Event()
    state_thread = StateThread(robot_mqtt, stop_event)
    state_thread.start()
    
    try:
        rospy.spin()
    finally:
        #回收线程
        stop_event.set()
        state_thread.join(timeout=1)
        #正常退出发布离线消息
        robot_mqtt.publish_connection(status="offline", reason="shutdown")
        robot_mqtt.stop()