import json
import paho.mqtt.client as mqtt
import time

BROKER_HOST = "10.25.0.3"
BROKER_PORT = 1883

def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected with the reason code {reason_code}")
    client.subscribe("localization_to_backend")
    client.message_callback_add("localization_to_backend", client_subscribe_handler)


def client_subscribe_handler(client, userdata, msg):
    data = json.loads(msg.payload.decode('utf-8'))
    x = data['x']
    y = data['y']
    heading = data['heading']
    floor_id = data['floor_id']
    status = data['status']

    print("Receive the data from robot, x: {x}, y: {y}, heading: {heading}, floor_id: {floor_id}, status: {status}")

def publish_goal(x, y, heading, floor_id, user_id):
    payload = {
        'x': x,
        'y': y,
        'heading': heading,
        'floor_id': floor_id,
        'user_id': user_id
    }
    payload = json.dumps(payload)
    print(f"publish {payload}")
    mqtt_client.publish(topic="localization_from_backend", payload=payload)


if __name__ == "__main__":

    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="backend")

    mqtt_client.on_connect = on_connect

    mqtt_client.connect(host=BROKER_HOST, port=BROKER_PORT, keepalive=60)
    
    try: 
        mqtt_client.loop_start()
        while True:
            publish_goal(1,2,3, "floor_id", "user_id")
            time.sleep(5)
    except KeyboardInterrupt:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        print("exiting......")