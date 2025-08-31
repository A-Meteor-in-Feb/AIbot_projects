import rospy
from std_msgs.msg import String
from robot_v3.msg import Goal_v3
import time

from std_msgs.msg import Int32


def goal_callback(msg: Goal_v3):
    if msg.relocation:
        print(f"receive goal {msg}")
        time.sleep(1)
        publish_signal("RELOCATION_RECEIVED")
        print("RELOCATION_RECEIVED\n")
        time.sleep(10)
        publish_signal("RELOCATION_COMPLETE") #"RELOCATION_FAILURE"
        print("RELOCATION_COMPLETE\n")
    else:
        print(f"receive goal {msg}")
        time.sleep(1)
        publish_signal("GOAL_RECEIVED")
        print("GOAL_RECEIVED\n")
        time.sleep(10)
        publish_signal("GOAL_ARRIVED")
        print("GOAL_ARRIVED\n")

'''
def return_callback(msg: String):
    print(f"receive return signal {msg}")
    time.sleep(10)
    publish_signal("RETURN_COMPLETE")
'''

def publish_signal(signal):
    signal_publisher.publish(signal)

def publish_step(step):
    """
    参数为一个数字
    step = 1 : 机器人到达电梯门口要坐电梯 --- u/d
    step = 2 : 机器人进入电梯内部要开始坐电梯. --- 目标楼层
    """
    step_publisher.publish(step)

if __name__ == "__main__":
    rospy.init_node('mock_rosNode', anonymous=True)

    rospy.Subscriber("/goal_v3", Goal_v3, goal_callback, queue_size=1)
    #rospy.Subscriber("signal/return", String, return_callback, queue_size=1)
    
    signal_publisher = rospy.Publisher("signal", String, queue_size=1)  
    step_publisher = rospy.Publisher("step", Int32, queue_size=1)
    
    rospy.spin()