import paho.mqtt.client as mqtt
import json

ROBOTID = "18950214603"

def state_handler(client, userdata, msg):
    """
        process robot/{robotId}/state message.
        print corresponding header and data.
    """
    data_str = msg.payload.decode("utf-8")
    data = json.loads(data_str)
    print(f"The state topic from robot {ROBOTID} side:\n", data)


def connection_handler(client, userdata, msg):
    """
        process robot/{robotId}/connect message.
        print corresponding header and data.
    """
    data_str = msg.payload.decode("utf-8")
    data = json.loads(data_str)
    print(f"The connection topic from robot {ROBOTID} side:\n", data)


def ip_handler(client, userdata, msg):
    data_str = msg.payload.decode("utf-8")
    data = json.loads(data_str)
    print(f"The network/ip topic from robot {ROBOTID} side:\n", data)
    


TOPICS = [
    (f"robots/{ROBOTID}/state", 0, state_handler),
    (f"robots/{ROBOTID}/network/ip", 1, ip_handler),
    (f"robots/{ROBOTID}/connection", 1, connection_handler)
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



if __name__ == "__main__":
    mqtt_client = mqtt.Client(client_id="backend_mqtt", callback_api_version=mqtt.CallbackAPIVersion.VERSION2)

    mqtt_client.on_connect = on_connect

    mqtt_client.connect("10.25.0.2", 1883, 60)

    try:
        mqtt_client.loop_forever()
    except KeyboardInterrupt:
        print("exiting ...")