import json, logging, rospy, paho.mqtt.client as mqtt
from std_msgs.msg import Float64MultiArray
from robot.msg import State
from client import get_authCode, notify_taskComplete

MQTT_INNER = dict(host="192.168.10.249", port=1883, topic_goal="goal")
MQTT_OUTER = dict(host="10.25.0.2", port=1883, topic_state="state")
ROBOT_ID = "R1234"
class MqttRosBridge:
    def __init__(self):
        self.task_id = None
        self.bin_id  = None

        self.ros_goal_pub  = rospy.Publisher("goal", Float64MultiArray, queue_size=1)
        rospy.Subscriber("state", State, self.handle_state, queue_size=1)

        self.inner = mqtt.Client(client_id="inner_mqtt", callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
        self.inner.on_connect = self.on_inner_connect
        self.inner.message_callback_add("goal", self.on_goal)
        self.inner.connect(MQTT_INNER["host"], MQTT_INNER["port"])
        self.inner.loop_start()

        self.outer = mqtt.Client(client_id="outer_mqtt", callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
        self.outer.on_connect = lambda c,u,f,rc, properties: logging.info(f"Outer MQTT connected: {rc}")
        self.outer.connect(MQTT_OUTER["host"], MQTT_OUTER["port"])
        self.outer.loop_start()

        print("success")

    def on_inner_connect(self, client, userdata, flags, rc, props=None):
        client.subscribe("goal", qos=1)
        print("Subscribed to MQTT goal")

    def on_goal(self, client, userdata, msg):
        data       = json.loads(msg.payload.decode())
        self.task_id = data["taskId"]
        self.bin_id  = data["binId"]
        print(f"Received goal: {data}")

        arr = Float64MultiArray(data=[data["x"], data["y"], data["z"]])
        self.ros_goal_pub.publish(arr)

    def handle_state(self, msg: State):
        
        self.publish_state(msg, msg.taskStatus)
        
        if msg.taskStatus == "arrived" and get_authCode(self.task_id):
            self.publish_state(msg, "delivered")
        
        if msg.taskStatus == "delivered" and notify_taskComplete(self.task_id):
            self.publish_state(msg, "idle")

    def publish_state(self, msg: State, status: str):
        payload = {
            "position": {
                "x": msg.position.x,
                "y": msg.position.y,
                "z": msg.position.z
            },
            "coordinateType": "local",
            "battery": 100,
            "taskStatus": status,
            "taskId": self.task_id,
            "connection": "online",
            "autonomousMode": False,
            "fault": False,
            "binsNum": self.bin_id
        }
        self.outer.publish(f"robots/{ROBOT_ID}/state", json.dumps(payload), qos=0)
        print(f"Published state [{status}]: {payload}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    rospy.init_node("mqtt_ros_bridge", anonymous=True)
    bridge = MqttRosBridge()
    rospy.spin()
