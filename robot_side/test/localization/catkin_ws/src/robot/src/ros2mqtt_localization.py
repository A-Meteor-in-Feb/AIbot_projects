import rospy
import json
import tf
from nav_msgs.msg import Odometry
from std_msgs.msg import String
import paho.mqtt.client as mqtt
from robot.msg import Sub
from robot.msg import Pub

BROKER_HOST = "10.25.0.3"
BROKER_PORT = 1883

ORG_ID = "AIbot"

DEVICE_TYPE = "robot"
ROBOT_ID = "R1234"

CLIENT_ID = f"d:{ORG_ID}:{DEVICE_TYPE}:{ROBOT_ID}"


def on_connect(client, userdata, flags, reason_code, properties):
    """
        connect callback
    """
    print(f"Connected with the result code {reason_code}")
    client.subscribe("localization_from_backend")
    client.message_callback_add("localization_from_backend", subscribe_handler)


def subscribe_handler(client, userdate, msg):
    sub_topic = Sub()

    data = json.loads(msg.payload.decode('utf-8'))

    sub_topic.x = data['x']
    sub_topic.y = data['y']
    sub_topic.heading = data['heading']
    sub_topic.floor_id = data['floor_id']
    sub_topic.user_id = data['user_id']

    ros2ros_pub.publish(sub_topic)


def publish_callback(msg):

    payload = {
        "x": msg.x,
        "y": msg.y,
        "heading": msg.heading,
        "floor_id": msg.floor_id,
        "status": msg.status
    }

    message = json.dumps(payload)
    
    mqtt_client.publish(f"localization_to_backend", message, qos=0)

    rospy.loginfo(f"Forwarded state topic to MQTT: {payload}")
    

if __name__ == "__main__":
    rospy.init_node("ros2mqtt_bridge", anonymous=True)
    rospy.Subscriber("localization_to_backend", Pub, publish_callback)
    ros2ros_pub = rospy.Publisher("localization_from_backend", Sub, queue_size=1)

    mqtt_client = mqtt.Client(client_id=CLIENT_ID, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    mqtt_client.on_connect = on_connect

    mqtt_client.connect(host=BROKER_HOST, port=BROKER_PORT, keepalive=60)
    mqtt_client.loop_start()

    rospy.spin()
    mqtt_client.loop_stop()
    mqtt_client.disconnect()