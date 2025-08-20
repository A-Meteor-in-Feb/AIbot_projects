import rospy
from std_msgs.msg import String
from robot_v3.msg import Goal
import time


def goal_callback(msg: Goal):
    print(f"receive goal {msg}")
    time.sleep(10)
    publish_signal("PLANNING_COMPLETE")
    print("PLANNING_COMPLETE")
    time.sleep(10)
    publish_signal("GOAL_ARRIVED")
    print("ARRIVED")

'''
def return_callback(msg: String):
    print(f"receive return signal {msg}")
    time.sleep(10)
    publish_signal("RETURN_COMPLETE")
'''

def publish_signal(signal):
    signal_publisher.publish(signal)


if __name__ == "__main__":
    rospy.init_node('mock_rosNode', anonymous=True)

    rospy.Subscriber("goal", Goal, goal_callback, queue_size=1)
    #rospy.Subscriber("signal/return", String, return_callback, queue_size=1)
    
    signal_publisher = rospy.Publisher("signal", String, queue_size=1)  
    
    rospy.spin()