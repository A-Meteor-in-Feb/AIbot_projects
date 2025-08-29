import rospy
from nav_msgs.msg import Odometry
from tf.transformations import euler_from_quaternion

def odom_cb(msg):
    # 四元数
    q = msg.pose.pose.orientation
    quat = [q.x, q.y, q.z, q.w]

    # 转欧拉角 (roll, pitch, yaw)
    roll, pitch, yaw = euler_from_quaternion(quat)

    print(msg.pose.pose.position.x, msg.pose.pose.position.y, yaw)


def battery(msg):
    print(msg)

rospy.init_node("odom_angle_listener")
#rospy.Subscriber("/odom", Odometry, odom_cb)
rospy.Subscriber("")
rospy.spin()
