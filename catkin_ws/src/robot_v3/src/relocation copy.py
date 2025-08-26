import rospy
from robot_v3.msg import Goal_v3
from geometry_msgs.msg import PoseStamped

def position_transform():
    ps = PoseStamped()
    ps.header.stamp = rospy.Time.now()
    ps.header.frame_id = "map"
    ps.pose.position.x = 2.6
    ps.pose.position.y = -0.2
    ps.pose.position.z = 0.0

    ps.pose.orientation.x = 0.0
    ps.pose.orientation.y = 0.0
    ps.pose.orientation.z = -0.79161106
    ps.pose.orientation.w = 0.61102531
    return ps

def publish_goal():
    goal = Goal_v3()
    goal.pose = position_transform()
    goal.floor = "2m"
    goal.relocation = False
    ros_pub_goal.publish(goal)
    rospy.loginfo(f"\n Forwarded the goal info to the planning part \n {goal}\n")

if __name__ == "__main__":
    rospy.init_node("robot_comNode", anonymous=False)
    ros_pub_goal = rospy.Publisher("/goal_v3", Goal_v3, queue_size=1)
    rospy.sleep(0.1)
    publish_goal()
