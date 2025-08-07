import rospy
from std_msgs.msg import Float64MultiArray
from std_msgs.msg import String
from robot.msg import State

def goal_callback(msg: Float64MultiArray):
    x, y, z = msg.data
    print(msg.data)
    publish_state("delivering")
    publish_state("arrived")
    publish_state("delivered")


def publish_state(x, y, z, status):
    state = State()
    state.position(x=x, y=y, z=z)
    state.taskStatus = status
    state_publisher.publish(state)


if __name__ == "__main__":
    rospy.init_node('ros4localization', anonymous=True)

    rospy.Subscriber("goal", Float64MultiArray, goal_callback, queue_size=1)
    state_publisher = rospy.Publisher("state", String, queue_size=1)

    rospy.spin()