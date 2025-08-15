import rospy
from geometry_msgs.msg import Pose2D
from std_msgs.msg import UInt64
from robot_v2.msg import Battery
from std_msgs.msg import String
from robot_v2.msg import Goal
import time


def goal_callback(msg: Goal):
    print(f"receive goal {msg}")
    time.sleep(3)
    publish_arrived()

def return_callback(msg: String):
    print(f"receive return signal {msg}")
    time.sleep(3)
    publish_canReplan()


def publish_arrived():
    arrived_publisher.publish("ARRIVED")
    print("robot arrived")
    time.sleep(3)

def publish_canReplan():
    canReplan_publisher.publish("CAN_REPLAN")
    print("robot can do replan")

def publish_pose():
    pose = Pose2D()
    pose.x = 1.1111902
    pose.y = 0.9999812
    pose.theta = -3.7878783
    pose_publisher.publish(pose)
    print(f"publish pose message {pose}")


def publish_battery():
    battery = Battery()
    battery.batteryPercentage = 29
    battery_publisher.publish(battery)
    print(f"publish battery info {battery}")


def publish_fault():
    fault = UInt64()
    fault.data = 1020304050607089
    fault_publisher.publish(fault)
    print(f"publish fault message {fault}")

if __name__ == "__main__":
    rospy.init_node('mock_rosNode', anonymous=True)

    rospy.Subscriber("goal", Goal, goal_callback, queue_size=1)
    rospy.Subscriber("signal/return", String, return_callback, queue_size=1)
    pose_publisher = rospy.Publisher("/movebase_pose2d", Pose2D, queue_size=1)
    battery_publisher = rospy.Publisher("/battery", Battery, queue_size=1)
    fault_publisher = rospy.Publisher("/status_code", UInt64, queue_size=1)
    
    arrived_publisher = rospy.Publisher("/signal/arrived", String, queue_size=1)
    canReplan_publisher = rospy.Publisher("signal/canReplan", String, queue_size=1)
    #每两秒执行一次
    rate = rospy.Rate(0.1)
    while not rospy.is_shutdown():
        publish_pose()
        publish_battery()
        publish_fault()
        rate.sleep()    
    
    rospy.spin()