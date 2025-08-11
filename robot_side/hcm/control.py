from flask import Flask
from flask import request
from flask import jsonify
from datetime import datetime
from datetime import timezone

from utils import response
from utils import efficient_interfaces
from utils import hardware_state
import utils.movement as movement

DEFAULT_SPEED = 1

app = Flask(__name__)

@app.route('/api/hcm/move', methods=['POST'])
def moveToPosition():
    payload = request.get_json()
    
    target = {
        "x": payload.get("x"),
        "y": payload.get("y"),
        "z": payload.get("z"),
        "coordinateType": payload.get("coordinateType"),
        "speed": payload.get("speed", DEFAULT_SPEED)
    }

    if movement.validateTarget(target):
        result = movement.startMovement(target)
        if result['success']:
            tsp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-4]+"Z"
            data = {
                "status": "success",
                "message": "Moving to target position",
                "estimated_duration": movement.calculateDuration(target),
                "timestamp": tsp
            }
            success_resp = response.success_reponse(data=data)
            return jsonify(success_resp), 200
        else:
            message = result['message']
            tsp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-4]+"Z"
            error_resp = response.error_response(message=message, code=500, timestamp=tsp)
            return jsonify(error_resp), 500
    else:
        tsp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-4]+"Z"
        error_resp = response.error_response(message="Invalid target position", code=500, timestamp=tsp)
        return jsonify(error_resp), 500


@app.route('/api/hcm/stop', method=['POST'])
def stopToPosition():
    payload = request.get_json()

    # 发送停止运行的信号

    # 获取现在的位置信息
    current_pos = efficient_interfaces.readPositionSensors()

    data = {
        "status": "success",
        "message": "Motion stopped",
        "current_position": {
            "x": current_pos.x,
            "y": current_pos.y,
            "z": current_pos.z
        },
        "timestamp": hardware_state.getCurrentTimestamp()
    }

    success_resp = response.success_reponse(data=data)

    return jsonify(success_resp), 200

