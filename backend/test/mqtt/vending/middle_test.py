import json
import paho.mqtt.client as mqtt
import time

BROKER_HOST_VPN = "10.25.0.3"
BROKER_PORT_VPN = 1883
BROKER_HOST_5G = "192.168.1.2"
BROKER_PORT_5G = 1883
CLIENT_ID_VPN = "middle_point_vpn"
CLIENT_ID_5G = "middle_point_5g"

COUNT = 0

def on_connect_vpn(client, userdata, flags, reason_code, properties):
    print(f"{CLIENT_ID_VPN} connected with the reason code {reason_code}")
    client.subscribe("vending/client")
    client.message_callback_add("vending/client", subscribe_client_topic_handler)
    print(f"{CLIENT_ID_VPN} subscribe to the topic - vending/client\n\n")


def on_connect_5g(client, userdata, flags, reason_code, properties):
    print(f"{CLIENT_ID_5G} connected with the reason code {reason_code}")
    client.subscribe("vending/server")
    client.message_callback_add("vending/server", subscribe_server_topic_handler)
    print(f"{CLIENT_ID_5G} subscribe to the topic - vending/server\n\n")


def subscribe_client_topic_handler(client, userdata, msg):
    msg_dict = json.loads(msg.payload.decode())
    print(f"Receive vending/client from backend: \n {msg_dict}\n")
    payload = json.dumps(msg_dict)
    mqtt_client_5g.publish("vending/client", payload=payload)
    print(f"Forward vending/client to the board: \n {msg_dict}\n\n")

def subscribe_server_topic_handler(client, userdata, msg):
    msg_dict = json.loads(msg.payload.decode())
    print(f"Receive vending/server from board: \n {msg_dict}\n\n")
    payload = json.dumps(msg_dict)
    mqtt_client_vpn.publish("vending/server", payload=payload)
    print(f"Forward vending/client to the board: \n {msg_dict}\n\n")


if __name__ == "__main__":
    mqtt_client_vpn = mqtt.Client(client_id=CLIENT_ID_VPN, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    mqtt_client_5g = mqtt.Client(client_id=CLIENT_ID_5G, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    
    #authentication
    #mqtt_client.username_pw_set(username=USERNAME, PASSWORD=PASSWORD)
    
    mqtt_client_vpn.on_connect = on_connect_vpn
    mqtt_client_5g.on_connect = on_connect_5g

    mqtt_client_vpn.connect(host=BROKER_HOST_VPN, port=BROKER_PORT_VPN, keepalive=60)
    mqtt_client_5g.connect(host=BROKER_HOST_5G, port=BROKER_PORT_5G, keepalive=60)

    mqtt_client_5g.loop_start()
    mqtt_client_vpn.loop_start()
    

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        mqtt_client_vpn.loop_stop()
        mqtt_client_5g.loop_stop()
        mqtt_client_vpn.disconnect()
        mqtt_client_5g.disconnect()
        print("exiting .....")