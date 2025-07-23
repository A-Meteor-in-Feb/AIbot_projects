#!/usr/bin/env python3
import rospy
import time
from robot.msg import State
from robot.msg import Error
from robot.msg import Cargo
from robot.msg import Slot
from std_msgs.msg import Header
from datetime import datetime
from datetime import timezone
from geometry_msgs.msg import Point


def publish_state():

    state = State()
        
    state.position = Point(x=12.34, y=5.67, z=0.00)
    state.coordinateType = "geodetic"
    state.battery = 75
    state.taskStatus = "delivering"
    state.taskId = 12345
    state.connection = "online"
    state.autonomousMode = False
    state.fault = False
    state.binsNum = 6

    state_publisher.publish(state)


def publish_error():

    error = Error()

    error.timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-4]+"Z"
    error.errorCode = "ROBOT_TIPPED"
    error.severity = "high"
    error.message = "The robot has fallen sideways near Lobby A"
    error.taskId = 12345
    error.position = Point(x=1.2921, y=103.7764, z=15.0)
    error.suggestion = "Check if robot needs manual recovery"
    error.retryable = False

    error_publisher.publish(error)


def publish_cargo():

    cargo = Cargo()

    cargo.timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-4]+"Z"
    cargo.doorStatus = "closed"
    cargo.cargoPresent = True
    slot1 = Slot(slotId=1, occupied=True, itemId="SKU12345")
    slot2 = Slot(slotId=2, occupied=False, itemId="N.A.")
    cargo.slots = [slot1, slot2]
    cargo.temperature = 24.5
    cargo.humidity = 60
    cargo.tamperAlert = False
    cargo.lastAccessMethod = "user_pickup"
    cargo.taskId = 12345

    cargo_publisher.publish(cargo)

if __name__ == "__main__":

    rospy.init_node("test_ros_publisher")

    state_publisher = rospy.Publisher("state", State, queue_size=1)
    error_publisher = rospy.Publisher("error", Error, queue_size=1)
    cargo_publisher = rospy.Publisher("cargo", Cargo, queue_size=1)

    rate = rospy.Rate(0.5)   
    while not rospy.is_shutdown():
        publish_state()
        publish_error()
        publish_cargo()
        rate.sleep()
