import rospy
from std_msgs.msg import Float64MultiArray
from std_msgs.msg import String
from robot.msg import State
from geometry_msgs.msg import Point
from robot.msg import Goal
import client

def goal_callback(msg: Goal):
    x = msg.x
    y = msg.y
    z = msg.z
    address = msg.address
    print(msg)
    taskId = msg.taskId
    binId = msg.binId
    #do something - 在运行过程中, x, y, z 要变的
    publish_state(1,2,3, taskId, binId, "delivering")
    #do something - 到达目的地之后,  x, y, z 要变的
    publish_state(1,2,3, taskId, binId, "arrived")
    if client.goal_arrived(taskId):
        if client.check_authCode(taskId):
            publish_state(1, 2, 3, taskId, binId, "delivered")
            if client.notify_taskComplete(taskId):
                publish_state(1, 2, 3, 0, 0, "idle")


def publish_state(x, y, z, taskId, binId, status):
    state = State()
    state.position=Point(x=x, y=y, z=z)
    state.coordinateType = "local"
    state.battery = 100
    state.taskStatus = status
    state.taskId = taskId
    state.connection = "online"
    state.autonomousMode = False
    state.fault = False
    state.binsNum = binId
    state_publisher.publish(state)


if __name__ == "__main__":
    rospy.init_node('ros4localization', anonymous=True)

    rospy.Subscriber("goal", Goal, goal_callback, queue_size=1)
    state_publisher = rospy.Publisher("state", State, queue_size=1)
    publish_state(1, 2, 3, 0, 0, "idle")
    
    rospy.spin()