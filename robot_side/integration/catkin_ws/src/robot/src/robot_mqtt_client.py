#!/usr/bin/env python3
import rospy
import json
import struct
import ssl
import socket
import paho.mqtt.client as mqtt
from robot.msg import State
from robot.msg import Error
from robot.msg import Cargo
from datetime import datetime
from datetime import timezone

BROKER_HOST = "10.25.0.3"
BROKER_PORT = 1883

ORG_ID = "AIbot"

DEVICE_TYPE = "robot"
ROBOT_ID = "R1234"
TOKEN = "ABCDEF12345"
ROBOT_IP = ""

CLIENT_ID = f"d:{ORG_ID}:{DEVICE_TYPE}:{ROBOT_ID}"

CONN_HEADER_ID = 0
STATE_HEADER_ID = 0
ERROR_HEADER_ID = 0
CARGO_HEADER_ID = 0
IP_HEADER_ID = 0

VERSION = "version"
MANUFACTURER = "manu"
SERIAL_NUMBER = "serial"


def VDA_5050_header(header_id, version, manufacturer, serial_number) -> bytes:
    """
        Generate binary vda5050 message header.
        header_id: the id number for every topic.
        version: protocol's version.
        manufacturer: the manufacturer.
        serial_number: serial number
        return header
    """
    header_id_bytes = struct.pack(">I", header_id)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-4]+"Z"
    parts = [header_id_bytes, timestamp.encode("utf-8"), version.encode("utf-8"), manufacturer.encode("utf-8"), serial_number.encode("utf-8")]
    header = b"\n".join(parts)+b"\n"
    return header

def on_connect(client, userdata, flags, reason_code, properties):
    """
        connect callback
    """
    print(f"Connected with the result code {reason_code}")


def state_callback(msg):
    """
        callback function for robots/{robotId}/state topic.
    """

    global STATE_HEADER_ID
    STATE_HEADER_ID += 1

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
    
    vda5050_header = VDA_5050_header(STATE_HEADER_ID, VERSION, MANUFACTURER, SERIAL_NUMBER)
    vda5050_body = json.dumps(payload).encode("utf-8")

    message = vda5050_header+vda5050_body

    mqtt_client.publish(f"robot/{ROBOT_ID}/state", message, qos=0)

    rospy.loginfo(f"Forwarded state topic to MQTT: {payload}")


def error_callback(msg):

    global ERROR_HEADER_ID
    ERROR_HEADER_ID += 1

    payload = {
        "timestamp": msg.timestamp,
        "errorCode": msg.errorCode,
        "severity": msg.severity,
        "message": msg.message,
        "taskId": msg.taskId,
        "position": {
            "x": msg.position.x,
            "y": msg.position.y,
            "z": msg.position.z
        },
        "suggestion": msg.suggestion,
        "retryable": msg.retryable
    }

    vda5050_header = VDA_5050_header(ERROR_HEADER_ID, VERSION, MANUFACTURER, SERIAL_NUMBER)
    vda5050_body = json.dumps(payload).encode("utf-8")

    message = vda5050_header+vda5050_body

    mqtt_client.publish(f"robot/{ROBOT_ID}/error", message, qos=0)

    rospy.loginfo(f"Forwarded error topic to MQTT: {payload}")


def cargo_callback(msg):

    global CARGO_HEADER_ID
    CARGO_HEADER_ID += 1

    slots = []
    for item in msg.slots:
        slot = {}
        slot["slotId"] = item.slotId
        slot["occupied"] = item.occupied
        slot["itemId"] = item.itemId
        slots.append(slot)

    payload = {
        "timestamp": msg.timestamp,
        "doorStatus": msg.doorStatus,
        "cargoPresent": msg.cargoPresent,
        "slots": slots,
        "temperature": msg.temperature,
        "humidity": msg.humidity,
        "tamperAlert": msg.tamperAlert,
        "lastAccessMethod": msg.lastAccessMethod,
        "taskId": msg.taskId
    }

    vda5050_header = VDA_5050_header(CARGO_HEADER_ID, VERSION, MANUFACTURER, SERIAL_NUMBER)
    vda5050_body = json.dumps(payload).encode("utf-8")

    message = vda5050_header+vda5050_body

    mqtt_client.publish(f"robot/{ROBOT_ID}/cargo", message, qos=0)

    rospy.loginfo(f"Forwarded cargo topic: {payload}")


def online_notification():
    """
        publish the mqtt client (robot side) online state
    """

    global CONN_HEADER_ID
    CONN_HEADER_ID += 1

    payload = {"status": "online", "reason": "connect"}

    vda5050_header = VDA_5050_header(STATE_HEADER_ID, VERSION, MANUFACTURER, SERIAL_NUMBER)
    vda5050_body = json.dumps(payload).encode("utf-8")

    message = vda5050_header+vda5050_body

    mqtt_client.publish(f"robot/{ROBOT_ID}/connection", message, qos=1, retain=True)

    print(f"Publish connection topic {payload}")


def last_will_set():
    """
        set last will for robot
    """

    global CONN_HEADER_ID
    CONN_HEADER_ID += 1

    payload = {"status": "offline", "reason": "disconnect"}

    vda5050_header = VDA_5050_header(STATE_HEADER_ID, VERSION, MANUFACTURER, SERIAL_NUMBER)
    vda5050_body = json.dumps(payload).encode("utf-8")

    message = vda5050_header+vda5050_body

    mqtt_client.will_set(f"robot/{ROBOT_ID}/connection", message, qos=1, retain=True)


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
    global IP_HEADER_ID
    IP_HEADER_ID += 1

    global ROBOT_IP
    ROBOT_IP = get_ip()

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-4]+"Z"

    payload = {
        "interface": "wireguard",
        "ip": ROBOT_IP,
        "timestamp": timestamp
    }

    vda5050_header = VDA_5050_header(IP_HEADER_ID, VERSION, MANUFACTURER, SERIAL_NUMBER)
    vda5050_body = json.dumps(payload).encode("utf-8")

    message = vda5050_header+vda5050_body

    mqtt_client.publish(f"robot/{ROBOT_ID}/network/ip", message, qos=1, retain=False)

    print(f"Publish network/ip topic {payload}")


if __name__ == "__main__":

    rospy.init_node('ros2mqtt_bridge', anonymous=True)

    mqtt_client = mqtt.Client(client_id=CLIENT_ID, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)

    #Authentication
    #mqtt_client.username_pw_set(username=ROBOTID, password=TOKEN)
    
    #TLS
    #mqtt_client.tls_set(ca_certs="/home/avnuc/yangtianjiao/AIbot_projects/mqtt_certs/ca.crt", tls_version=ssl.PROTOCOL_TLSv1_2)
    
    mqtt_client.on_connect = on_connect

    #LAST WILL 
    last_will_set()

    mqtt_client.connect(host=BROKER_HOST, port=BROKER_PORT, keepalive=60)
    mqtt_client.loop_start()

    
    online_notification()
    
    ip_notification()

    rospy.Subscriber("state", State, state_callback)
    rospy.Subscriber("error", Error, error_callback)
    rospy.Subscriber("cargo", Cargo, cargo_callback)

    rospy.spin()

    mqtt_client.loop_stop()
    mqtt_client.disconnect()