from flask import Flask
from flask import request
from flask import jsonify
import paho.mqtt.client as mqtt
import json


app = Flask(__name__)
inner_mqtt = mqtt.Client()
inner_mqtt.connect("192.168.10.249", 1883)
inner_mqtt.loop_start()

@app.route('/api/robots/<string:robotId>/task', methods=['POST'])
def task_handler(robotId):
    """
        Receive the request from the backend.
        Response to it and make corresponding actions.
    """

    #TODO: 有没有authorization的处理, 包不包括token

    data = request.get_json(force=True)
    parameters = data.get('params', {})

    taskId = parameters.get("taskId")
    binId = parameters.get("binId")
    number = parameters.get("number")
    location = parameters.get("location")
    address = location.get("address")
    coordinateType = location.get("coordinateType")
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

    result = {"status": "accpted"}

    return jsonify(result), 200


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8888)

