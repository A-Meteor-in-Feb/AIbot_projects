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
#import httpServer
import encryption
#import qrCode
#import elevatorFlowGetter

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
    def __init__(self, robotState: dataInfo.RobotStateInfo, relocalizationInfo:dataInfo.RelocalizationInfo, 
                 http_client: httpClient.HttpClient, ros_pub_goal, stop_event: threading.Event):
        
        super().__init__(daemon=True)

        self.robotState = robotState
        self.relocalizationInfo = relocalizationInfo
        self.ros_pub_goal = ros_pub_goal
        self.http_client = http_client
        self.stop_event = stop_event

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

            if robotStatus == "reset_address":
                # TODO: 看现在有没有在执行任务的状态, 如果在的话, 直接把所有的任务数据删掉即可

                try:
                    relocalization = self.relocalizationInfo.get_relocalizationInfo()
                    relocalization_pos = relocalization.get("relocalization_position")
                    relocalization_floor = relocalization.get("floor")
                    relocalization_house = relocalization.get("house")
                except Exception as e:
                    rospy.loginfo(f"\n <executor-92> Error in READ GOAL: {e}\n")

                try:
                    self.publish_goal(goal_pos=relocalization_pos, goal_floor=relocalization_floor , goal_house=relocalization_house , relocation=True, robotStatus_old=robotStatus)
                except Exception as e:
                    rospy.loginfo(f"\n <executor-92> Error in PUBLISH GOAL: {e}\n")
            
            elif robotStatus == "reset_success":
                self.relocalizationInfo.reset_relocalizationInfo()

            elif robotStatus == "reset_failure":
                self.toBackend_reportWarn(taskId=None, type="reset_failure")
        
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

    def publish_goal(self, goal_pos, goal_floor, goal_house, relocation, robotStatus_old):
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
        self.publish_goal_wait(robotStatus_old=robotStatus_old)
        
    def publish_goal_wait(self, robotStatus_old):
        """
        控制每0.1秒检查一次状态
        如果tianxin没有给我发接收到目标地址的信号, 则超时后将重发
        """
        rate = rospy.Rate(10) 
        waited = 0
        while waited < 5.0:
                            
            if self.stop_event.is_set() or rospy.is_shutdown():
                break
                            
            robot_state = self.robotState.get_state()
            robotStatus_new = robot_state.get("taskStatus")
            if robotStatus_new != robotStatus_old:
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