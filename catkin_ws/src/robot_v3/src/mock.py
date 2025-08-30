import rospy
from std_msgs.msg import String
from robot_v3.msg import Goal_v3
from geometry_msgs.msg import PoseStamped
from tf.transformations import quaternion_from_euler
import time

from std_msgs.msg import Int32

def position_transform(position):
    """
    这个函数用来把普通坐标点转换成tianxin可以直接用的pose
    参数:
        position: {"x": float, "y": float, "theta": float}
    返回:
        一个 PoseStamped 对象
    """
    ps = PoseStamped()
    ps.header.stamp = rospy.Time.now()
    ps.header.frame_id = "map"
    ps.pose.position.x = position["x"]
    ps.pose.position.y = position["y"]
    ps.pose.position.z = 0.0

    q = quaternion_from_euler(0.0, 0.0, position["theta"])
    ps.pose.orientation.x = q[0]
    ps.pose.orientation.y = q[1]
    ps.pose.orientation.z = q[2]
    ps.pose.orientation.w = q[3]

    return ps

def publish_goal():
    """
    给tianxin发布他规划路径需要的数据
    参数:
        outside_lift: 电梯外面的坐标
        inside_lift: 电梯内部的坐标
        final_position: 最后机器人需要到达的坐标
        final_floor: 最后机器人需要到达的楼层
    """

    goal = Goal_v3()
    goal_pos = {
      "theta": 0.32999998331069946,
      "x": 32.720001220703125,
      "y": -3.1600000858306885
    }
    goal_floor = "2m"
    relocation = True
    goal.pose = position_transform(goal_pos)
    goal.floor = goal_floor
    goal.relocation = relocation
    publisher.publish(goal)
    rospy.loginfo(f"\n Forwarded the goal info to the planning part \n {goal}\n")
    


if __name__ == "__main__":
    rospy.init_node('mock_rosNode', anonymous=True)

    publisher = rospy.Publisher("/goal_v3", Goal_v3, queue_size=1)
    time.sleep(0.1)
    publish_goal()