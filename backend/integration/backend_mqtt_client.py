import json
import ssl
import paho.mqtt.client as mqtt

# self-defined class
from backend_robotInfo import Robot, Robots

BROKER_HOST = "10.25.0.3"
BROKER_PORT = 1883

ORG_ID = "AIbot"

ROBOT_ID_1 = "R1234"
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


def parse_message(vda5050_msg:bytes):
    """
        Parse binary vda5050 message into header and data.
        vda5050_msg: The received data.
        return: (header, data)
    """

    message = vda5050_msg.payload.decode("utf-8")
    print(len(message))

    header_id_byte_str = message[:4]
    header_id_byte = header_id_byte_str.encode("latin-1")
    header_id = int.from_bytes(header_id_byte, byteorder='big', signed=True)

    rest = message[4:].split("\n", 5)
    timestamp = rest[1]
    version = rest[2]
    manufacturer = rest[3]
    serial_number = rest[4]

    header = {"header_id": header_id, "timestamp": timestamp, "version": version, "manufacturer": manufacturer, "serial_number": serial_number}

    vda5050_data = rest[5]
    data = json.loads(vda5050_data)

    return (header, data)


def state_handler(client, userdata, msg):
    """
        process robot/{robotId}/state message.
        print corresponding header and data.
    """
    (header, data) = parse_message(msg)
    print(f"The state topic from robot {ROBOT_ID_1} side:\n", data, "\n", header)


def connection_handler(client, userdata, msg):
    """
        process robot/{robotId}/connect message.
        print corresponding header and data.
    """
    (header, data) = parse_message(msg)
    print(f"The connection topic from robot {ROBOT_ID_1} side:\n", data, "\n", header)


def error_handler(client, userdata, msg):
    (header, data) = parse_message(msg)
    print(f"The error topic from robot {ROBOT_ID_1} side:\n", data, "\n", header)


def cargo_handler(client, userdata, msg):
    (header, data) = parse_message(msg)
    print(f"The cargo topic from robot {ROBOT_ID_1} side:\n", data, "\n", header)


def ip_handler(client, userdata, msg):
    (header, data) = parse_message(msg)
    print(f"The network/ip topic from robot {ROBOT_ID_1} side:\n", data, "\n", header)
    
    # Update and store the info
    robot_ip = data.get("ip")
    for robot_item in robots:
        if robot_item.robotId == ROBOT_ID_1:
            robot_item.robotIP = robot_ip


TOPICS = [
    (f"robot/{ROBOT_ID_1}/state", 0, state_handler),
    (f"robot/{ROBOT_ID_1}/error", 0, error_handler),
    (f"robot/{ROBOT_ID_1}/cargo", 0, cargo_handler),
    (f"robot/{ROBOT_ID_1}/network/ip", 1, ip_handler),
    (f"robot/{ROBOT_ID_1}/connection", 1, connection_handler)
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
    robot1 = Robot(robotId=ROBOT_ID_1, robotIP=None)
    robot2 = Robot(robotId=ROBOT_ID_2, robotIP=None)
    robots = Robots([robot1, robot2])

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