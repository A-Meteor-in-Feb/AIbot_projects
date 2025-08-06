import json
import socket
import paho.mqtt.client as mqtt
from datetime import datetime
from datetime import timezone
import argparse
import uuid
import time
import threading
from multiprocessing import Process
import random


BROKER_HOST = "10.25.0.2"
BROKER_PORT = 1883

ORG_ID = "AIbot"

DEVICE_TYPE = "robot"
ROBOT_ID = ""
ROBOT_IP = ""

connect_event = threading.Event()

def on_connect(client, userdata, flags, reason_code, properties):
    """
        connect callback
    """
    print(f"Connected with the result code {reason_code}")
    if reason_code == 0:
        connect_event.set()


def state_callback():
    """
        callback function for robots/{robotId}/state topic.
    """
    battery = random.randint(0, 100)
    payload = {
        "position": {
            "x": 1.1,
            "y": 2.2,
            "z": 3.3
        },
        "coordinateType": "geodetic",
        "battery": battery,
        "taskStatus": "idle",
        "connection": "connection",
        "autonomousMode": False,
        "fault": False,
        "binsNum": 6
    }

    print(f"{ROBOT_ID}'s battery: {battery}")
    
    message = json.dumps(payload).encode("utf-8")

    mqtt_client.publish(f"robots/{ROBOT_ID}/state", message, qos=0)


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
    
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect((BROKER_HOST, BROKER_PORT))
        return s.getsockname()[0]
    """
    return "10.25.0.5"
    


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


def run_single(robot_id, freq):

    global ROBOT_ID, mqtt_client, connect_event
    ROBOT_ID = robot_id
    CLIENT_ID = f"d:{ORG_ID}:{DEVICE_TYPE}:{ROBOT_ID}"

    print(f"{ROBOT_ID}: starting, freq={freq}Hz")

    mqtt_client = mqtt.Client(client_id=CLIENT_ID, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)

    #mqtt_client.on_connect = on_connect
    mqtt_client.on_connect = lambda client, u, f, rc, p: connect_event.set() if rc==0 else None

    #LAST WILL 
    last_will_set()

    mqtt_client.connect(host=BROKER_HOST, port=BROKER_PORT, keepalive=60)
    mqtt_client.loop_start()
    
    if not connect_event.wait(timeout=10):
        print("Warning: MQTT connection timeout")
    else:
        print("Successfully connected.")
        online_notification()
        ip_notification()

    duration = 60
    end_time = time.time() + duration

    try:
        interval = 1.0 / freq
        while time.time() < end_time:
            state_callback()
            time.sleep(interval)
    except Exception as e:
        print(f"{robot_id} error", e)
        mqtt_client.reconnect()
    finally:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        prog= "mqtt_stressTesting.py",
        description= "Robot simulator publishes high-frequency data"
    )
    parser.add_argument(
        "--robot-id",
        type=str,
        default=uuid.uuid4().hex[:8],
        help="Robot ID"
    )
    parser.add_argument(
        "--freq-hz",
        type=int,
        default=50,
        help="the data publish frequency"
    )
    parser.add_argument(
        "--num", "-n",
        type=int, 
        default=1,
        help="robot's amount"
    )
    args = parser.parse_args()

    if args.num == 1:
        run_single(args.robot_id, args.freq_hz)
    else:
        procs = []
        for i in range(1, args.num + 1):
            rid = f"{args.robot_id}{i:02d}"
            p = Process(target=run_single, args=(rid, args.freq_hz))
            p.start()
            procs.append(p)
            time.sleep(0.02)
        for p in procs:
            p.join()