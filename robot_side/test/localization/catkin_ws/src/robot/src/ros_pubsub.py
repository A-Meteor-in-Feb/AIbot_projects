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


'''
    x, y, heading = msg.data

    odom = Odometry()
    # 时间戳与坐标系
    odom.header.stamp = rospy.Time.now()
    odom.header.frame_id = "map"         # 全局坐标系
    odom.child_frame_id = "base_link"    # 机器人自身坐标系

    # 填写位置
    odom.pose.pose.position.x = x
    odom.pose.pose.position.y = y
    odom.pose.pose.position.z = 0.0

    # heading 转成四元数
    quat = tf.transformations.quaternion_from_euler(
        0.0,    # roll
        0.0,    # pitch
        heading # yaw
    )
    odom.pose.pose.orientation.x = quat[0]
    odom.pose.pose.orientation.y = quat[1]
    odom.pose.pose.orientation.z = quat[2]
    odom.pose.pose.orientation.w = quat[3]

    # 可选：填写速度为 0
    odom.twist.twist.linear.x  = 0.0
    odom.twist.twist.linear.y  = 0.0
    odom.twist.twist.angular.z = 0.0

    odom_pub.publish(odom)
    rospy.logdebug(f"Published Odometry: x={x:.2f}, y={y:.2f}, heading={heading:.2f}")

    # 发布 Odometry
    # odom_pub = rospy.Publisher("odom_converted", Odometry, queue_size=1)

'''