import time
import threading
import rospy

import mqttClient
import rosSub
import httpClient
import dataInfo


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

    state = dataInfo.StateInfo()

    robot_mqtt = mqttClient.MqttClient(BROKER_HOST, BROKER_PORT, ROBOTID, state)
    robot_mqtt.connect()

    ros_sub = rosSub.RosStateSub(state)
    http_client = httpClient.HttpClient(HTTP_HEAD, BACKEND_HOST, BACKEND_PORT, ROBOTID, PRIVATE_KEY, IV_VECTOR)

    rospy.loginfo("MQTT client and ROS subscribers initialized")
    
    next_state = time.monotonic()
    #每5秒 (0.2hz) 发布一次state话题
    rate = rospy.Rate(0.2)
    try:
        while not rospy.is_shutdown():

            #发布状态数据
            now = time.monotonic()
            if now >= next_state:
                robot_mqtt.publish_state()
                # 计算下一次发布状态数据的时间节点
                now = time.monotonic()
                next_state = now + HEARTBEAT

            #如果当前机器人为idle则拉取任务信息
            robot_state = state.get_state()
            if robot_state["taskStatus"] == "idle":
                #调用HTTP接口获得任务信息
                response = http_client.select_taskInfo()
                
                taskId = response.get("taskInfo").get("id")
                dock = response.get("taskInfo").get("addressParams").get("pose").get("dock")
                floor = response.get("taskInfo").get("addressParams").get("floor")

                state.update_taskId(taskId)
                state.update_taskStatus("delivering")

                robot_mqtt.publish_state()

                rospy.loginfo(f"Assigned task: {taskId}, addr={dock}, floor={floor}")
            
            #当机器人到达目的地后, 调用接口通知后台机器人已到达, 现在是待收货的状态
            elif robot_state["taskStatus"] == "arrived":
                response = http_client.update_taskStatus(dataInfo.TaskStatus.PENDING_RECEIPT.value)

            rate.sleep()

    #正常退出发布离线消息
    finally:
        robot_mqtt.publish_connection(status="offline", reason="shutdown")
        robot_mqtt.stop()
