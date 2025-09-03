import rospy
from geometry_msgs.msg import Pose2D
from std_msgs.msg import UInt64
from robot_v3.msg import Battery
from robot_v3.msg import Position
from robot_v5 import dataInfo
from std_msgs.msg import String
from nav_msgs.msg import Odometry
from tf.transformations import euler_from_quaternion
from std_msgs.msg import Int32

class RosSub:
    def __init__(self, robotState: dataInfo.RobotStateInfo, programStatus: dataInfo.ProgramStatus):
        """
        这个类用与订阅各种来自不同子系统的ROS话题.
        参数:
            robotState: 对象实例, 方便相应属性更新.
        """
        self.robotState = robotState
        self.programStatus = programStatus

        #机器人基础状态 - 位置、电量、异常码 需要的话题
        self.topic_localization = "/global_localization" 
        self.topic_battery = "/battery"
        self.topic_statusCode = "/status_code"

        #跟tianxin交互需要用到的话题
        self.topic_signal = "/signal"

        #话题订阅
        self.sub_localization = rospy.Subscriber(self.topic_localization, Odometry, self.callback_localization, queue_size=1, tcp_nodelay=True)
        self.sub_battery = rospy.Subscriber(self.topic_battery, Battery, self.callback_battery, queue_size=1, tcp_nodelay=True)
        self.sub_statusCode = rospy.Subscriber(self.topic_statusCode, UInt64, self.callback_statusCode, queue_size=1, tcp_nodelay=True)
        
        #跟tianxin交互需要用到的话题
        self.sub_signal = rospy.Subscriber(self.topic_signal, String, self.callback_signal, queue_size=1, tcp_nodelay=True)

    def callback_localization(self, msg: Odometry):
        """
        For 实时或者定时更新机器人的地理位置.
        参数:
            msg: Odometry, 由localization部分发送过来
        """
        q = msg.pose.pose.orientation
        quat = [q.x, q.y, q.z, q.w]

        roll, pitch, yaw = euler_from_quaternion(quat)

        self.robotState.update_localization(msg.pose.pose.position.x, msg.pose.pose.position.y, yaw)

    def callback_battery(self, msg: Battery):
        """
        For 实时更新机器人的电池电量.
        参数:
            msg: Battery, 由机器人底盘发布的电量信息
        """
        self.robotState.update_battery(int(msg.batteryPercentage))

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
        robotStatus = self.robotState.get_state().get("robotStatus")
        programStatus = self.programStatus.get_programStatus()

        if signal == "GOAL_RECEIVED":
            if programStatus == "to_lift_outside" or programStatus == "to_another_lift_outside":
                self.programStatus.update_programStatus(programStatus="moving_lift_outside")
            elif programStatus == "to_lift_inside":
                self.programStatus.update_programStatus(programStatus="moving_lift_inside")
            elif programStatus == "ready_move":
                self.programStatus.update_programStatus(programStatus="moving")
        
        if signal == "STOP_RECEIVED":
            if programStatus == "stop":
                self.programStatus.update_programStatus(programStatus="stop_complete")
        
        if signal == "GOAL_ARRIVED":
            if programStatus == "moving_lift_outside":
                self.programStatus.update_programStatus(programStatus="to_lift_inside")
            elif programStatus == "moving_lift_inside":
                self.programStatus.update_programStatus(programStatus="at_lift_inside")
            elif programStatus == "moving" and robotStatus == "rest":
                self.programStatus.update_programStatus(programStatus="move_complete")
            elif programStatus == "moving" and robotStatus == "task":
                self.programStatus.update_programStatus(programStatus="arrived")
            elif programStatus == "moving" and robotStatus == "back":
                self.programStatus.reset_programStatus()
                self.robotState.update_robotStatus("idle")
        
        if signal == "RELOCATION_RECEIVED":
            if programStatus == "reset_address":
                self.programStatus.update_programStatus(programStatus="resetting")
            elif programStatus == "relocalization":
                self.programStatus.update_programStatus(programStatus="relocalizing")

        if signal == "RELOCATION_COMPLETE":
            if programStatus == "resetting":
                self.programStatus.update_programStatus(programStatus="reset_success")
            if programStatus == "relocalizing":
                self.programStatus.update_programStatus(programStatus="ready_move")

        if signal == "RELOCATION_FAILURE":
            if programStatus == "resetting":
                self.programStatus.update_programStatus(programStatus="reset_failure")
