from flask import Flask
from flask import request
from flask import jsonify
import time

import hardware_state
import efficient_interfaces
from utils import response


app = Flask(__name__)

@app.route('/api/hcm/status', methods=['GET'])
def getHardwareStatus():
    """
        获取机器人完整硬件状态,
        供CM定期轮询使用.

        TODO: 可能会出现什么问题导致无法获取这些状态信息然后出现error呢?
        你肯定不能一直 always 是成功的对吧?
    """
    position = hardware_state.getCurrentPosition()
    battery = hardware_state.getBatteryStatus()
    sensors = hardware_state.getAllSensorStatus()
    motion = hardware_state.getMotionStatus()

    data = {
        "position": position,
        "coordinateType": "local",
        "battery": battery,
        "connection": "online",
        "fault": hardware_state.checkSystemFault(),
        "sensors": sensors,
        "motion": motion,
        "timestamp": hardware_state.getCurrentTimestamp()
    }

    success_resp = response(data)

    return jsonify(success_resp), 200


@app.route('/api/hcm/position', methods=['GET'])
def getPosition():
    """
        高频位置查询专用接口, 优化响应速度

        TODO: 可能会出现什么问题导致无法获取这些状态信息然后出现error呢?
        你肯定不能一直 always 是成功的对吧?
    """
    position = efficient_interfaces.readPositionSensors()

    data = {
        "position":{
            "x": position.x,
            "y": position.y,
            "z": position.z,
            "accurary": position.accuracy
        },
        "coordinateType": "local",
        "timestamp": hardware_state.getCurrentTimestamp()
    }

    success_resp = response.success_reponse(data)

    return jsonify(success_resp), 200


@app.route('/api/hcm/battery', methods=['GET'])
def getBattry():
    """
        获取电池状态, 虽然我不知道为什么要单独获取一个电池状态

        TODO: 可能会出现什么问题导致无法获取这些状态信息然后出现error呢?
        你肯定不能一直 always 是成功的对吧?
    """
    battery = efficient_interfaces.readBatteryInfo()

    data = {
        "level": battery.level,
        "voltage": battery.voltage,
        "current": battery.current,
        "temperature": battery.temperature,
        "charging": battery.charging,
        "estimated_runtime": battery.estimated_runtime,
        "timestamp": hardware_state.getCurrentTimestamp()
    }

    success_resp = response.success_reponse(data)

    return jsonify(success_resp), 200