import rospy
from std_msgs.msg import String
from robot_v3.msg import Goal_v3
import time


def goal_callback(msg: Goal_v3):
    if msg.relocation:
        print(f"receive goal {msg}")
        time.sleep(1)
        publish_signal("RELOCATION_RECEIVED")
        print("RELOCATION_RECEIVED\n")
        time.sleep(8)
        publish_signal("RELOCATION_COMPLETE") #"RELOCATION_FAILURE"
        print("RELOCATION_COMPLETE\n")
    else:
        print(f"receive goal {msg}")
        time.sleep(1)
        publish_signal("GOAL_RECEIVED")
        print("GOAL_RECEIVED\n")
        time.sleep(1)
        publish_signal("GOAL_ARRIVED")
        print("GOAL_ARRIVED\n")


def publish_signal(signal):
    signal_publisher.publish(signal)


if __name__ == "__main__":
    rospy.init_node('mock_rosNode', anonymous=True)

    rospy.Subscriber("goal_v3", Goal_v3, goal_callback, queue_size=1)
    
    signal_publisher = rospy.Publisher("signal", String, queue_size=1)  
    
    rospy.spin()