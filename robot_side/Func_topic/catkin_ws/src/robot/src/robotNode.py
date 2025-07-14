#!/usr/bin/env python3
import paho.mqtt.client as mqtt
import rospy
import json
from std_msgs.msg import String

def on_connect(client, userdata, flags, reason_code, properties):
    #rospy.loginfo(f"Connected with the result code {reason_code}")
    print(f"Connected with the result code {reason_code}")

def ros_callback(msg):
    payload = json.dumps({
        "ros_topic": msg._connection_header['topic'],
        "data": msg.data,
        "stamp": rospy.get_time()
    })
    mqtt_client.publish(topic="test/topic", payload=payload, qos=1)
    rospy.loginfo(f"Forwarded to MQTT: {payload}")

if __name__ == "__main__":

    rospy.init_node('ros2mqtt_bridge', anonymous=True)

    mqtt_client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id="bridge")
    mqtt_client.on_connect = on_connect
    mqtt_client.connect(host="127.0.01.1", port=1883, keepalive=60)
    mqtt_client.loop_start()

    rospy.Subscriber("test/topic", String, ros_callback)

    rospy.spin()

    mqtt_client.loop_stop()
    mqtt_client.disconnect()