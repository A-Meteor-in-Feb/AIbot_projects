import rospy
from robot_v3.msg import Goal_v3
from geometry_msgs.msg import PoseStamped

def position_transform():
    ps = PoseStamped()
    ps.header.stamp = rospy.Time.now()
    ps.header.frame_id = "map"
    ps.pose.position.x = 12.069999694824219
    ps.pose.position.y = 1.4900000095367432
    ps.pose.position.z = 0.0

    ps.pose.orientation.x = 0.0
    ps.pose.orientation.y = 0.0
    ps.pose.orientation.z = 0.1345903163229573
    ps.pose.orientation.w = 0.9909013304825492
    return ps

def publish_goal():
    goal = Goal_v3()
    goal.pose = position_transform()
    goal.floor = "3"
    goal.relocation = True
    ros_pub_goal.publish(goal)
    rospy.loginfo(f"\n Forwarded the goal info to the planning part \n {goal}\n")

if __name__ == "__main__":
    rospy.init_node("robot_comNode", anonymous=False)
    ros_pub_goal = rospy.Publisher("/goal_v3", Goal_v3, queue_size=1)
    rospy.sleep(0.5)
    publish_goal()
    rospy.sleep(0.5)
