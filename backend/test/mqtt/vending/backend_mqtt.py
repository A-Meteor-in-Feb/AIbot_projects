import json
import paho.mqtt.client as mqtt

BROKER_HOST = "10.25.0.3"
BROKER_PORT = 1883
CLIENT_ID = "backend"


def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected with the reason code {reason_code}")
    client.subscribe("vending/server")
    client.message_callback_add("vending/server", subscribe_server_topic_handler)
    print("Subscribe to the topic - vending/server")


def on_disconnect(client, userdata, reason_code):
    print(f"Disconnect with reason code {reason_code}, reconnecting ...")
    client.reconnect()


def subscribe_server_topic_handler(client, userdata, msg):
    msg = json.loads(msg.payload.decode())
    cmd = msg.get("cmd")
    data = msg.get("data")
    if(cmd == "shipment"):
        #execute something then get the result back
        #then publish the response topic
        data["r"] = 0
    else:
        #execute something then get the result back
        #then publish the response topic
        data["r"] = 0
    
    
    
    payload = json.dumps(msg)
    mqtt_client.publish("vending/client", payload=payload)

if __name__ == "__main__":
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=CLIENT_ID)

    mqtt_client.on_connect = on_connect
    mqtt_client.on_disconnect = on_disconnect

    mqtt_client.connect(host=BROKER_HOST, port=BROKER_PORT, keepalive=60)

    try: 
        mqtt_client.loop_forever()
    except KeyboardInterrupt:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        print("exiting......")
