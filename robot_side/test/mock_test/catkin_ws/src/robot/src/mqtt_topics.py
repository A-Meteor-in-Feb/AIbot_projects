#!/usr/bin/env python3
#import rospy
import json
import socket
import paho.mqtt.client as mqtt
#from robot.msg import State
from datetime import datetime
from datetime import timezone
import threading
import time

BROKER_HOST = "10.25.0.2"
BROKER_PORT = 1883

ORG_ID = "AIbot"

DEVICE_TYPE = "robot"
ROBOT_ID = "R1234"
TOKEN = "ABCDEF12345"
ROBOT_IP = ""

CLIENT_ID = f"d:{ORG_ID}:{DEVICE_TYPE}:{ROBOT_ID}"

last_state_bytes = None
last_state_recv = None
lock = threading.Lock()


def on_connect(client, userdata, flags, reason_code, properties):
    """
        connect callback
    """
    print(f"Connected with the result code {reason_code}")
    online_notification()
    ip_notification()

"""
def encode_state(msg: State) -> bytes:
    payload = {
        "position": {
            "x": msg.position.x,
            "y": msg.position.y,
            "z": msg.position.z
        },
        "coordinateType": msg.coordinateType,
        "battery": msg.battery,
        "taskStatus": msg.taskStatus,
        "taskId": msg.taskId,
        "connection": msg.connection,
        "autonomousMode": msg.autonomousMode,
        "fault": msg.fault,
        "binsNum": msg.binsNum
    }
    return json.dumps(payload).encode("utf-8")

def state_callback(msg: State):
    global last_state_bytes, last_state_recv
    state_bytes = encode_state(msg)
    mqtt_client.publish("robots/R1234/state", state_bytes, qos=0)
    print("forward MQTT state to backend")

    with lock:
        last_state_bytes = state_bytes
        last_state_recv = rospy.Time.now()

def heartbeat_state(event):
    with lock:
        if last_state_bytes is None or last_state_recv is None:
            return
        gap = (rospy.Time.now() - last_state_recv).to_sec()

    if gap >= 5:
        mqtt_client.publish("robots/R1234/state", last_state_bytes, qos=0)
        print("Update heartbeat")
"""
def online_notification():
    """
        publish the mqtt client (robot side) online state
    """

    payload = {"status": "online", "reason": "connect"}

    message = json.dumps(payload).encode("utf-8")

    mqtt_client.publish(f"robots/{ROBOT_ID}/connection", message, qos=1, retain=False)

    print(f"Publish connection topic {payload}")


def last_will_set():
    """
        set last will for robot
    """

    payload = {"status": "offline", "reason": "disconnect"}

    message = json.dumps(payload).encode("utf-8")

    mqtt_client.will_set(f"robots/{ROBOT_ID}/connection", message, qos=1, retain=True)


def get_ip():
    """
        Get IP address.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect((BROKER_HOST, BROKER_PORT))
        return s.getsockname()[0]


def ip_notification():
    """
        Publish Robot's IP notification to the backend
    """

    global ROBOT_IP
    ROBOT_IP = get_ip()

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-4]+"Z"

    payload = {
        "interface": "wireguard",
        "ip": ROBOT_IP,
        "timestamp": timestamp
    }

    message = json.dumps(payload).encode("utf-8")

    mqtt_client.publish(f"robots/{ROBOT_ID}/network/ip", message, qos=1, retain=False)

    print(f"Publish network/ip topic {payload}")


def state_notify():
    payload = {
        "position": {"x": 0, "y": 0, "z": 0},
        "coordinateType": "local",
        "battery": 100,
        "taskStatus": "idle",
        "taskId": 0,
        "connection": "online",
        "autonomousMode": False,
        "fault": False,
        "binsNum": 0,
        "timestamp": "ts"
    }
    message = json.dumps(payload).encode("utf-8")
    print("publish state")
    mqtt_client.publish("robots/R1234/state", message, qos=0)


if __name__ == "__main__":

    #rospy.init_node('ros2mqtt_bridge', anonymous=True)

    mqtt_client = mqtt.Client(client_id=CLIENT_ID, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)

    mqtt_client.on_connect = on_connect

    #LAST WILL 
    last_will_set()

    mqtt_client.connect(host=BROKER_HOST, port=BROKER_PORT, keepalive=60)
    mqtt_client.loop_start()


    #rospy.Subscriber("state", State, state_callback, queue_size=1)
    #rospy.Timer(rospy.Duration(2.0), heartbeat_state, oneshot=False)

    #rospy.spin()
    try:
        while True:
            state_notify()
            time.sleep(2)
    except KeyboardInterrupt:
        print("exiting")
    finally:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
    