import json
import paho.mqtt.client as mqtt

BROKER_HOST = "192.168.123.62"
BROKER_PORT = 1883
CLIENT_ID = "backend"


def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected with the reason code {reason_code}")
    client.subscribe("vending/server")
    client.message_callback_add("vending/server", subscribe_server_topic_handler)
    client.publish("vending/client", payload=json.dumps("hi"))
    print("Subscribe to the topic - vending/server")


def on_disconnect(client, userdata, reason_code):
    print(f"Disconnect with reason code {reason_code}, reconnecting ...")
    client.reconnect()


def subscribe_server_topic_handler(client, userdata, msg):
    msg = json.loads(msg.payload.decode())
    print(f"receive {msg}")
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
    mqtt_client.publish("vending/server", payload=payload)

if __name__ == "__main__":
    print(1)
    mqtt_client = mqtt.Client(client_id=CLIENT_ID, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)

    mqtt_client.on_connect = on_connect
    #mqtt_client.on_disconnect = on_disconnect

    mqtt_client.connect(host=BROKER_HOST, port=BROKER_PORT, keepalive=60)

    try: 
        mqtt_client.loop_forever()
    except KeyboardInterrupt:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        print("exiting......")


'''
password_file /etc/mosquitto/passwords

listener 8445
cafile /home/avnuc/yangtianjiao/AIbot_projects/mqtt_certs/ca.crt
certfile /home/avnuc/yangtianjiao/AIbot_projects/mqtt_certs/server.crt
keyfile /home/avnuc/yangtianjiao/AIbot_projects/mqtt_certs/server.key

'''
