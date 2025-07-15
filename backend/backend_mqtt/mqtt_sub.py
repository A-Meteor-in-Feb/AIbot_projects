import json
import struct
import paho.mqtt.client as mqtt


#HOST = "192.168.123.61"
#PORT = 1883
HOST = "127.0.0.1"
PORT = 1883
ROBOTID = "R1234"


def parse_message(vda5050_msg:bytes):

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
    (header, data) = parse_message(msg)
    print(f"The state topic from robot {ROBOTID} side:\n", data, "\n", header)

def connection_handler(client, userdata, msg):
    (header, data) = parse_message(msg)
    print(f"The connection topic from robot {ROBOTID} side:\n", data, "\n", header)



TOPICS = [
    (f"robot/{ROBOTID}/state", 0, state_handler),
    (f"robot/{ROBOTID}/connection", 1, connection_handler)
]


def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected with the reason code {reason_code}")
    for topic, qos, handler in TOPICS:
        client.subscribe(topic, qos)
        client.message_callback_add(topic, handler)
        print(f"Subscribe to topic: {topic}; with QoS: {qos}.")

def on_disconnect(client, userdata, reason_code):
    print(f"Disconnect with reason code {reason_code}, reconnecting ...")
    client.reconnect()


if __name__ == "__main__":
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="mqtt_subscriber")
    mqtt_client.on_connect = on_connect
    mqtt_client.on_disconnect = on_connect

    mqtt_client.connect(HOST, PORT, 60)
    try:
        mqtt_client.loop_forever()
    except KeyboardInterrupt:
        print("exiting ...")