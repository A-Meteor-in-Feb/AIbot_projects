import json
import time
import paho.mqtt.client as mqtt

BROKER_HOST = "10.25.0.3"
BROKER_PORT = 1883

TOPIC = "mqtt_backend/goal"


def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected with the reason code {reason_code}")


def publish_goal(x, y, yaw, frame_id='map'):
    payload = {
        'frame_id': frame_id,
        'x': x,
        'y': y,
        'yaw': yaw
    }
    payload = json.dumps(payload)
    print(f"publish {payload}")
    mqtt_client.publish(topic=TOPIC, payload=payload)


if __name__ == "__main__":

    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="backend")

    mqtt_client.on_connect = on_connect

    mqtt_client.connect(host=BROKER_HOST, port=BROKER_PORT, keepalive=60)
    
    try: 
        mqtt_client.loop_start()
        while True:
            publish_goal(1,2,3)
            time.sleep(1)
    except KeyboardInterrupt:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        print("exiting......")