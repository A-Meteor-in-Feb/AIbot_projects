import paho.mqtt.client as mqtt
import time

def on_publish(client, userdata, mid, reason_code, properties):
    try:
        userdata.remove(mid)
    except KeyError:
        print("on_publish() is called with a mid not present in unacked_publish")

mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="test_publisher")

unacked_publish = set()

mqtt_client.on_publish = on_publish

mqtt_client.user_data_set(unacked_publish)

# keepalive is the maximum period (s) between communications with the broker, may need chage
mqtt_client.connect("127.0.0.1", port=1883, keepalive=60)

mqtt_client.loop_start()

msg_info1 = mqtt_client.publish("test/topic", "testing", qos=1)
unacked_publish.add(msg_info1.mid)

msg_info2 = mqtt_client.publish("test/topic", "testing again", qos=1)
unacked_publish.add(msg_info2)

while len(unacked_publish):
    time.sleep(5)

msg_info1.wait_for_publish()
msg_info2.wait_for_publish()

mqtt_client.disconnect()
mqtt_client.loop_stop()
