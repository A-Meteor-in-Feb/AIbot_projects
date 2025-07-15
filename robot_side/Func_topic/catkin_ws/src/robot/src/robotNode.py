#!/usr/bin/env python3
import rospy
import json
import struct
import ssl
import paho.mqtt.client as mqtt
from robot.msg import State
from robot.msg import Connection
from datetime import datetime
from datetime import timezone

HOST = "127.0.0.1"
PORT = 8883
ROBOTID = "R1234"

STATE_HEADER_ID = 0
CONN_HEADER_ID = 0
VERSION = "version"
MANUFACTURER = "manu"
SERIAL_NUMBER = "serial"


def VDA_5050_header(header_id, version, manufacturer, serial_number) -> bytes:
    header_id_bytes = struct.pack(">I", header_id)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-4]+"Z"
    parts = [header_id_bytes, timestamp.encode("utf-8"), version.encode("utf-8"), manufacturer.encode("utf-8"), serial_number.encode("utf-8")]
    header = b"\n".join(parts)+b"\n"
    return header

def on_connect(client, userdata, flags, reason_code, properties):
    #rospy.loginfo(f"Connected with the result code {reason_code}")
    print(f"Connected with the result code {reason_code}")


def state_callback(msg):

    global STATE_HEADER_ID
    STATE_HEADER_ID += 1

    payload = {
        "position": {"x": msg.x, "y": msg.y, "z": msg.z},
        "battery": msg.battery,
        "taskStatus": msg.taskStatus,
        "connection": msg.connection,
        "fault": msg.fault,
        "cargoLoad": msg.cargoLoad
    }
    
    vda5050_header = VDA_5050_header(STATE_HEADER_ID, VERSION, MANUFACTURER, SERIAL_NUMBER)
    vda5050_body = json.dumps(payload).encode("utf-8")

    message = vda5050_header+vda5050_body

    mqtt_client.publish(f"robot/{ROBOTID}/state", message, qos=0)

    rospy.loginfo(f"Forwarded state topic to MQTT: {payload}")


def online_notification():

    global CONN_HEADER_ID
    CONN_HEADER_ID += 1

    payload = {"status": "online", "reason": "connect"}

    vda5050_header = VDA_5050_header(STATE_HEADER_ID, VERSION, MANUFACTURER, SERIAL_NUMBER)
    vda5050_body = json.dumps(payload).encode("utf-8")

    message = vda5050_header+vda5050_body

    mqtt_client.publish(f"robot/{ROBOTID}/connection", message, qos=1, retain=True)


def last_will_set():

    global CONN_HEADER_ID
    CONN_HEADER_ID += 1

    payload = {"status": "offline", "reason": "disconnect"}

    vda5050_header = VDA_5050_header(STATE_HEADER_ID, VERSION, MANUFACTURER, SERIAL_NUMBER)
    vda5050_body = json.dumps(payload).encode("utf-8")

    message = vda5050_header+vda5050_body

    mqtt_client.will_set(f"robot/{ROBOTID}/connection", message, qos=1, retain=True)


if __name__ == "__main__":

    rospy.init_node('ros2mqtt_bridge', anonymous=True)

    mqtt_client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id="mqtt_publisher")
    
    #TLS
    mqtt_client.tls_set(ca_certs="/home/avnuc/yangtianjiao/AIbot_projects/mqtt_certs/ca.crt", tls_version=ssl.PROTOCOL_TLSv1_2)
    
    mqtt_client.on_connect = on_connect

    #LAST WILL 
    last_will_set()

    mqtt_client.connect(host=HOST, port=PORT, keepalive=60)
    mqtt_client.loop_start()

    online_notification()

    rospy.Subscriber("state", State, state_callback)

    rospy.spin()

    mqtt_client.loop_stop()
    mqtt_client.disconnect()