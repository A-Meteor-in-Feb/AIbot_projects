import rospy
from geometry_msgs.msg import Pose2D
from std_msgs.msg import UInt64
from robot_v3.msg import Battery
import dataInfo
from std_msgs.msg import String

class RosSub:
    def __init__(self, state: dataInfo.StateInfo):
        """
        这个类用与订阅各种来自不同子系统的ROS话题.
        参数:
            state: 对象实例, 方便相应属性更新.
        """
        #机器人基础状态 - 位置、电量、异常码 需要的话题
        self.topic_pose2d = "/moverbase_pose2d" #这个之后需要换成jianyu的发布的数据话题
        self.topic_battery = "/battery"
        self.topic_statusCode = "/status_code"

        #跟tianxin交互需要用到的话题
        self.topic_signal = "signal"

        #话题订阅
        self.sub_pose2d = rospy.Subscriber(self.topic_pose2d, Pose2D, self.callback_pose2d, queue_size=1, tcp_nodelay=True)
        self.sub_battery = rospy.Subscriber(self.topic_battery, Battery, self.callback_battery, queue_size=1, tcp_nodelay=True)
        self.sub_statusCode = rospy.Subscriber(self.topic_statusCode, UInt64, self.callback_statusCode, queue_size=1, tcp_nodelay=True)
        self.sub_signal = rospy.Subscriber(self.topic_signal, String, self.callback_signal, queue_size=1, tcp_nodelay=True)
        
        self.state = state

    def callback_pose2d(self, msg: Pose2D):
        """
        For 实时或者定时更新机器人的地理位置.
        参数:
            msg: Pose2D, 由localization部分发送过来
        """
        self.state.update_position(msg.x, msg.y, msg.theta)

    def callback_battery(self, msg: Battery):
        """
        For 实时更新机器人的电池电量.
        参数:
            msg: Battery, 由机器人底盘发布的电量信息
        """
        self.state.update_battery(int(msg.batteryPercentage))

    def callback_statusCode(self, msg: UInt64):
        """
        For 实时获取异常码 published by 机器人底盘
        参数:
            msg: UIn64 一个112位数字, 代表机器人是否发生故障
        TODO 但其实我觉得故障来源不止这里, 而且不一定机器人底盘现在是可以被正常使用的状态
        TODO 而且有很多异常码, 也有很多正常码, 我觉得判断的逻辑是不是需要改一改或者怎么样之类的
        """
        code = int(msg.data)
        if code == 1:
            self.state.update_fault(False)
        else:
            self.state.update_fault(True)

    def callback_signal(self, msg: String):
        """
        订阅 signal 话题, 然后修改机器人相应的状态
        参数:
            msg: String, 一个字符串代表机器人的状态
            PLANNING_COMPLETE
        """
        signal = msg.data
        # tianxin 发规划完成, 我这里把机器人状态更新为delivering
        if signal == "PLANNING_COMPLETE":
            self.state.update_taskStatus("delivering")
        # tianxin 到达目标地址, 我这里把机器人状态更新为 arrived
        if signal == "GOAL_ARRIVED":
            self.state.update_taskStatus("arrived")
        # tianxin 回到原点/起点
        if signal == "RETURN_COMPLETE":
            self.state.update_taskStatus("idle")
            self.state.update_taskId(0)