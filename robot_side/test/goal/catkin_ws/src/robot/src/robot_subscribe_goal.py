#!/usr/bin/env python

import rospy
import json
import paho.mqtt.client as mqtt
from geometry_msgs.msg import PoseStamped
from tf.transformations import quaternion_from_euler


BROKER_HOST = "10.25.0.3"
BROKER_PORT = 1883

TOPIC = "goal"


def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected with reason code={reason_code}")
    client.subscribe(TOPIC)
    client.message_callback_add(TOPIC, goal_handler)
    print("subscribe to topic - goal")


def goal_handler(client, userdata, msg):
    data = json.loads(msg.payload.decode('utf-8'))
    print(f"receive data {data}", flush=True)

    ps = PoseStamped()
    ps.header.stamp = rospy.Time.now()
    ps.header.frame_id = data.get('frame_id', 'map')
    ps.pose.position.x = data['x']
    ps.pose.position.y = data['y']
    ps.pose.position.z = data.get('z', 0.0)
        
    q = quaternion_from_euler(0.0, 0.0, data['yaw'])
    ps.pose.orientation.x = q[0]
    ps.pose.orientation.y = q[1]
    ps.pose.orientation.z = q[2]
    ps.pose.orientation.w = q[3]
        
    pub.publish(ps)
    
    print("Published PoseStamped goal to move_base_simple/goal")


if __name__ == '__main__':
    rospy.init_node('mqtt_goal_listener')
    pub = rospy.Publisher('move_base_simple/goal', PoseStamped, queue_size=1)

    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="robot")
    mqtt_client.on_connect = on_connect
    mqtt_client.connect(host=BROKER_HOST, port=BROKER_PORT, keepalive=60)

   
    mqtt_client.loop_start()
    rospy.spin()
    mqtt_client.loop_stop()
    mqtt_client.disconnect()