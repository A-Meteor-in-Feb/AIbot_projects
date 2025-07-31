import rospy
import json
import tf
from nav_msgs.msg import Odometry
from std_msgs.msg import String
from robot.msg import Pub
from robot.msg import Sub


def subscribe_callback(msg):
    x = msg.x
    y = msg.y
    heading = msg.heading
    floor_id = msg.floor_id
    user_id = msg.user_id

    print("SUbscribe the message x: {x}, y: {y}, heading: {heading}, floor_id: {floor_id}, user_id: {user_id}")
    pub.publish(1.1, 2.2, 3.3, "floor_id", "status")


if __name__ == "__main__":
    rospy.init_node("ros2mqtt_bridge", anonymous=True)
    rospy.Subscriber("localization_from_backend", Sub, subscribe_callback)
    pub = rospy.Publisher("localization_to_backend", Pub, queue_size=1)
    rate = rospy.Rate(5)
    rospy.spin()
    rate.sleep()