import rospy
from geometry_msgs.msg import Pose2D
from std_msgs.msg import UInt64
from woosh_msgs.msg import Battery
import dataInfo

class RosStateSub:
    def __init__(self, state: dataInfo.StateInfo):
        self.topic_pose2d = "/movebase_pose2d"
        self.topic_battery = "/battery"
        self.topic_status = "/status_code"

        self.sub_pose2d = rospy.Subscriber(self.topic_pose2d, Pose2D, self.callback_pose2d, queue_size=5, tcp_nodelay=True)
        self.sub_battery = rospy.Subscriber(self.topic_battery, Battery, self.callback_battery, queue_size=5, tcp_nodelay=True)
        self.sub_status = rospy.Subscriber(self.topic_status, UInt64, self.callback_status, queue_size=5, tcp_nodelay=True)
        
        self.state = state

    def callback_pose2d(self, msg: Pose2D):
        self.state.update_position(msg.x, msg.y, msg.theta)

    def callback_battery(self, msg: Battery):
        self.state.update_battery(int(msg.batteryPercentage))

    def callback_status(self, msg: UInt64):
        code = int(msg.data)
        if code == 1:
            self.state.update_fault(False)
        else:
            self.state.update_fault(True)

    
# 这里可能还需要再订阅一个话题 from tianxin, 用来接收小车是否到达目的地的信号
# 然后你可以通过这个信号来修改状态 为 arrived (from delivering to arrived)
# 再订阅一个话题 from tianxin, 用来接收小车是否返回可以可以进行下一轮配送的路径规划的点位
# 然后你可以通过这个信号来修改状态 为 idle (from delivered/ delivery_failed to idle)