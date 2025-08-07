from flask import Flask
from flask import request
from flask import jsonify
import paho.mqtt.client as mqtt
import json
import logging
from config import FLASK_HOST, FLASK_PORT
MQTT_INNER = dict(host="192.168.10.249", port=1883, topic_goal="goal")


app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

inner_mqtt = mqtt.Client(client_id="robot_server", callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
inner_mqtt.connect(MQTT_INNER["host"], MQTT_INNER["port"])
inner_mqtt.loop_start()

@app.route('/api/robots/<string:robotId>/task', methods=['POST'])
def task_handler(robotId):

    #TODO: 有没有authorization的处理, 包不包括token

    data = request.get_json(force=True)
    parameters = data.get('params', {})

    taskId = parameters.get("taskId")
    binId = parameters.get("binId")
    location = parameters.get("location")
    position = location.get("position")
    x = position.get("x")
    y = position.get("y")
    z = position.get("z")

    z = z/100 + 2
    
    mqtt_payload = {
        "taskId": taskId,
        "binId": binId,
        "x": x,
        "y": y,
        "z": z
    }

    inner_mqtt.publish("goal", json.dumps(mqtt_payload), qos=1)
    logging.info(f"Publish goal to ros side")

    result = {"status": "accpted"}

    return jsonify(result), 200


if __name__ == "__main__":
    app.run(host=FLASK_HOST, port=FLASK_PORT)

