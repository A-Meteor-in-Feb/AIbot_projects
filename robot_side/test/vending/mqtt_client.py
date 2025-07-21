import json
import paho.mqtt.client as mqtt
import time
BROKER_HOST = "10.25.0.3"
BROKER_PORT = 1883
CLIENT_ID = "robot"

USERNAME = "vending"
PASSWORD = "administrator"


def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected with the reason code {reason_code}")
    client.subscribe("vending/client")
    client.message_callback_add("vending/client", subscribe_client_topic_handler)
    print("Subscribe to the topic - vending/client")


def on_publish(client, userdata, mid):
    print(f"message {mid} published.")


def publish_server_topic(cmd, parameters):
    topic = "vending/server"
    payload = {
        "msg": 101,
        "sn" : "SN25063001",
        "cmd": cmd,
        "data": parameters
    }
    
    payload = json.dumps(payload)

    mqtt_client.publish("vending/server", payload=payload)


def subscribe_client_topic_handler(client, userdata, msg):
    msg = json.loads(msg.payload.decode())
    print(f"Receive response from backend: {msg}")


if __name__ == "__main__":
    mqtt_client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id=CLIENT_ID)

    #authentication
    #mqtt_client.username_pw_set(username=USERNAME, PASSWORD=PASSWORD)
    
    mqtt_client.on_connect = on_connect

    mqtt_client.connect(host=BROKER_HOST, port=BROKER_PORT, keepalive=60)

    try:
        mqtt_client.loop_start()
        while True:
            publish_server_topic("shipment", {"n": "1001"})
            publish_server_topic("barcode", {"c": "sdfasdfqwerqefasdfqwerqwerasdf"})
            time.sleep(5)
    except KeyboardInterrupt:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        print("exiting .....")