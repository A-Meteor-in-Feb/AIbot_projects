import rospy
import json
import socket
from datetime import datetime,timezone
import paho.mqtt.client as mqtt
import ros_sub


def utc_now_ms():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def on_connect(client, userdata, reason_code, properties):
    print(f"Robot mqtt client connected with {reason_code}")
    online_notification()
    ip_notification()


def on_disconnect(client, userdata, flags, reason_code, properties):
    print(f"Robot MQTT disconnected with {reason_code}, reconnecting...")


def online_notification():
    payload = {"status": "online", "reason": "connect"}
    message = json.dumps(payload).encode("utf-8")
    robot_mqtt.publish(f"robots/{ROBOT_ID}/connection", message, qos=1, retain=True)
    print(f"Publish connection topic {payload}")


def set_lastWill():
    payload = {"status": "offline", "reason": "disconnect"}
    message = json.dumps(payload).encode("utf-8")
    robot_mqtt.will_set(f"robots/{ROBOT_ID}/connection", message, qos=1, retain=True)


def get_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect((BROKER_HOST, BROKER_PORT))
            return s.getsockname()[0]
    except Exception:
        return ""


def ip_notification():
    global ROBOT_IP
    ROBOT_IP = get_ip()

    payload = {
        "interface": "wireguard",
        "ip": ROBOT_IP,
        "timestamp": utc_now_ms()
    }
    message = json.dumps(payload).encode("utf-8")
    
    robot_mqtt.publish(f"robots/{ROBOT_ID}/network/ip", message, qos=1, retain=False)
    print(f"Publish network/ip topic {payload}")


def publish_state(state):

    payload = {
        "position": state["position"],
        "coordinateType": "",
        "battery": state["battery"],
        "taskStatus": "",
        "taskId": "",
        "connection": "online",
        "autonomousMode": False,
        "fault": state["fault"],
        "binsNum": 5
    }
    message = json.dumps(payload).encode("utf-8")

    robot_mqtt.publish(f"robots/{ROBOT_ID}/state", message, qos=0)
    print("publish robot's state topic:", payload)



if __name__ == "__main__":
    rospy.init_node("ros_mqtt_bridge", anonymous=False)

    BROKER_HOST = rospy.get_param("~mqtt_host")
    BROKER_PORT = int(rospy.get_param("~mqtt_port"))
    ROBOT_ID = rospy.get_param("~robot_id")

    robot_node = ros_sub.RobotStateSubscriber()

    robot_mqtt = mqtt.Client(
        client_id=ROBOT_ID, 
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        clean_session=False #持久会话, 断线重连保持会话状态
    )
    robot_mqtt.on_connect = on_connect
    robot_mqtt.on_disconnect = on_disconnect
    #指数退避式自动重连
    robot_mqtt.reconnect_delay_set(min_delay=1, max_delay=30)

    #异常下线会发disconnect通知
    set_lastWill()

    try:
        #使用connect_async 实现即使首次连接失败也会重试
        robot_mqtt.connect_async(host=BROKER_HOST, port=BROKER_PORT, keepalive=60)
    except Exception as e:
        print("MQTT connected failed:", e)

    robot_mqtt.loop_start()

    rate = rospy.Rate(0.5) #每2秒

    try:
        while not rospy.is_shutdown():
            state = robot_node.get_robot_state()
            print("robot's state: ", state)
            try:
                publish_state(state)
            except Exception as e:
                print("MQTT publish error:", e)
                
            rate.sleep()
    #正常下线也会发disconnect通知
    finally:
        try:
            offline = {"status": "offline", "reason": "shutdown"}
            message = json.dumps(offline).encode("utf-8")
            robot_mqtt.publish(f"robots/{ROBOT_ID}/connection",message, qos=1, retain=True)
        except Exception as e:
            print("Error happens at the shutdown stage", e)

        robot_mqtt.loop_stop()
        robot_mqtt.disconnect()

"""
测试要测: 连通性(正常情况 & 网络落后于代码执行看能不能成功连上), last will, 以及 断线重连情况.
"""