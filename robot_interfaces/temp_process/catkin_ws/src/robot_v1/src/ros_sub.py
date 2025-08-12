import rospy
import time
from threading import Lock
import copy
from geometry_msgs.msg import Pose2D
from std_msgs.msg import UInt64

from woosh_msgs.msg import Battery

class RobotStateSubscriber:
    def __init__(self):
        self.topic_pose2d = rospy.get_param("~topic_pose2d", "/movebase_pose2d")
        self.topic_battery = rospy.get_param("~topic_battery", "/battery")
        self.topic_status = rospy.get_param("~topic_status", "/status_code")

        self.lock = Lock()

        self.state = {
            "position": {"x": None, "y": None, "theta": None},
            "battery": None,
            "fault": None
        }

        self.sub_pose2d = rospy.Subscriber(self.topic_pose2d, Pose2D, self.callback_pose2d, queue_size = 5, tcp_nodelay = True)
        self.sub_battery = rospy.Subscriber(self.topic_battery, Battery, self.callback_battery, queue_size = 5, tcp_nodelay = True)
        self.sub_status = rospy.Subscriber(self.topic_status, UInt64, self.callback_status, queue_size = 5, tcp_nodelay = True)

        print("subscriber starts working")

    def callback_pose2d(self, msg: Pose2D):
        with self.lock:
            self.state["position"].update({
                "x": msg.x,
                "y": msg.y,
                "theta": msg.theta 
            })
    
    def callback_battery(self, msg: Battery):
        with self.lock:
            self.state["battery"] = int(msg.batteryPercentage)
    
    def callback_status(self, msg:UInt64):
        code = int(msg.data)
        if code == 1234: # 应该是某个正数值代表没有错误之类的吧
            with self.lock:
                self.state["fault"] = False
        else:
            with self.lock:
                self.state["fault"] =True

    def get_robot_state(self):
        with self.lock:
            return copy.deepcopy(self.state)