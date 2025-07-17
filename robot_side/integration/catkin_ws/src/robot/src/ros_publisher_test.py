#!/usr/bin/env python3
import rospy
from robot.msg import State
from std_msgs.msg import Header

def publish_topics():

    rospy.init_node("test_publisher")

    pub_state = rospy.Publisher("state", State, queue_size=10)

    rate = rospy.Rate(1)

    while not rospy.is_shutdown():

        state = State()
        state.x = 3.14
        state.y = 2.72
        state.z = 0.0
        state.battery = 75
        state.taskStatus = "moving"
        state.connection = "online"
        state.fault = False
        state.cargoLoad = 5

        pub_state.publish(state)

        rate.sleep()

if __name__ == "__main__":
    try:
        publish_topics()
    except rospy.ROSInterruptException:
        print("exiting...")
        pass