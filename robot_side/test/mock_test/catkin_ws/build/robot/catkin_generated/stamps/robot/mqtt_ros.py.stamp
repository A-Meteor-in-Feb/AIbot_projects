import rospy
import json
import paho.mqtt.client as mqtt
from std_msgs.msg import Float64MultiArray
from robot.msg import State
import drafts.robot_client as robot_client

TASKID = 0
BINID = 0

def inner_on_connect(client, userdata, flags, reason_code, properties):
    client.subscribe("goal", qos=1)
    client.message_callback_add("goal", inner_goal_handler)
    
def outer_on_connect(client, userdata, flags, reason_code, properties):
    print(f"outer mqtt connect with {reason_code}")

def inner_goal_handler(client, userdata, msg):
    data = json.loads(msg.payload.decode('utf-8'))

    global TASKID
    global BINID
    TASKID = data['taskId']
    BINID = data['binId']
    
    print(data)
    arr = Float64MultiArray(data=[data['x'], data['y'], data['z']])

    pub.publish(arr)
    
    print("Published goal")


def state_callback(msg):

    payload = {
        "position": {
            "x": msg.position.x,
            "y": msg.position.y,
            "z": msg.position.z
        },
        "coordinateType": "local",
        "battery": 100,
        "taskStatus": msg.taskStatus,
        "taskId": TASKID,
        "connection": "online",
        "autonomousMode": False,
        "fault": False,
        "binsNum": BINID
    }

    message = json.dumps(payload).encode("utf-8")
    outer_mqtt.publish("state", message, qos=0)

    result = ""

    if msg.taskStatus == "arrived":
        result = robot_client.get_authCode(TASKID)

    if result == "ok":
        payload = {
        "position": {
            "x": msg.position.x,
            "y": msg.position.y,
            "z": msg.position.z
        },
        "coordinateType": "local",
        "battery": 100,
        "taskStatus": "delivered",
        "taskId": TASKID,
        "connection": "online",
        "autonomousMode": False,
        "fault": False,
        "binsNum": BINID
    }

    message = json.dumps(payload).encode("utf-8")
    outer_mqtt.publish("state", message, qos=0)
    
    if msg.taskStatus == "delivered":
        result = robot_client.notify_taskComplete(TASKID)

    if result == "ok":
        payload = {
        "position": {
            "x": msg.position.x,
            "y": msg.position.y,
            "z": msg.position.z
        },
        "coordinateType": "local",
        "battery": 100,
        "taskStatus": "idle",
        "taskId": TASKID,
        "connection": "online",
        "autonomousMode": False,
        "fault": False,
        "binsNum": BINID
    }

    message = json.dumps(payload).encode("utf-8")
    outer_mqtt.publish("state", message, qos=0)
    



if __name__ == "__main__":
    rospy.init_node("mqtt_ros_bridge")
    pub = rospy.Publisher("goal", Float64MultiArray, queue_size=1)
    sub = rospy.Subscriber("state", State, state_callback, queue_size=1)

    inner_mqtt = mqtt.Client(client_id="inner_mqtt", callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    inner_mqtt.on_connect = inner_on_connect
    inner_mqtt.connect("192.168.10.249", 1883)
    inner_mqtt.loop_start()

    outer_mqtt = mqtt.Client(client_id="outer_mqtt", callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    outer_mqtt.on_connect = outer_on_connect
    outer_mqtt.connect("10.25.0.2", 1883)
    outer_mqtt.loop_start()

    rospy.spin()

    inner_mqtt.loop_stop()
    inner_mqtt.disconnect()
    outer_mqtt.loop_stop()
    outer_mqtt.disconnect()