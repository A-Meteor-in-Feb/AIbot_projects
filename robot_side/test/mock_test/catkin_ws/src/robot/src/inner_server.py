from flask import Flask, request, jsonify
import rospy
from std_msgs.msg import Float64MultiArray
from robot.msg import Goal

app = Flask(__name__)
rospy.init_node('ros_bridge_pub', anonymous=True, disable_signals=True)
pub = rospy.Publisher("goal", Goal, queue_size=1)

@app.route('/inner-robot/goal', methods=['POST'])
def publish():
    goal = Goal()
    goal.x = request.json['x']
    goal.y = request.json['y']
    goal.z = request.json['z']
    goal.address = request.json['address']
    goal.taskId = request.json['taskId']
    goal.binId = request.json['binId']
    pub.publish(goal)
    return jsonify(ok=True), 200

# 单独进程跑它：python bridge.py （或用 gunicorn -w1）
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8886)