import rospy
from geometry_msgs.msg import PoseStamped
from tf.transformations import quaternion_from_euler


def goal_callback(msg):
    
    print("Receive the navigation goal data:", msg)

if __name__ == "__main__":
    rospy.init_node('ros2mqtt_bridge', anonymous=True)

    rospy.Subscriber("move_base_simple/goal", PoseStamped, goal_callback)

    rospy.spin()