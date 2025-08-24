import rospy
from geometry_msgs.msg import Pose2D
from std_msgs.msg import UInt64
from robot_v3.msg import Battery
from robot_v3.msg import Position
import dataInfo
from std_msgs.msg import String
from nav_msgs.msg import Odometry
from tf.transformations import euler_from_quaternion
from std_msgs.msg import Int32

class RosSub:
    def __init__(self, state: dataInfo.StateInfo):
        """
        这个类用与订阅各种来自不同子系统的ROS话题.
        参数:
            state: 对象实例, 方便相应属性更新.
        """
        #机器人基础状态 - 位置、电量、异常码 需要的话题
        self.topic_localization = "/global_localization" 
        self.topic_battery = "/battery"
        self.topic_statusCode = "/status_code"

        #跟tianxin交互需要用到的话题
        self.topic_signal = "/signal"
        self.topic_position = "/position" #TODO
        self.topic_step = "/step" #TODO

        #话题订阅
        self.sub_localization = rospy.Subscriber(self.topic_localization, Odometry, self.callback_localization, queue_size=1, tcp_nodelay=True)
        self.sub_battery = rospy.Subscriber(self.topic_battery, Battery, self.callback_battery, queue_size=1, tcp_nodelay=True)
        self.sub_statusCode = rospy.Subscriber(self.topic_statusCode, UInt64, self.callback_statusCode, queue_size=1, tcp_nodelay=True)
        
        #跟tianxin交互需要用到的话题
        self.sub_signal = rospy.Subscriber(self.topic_signal, String, self.callback_signal, queue_size=1, tcp_nodelay=True)
        self.sub_position = rospy.Subscriber(self.topic_position, Position, self.callback_position, queue_size=1, tcp_nodelay=True)
        self.sub_step = rospy.Subscriber(self.topic_step, Int32, self.callback_step, queue_size=1, tcp_nodelay=True)

        self.state = state

    def callback_localization(self, msg: Odometry):
        """
        For 实时或者定时更新机器人的地理位置.
        参数:
            msg: Odometry, 由localization部分发送过来
        """
        q = msg.pose.pose.orientation
        quat = [q.x, q.y, q.z, q.w]

        roll, pitch, yaw = euler_from_quaternion(quat)

        self.state.update_localization(msg.pose.pose.position.x, msg.pose.pose.position.y, yaw)

    
    def callback_position(self, msg: Position):
        """
        接收机器人所在的楼层和楼
        参数:
            msg: Position, 由 floor 和 building 组成
        """
        floor = msg.floor
        building = msg.building

        self.state.update_position(floor=floor, building=building)


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
        
        code = int(msg.data)
        if code == 1:
            self.state.update_fault(False)
        else:
            self.state.update_fault(True)
        """

    def callback_signal(self, msg: String):
        """
        订阅 signal 话题, 然后修改机器人相应的状态
        参数:
            msg: String, 一个字符串代表机器人的状态
            PLANNING_COMPLETE
        """
        signal = msg.data
        taskStatus = self.state.get_state().get("taskStatus")
        # tianxin 发规划完成, 
        if signal == "PLANNING_COMPLETE":
            # 如果机器人原来为idle, 则这里把机器人状态更新为delivering
            if taskStatus == "idle":
                self.state.update_taskStatus("delivering")
            # 其他任何状态, 只有两种情况 1-任务取消返回; 2-任务完成返回
            else:
                self.state.update_taskStatus("returning")
        # tianxin 到达目标地址
        if signal == "GOAL_ARRIVED":
            # 如果之前机器人状态为 returning, 则这里把机器人状态更新为 idle
            if taskStatus == "returning":
                self.state.update_taskStatus("idle")
            # 如果之前机器人状态为 delivering, 则这里把机器人状态更新为 arrived
            else:
                self.state.update_taskStatus("arrived")
        # tianxin 回到原点/起点
        #if signal == "RETURN_COMPLETE":
            #self.state.update_taskStatus("idle")
            #self.state.update_taskId(0)

    def callback_step(self, msg: Int32):
        """
        订阅step话题, 按需要给后台发交互电梯信号
        参数:
            msg: Int32 代表机器人执行步骤
        """
        step = msg.data
        if step == 1:
            self.state.update_step(step=1)
        elif step == 2:
            self.state.update_step(step=2)
        else:
            rospy.loginfo("Invalide step number")