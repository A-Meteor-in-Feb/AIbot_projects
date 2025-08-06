import json
import ssl
import paho.mqtt.client as mqtt

# self-defined class
from backend_robotInfo import Robot, Robots

BROKER_HOST = "10.25.0.2"
BROKER_PORT = 1883

ORG_ID = "AIbot"

ROBOT_ID_1 = "robot03"
ROBOT_ID_2 = "R1235"
ROBOT_VALID_TOKENS = {
    ROBOT_ID_1: "ABCDEF12345",
    ROBOT_ID_2: "1234567"
}
ROBOT_IP = ""

DEVICE_TYPE = "backend"
BACKEND_ID = "B1234"
BACKEND_TOKEN = "98765"
CLIENT_ID = f"d:{ORG_ID}:{DEVICE_TYPE}:{BACKEND_ID}"



def state_handler(client, userdata, msg):
    """
        process robot/{robotId}/state message.
        print corresponding header and data.
    """
    data_str = msg.payload.decode("utf-8")
    data = json.loads(data_str)
    print(f"The state topic from robot {ROBOT_ID_1} side:\n", data)


def connection_handler(client, userdata, msg):
    """
        process robot/{robotId}/connect message.
        print corresponding header and data.
    """
    data_str = msg.payload.decode("utf-8")
    data = json.loads(data_str)
    print(f"The connection topic from robot {ROBOT_ID_1} side:\n", data)


def error_handler(client, userdata, msg):
    data_str = msg.payload.decode("utf-8")
    data = json.loads(data_str)
    print(f"The error topic from robot {ROBOT_ID_1} side:\n", data)


def cargo_handler(client, userdata, msg):
    data_str = msg.payload.decode("utf-8")
    data = json.loads(data_str)
    print(f"The cargo topic from robot {ROBOT_ID_1} side:\n", data)


def ip_handler(client, userdata, msg):
    data_str = msg.payload.decode("utf-8")
    data = json.loads(data_str)
    print(f"The network/ip topic from robot {ROBOT_ID_1} side:\n", data)
    

    # Update and store the info
    # robot_ip = data.get("ip")
    # for robot_item in robots:
        # if robot_item.robotId == ROBOT_ID_1:
            # robot_item.robotIP = robot_ip


TOPICS = [
    (f"robots/{ROBOT_ID_1}/state", 0, state_handler),
    (f"robots/{ROBOT_ID_1}/error", 0, error_handler),
    (f"robots/{ROBOT_ID_1}/cargo", 0, cargo_handler),
    (f"robots/{ROBOT_ID_1}/network/ip", 1, ip_handler),
    (f"robots/{ROBOT_ID_1}/connection", 1, connection_handler)
]


def on_connect(client, userdata, flags, reason_code, properties):
    """
        Callbcak for MQTT connection.
        Subscribe the topics.
    """
    print(f"Connected with the reason code {reason_code}")
    for topic, qos, handler in TOPICS:
        client.subscribe(topic, qos)
        client.message_callback_add(topic, handler)
        print(f"Subscribe to topic: {topic}; with QoS: {qos}.")


def on_disconnect(client, userdata, reason_code):
    print(f"Disconnect with reason code {reason_code}, reconnecting ...")
    client.reconnect()


if __name__ == "__main__":
    

    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=CLIENT_ID)

    #Authentication
    #mqtt_client.username_pw_set(username=BACKEND_ID, password=BACKEND_TOKEN)
    
    #TLS
    #mqtt_client.tls_set(ca_certs="/home/avnuc/yangtianjiao/AIbot_projects/mqtt_certs/ca.crt", tls_version=ssl.PROTOCOL_TLSv1_2)
    
    mqtt_client.on_connect = on_connect

    mqtt_client.connect(BROKER_HOST, BROKER_PORT, 60)

    try:
        mqtt_client.loop_forever()
    except KeyboardInterrupt:
        print("exiting ...")