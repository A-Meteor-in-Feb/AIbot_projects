import json
import paho.mqtt.client as mqtt
import time

BROKER_HOST = "10.25.0.3"
BROKER_PORT = 1883
CLIENT_ID = "backend"

COUNT = 0

def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected with the reason code {reason_code}")
    client.subscribe("vending/server")
    client.message_callback_add("vending/server", subscribe_client_topic_handler)
    print("Subscribe to the topic - vending/server\n\n")



def publish_topic(cmd, parameters):
    global COUNT
    COUNT += 1
    print(f"num.{COUNT}")
    topic = "vending/client"
    payload = {
        "msg": 101,
        "sn" : "SN25063001",
        "cmd": cmd,
        "data": parameters
    }
    
    payload = json.dumps(payload)

    mqtt_client.publish("vending/client", payload=payload)

    print(f"publish topic vending/client to the board\n {payload}\n\n")


def subscribe_client_topic_handler(client, userdata, msg):
    msg = json.loads(msg.payload.decode())
    print(f"Receive response vending/server from board: \n {msg}\n\n")


if __name__ == "__main__":
    mqtt_client = mqtt.Client(client_id=CLIENT_ID, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)

    #authentication
    #mqtt_client.username_pw_set(username=USERNAME, PASSWORD=PASSWORD)
    
    mqtt_client.on_connect = on_connect

    mqtt_client.connect(host=BROKER_HOST, port=BROKER_PORT, keepalive=60)

    mqtt_client.loop_start()
    try:
        
        while True:
            publish_topic("shipment", {"n": "1001"})
            time.sleep(5)
    except KeyboardInterrupt:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        print("exiting .....")