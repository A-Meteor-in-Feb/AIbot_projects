from flask import Flask
from flask import request
from flask import jsonify
from flask import Blueprint
from flask import abort
import dataInfo

class HttpServer:
    def __init__(self, state: dataInfo.StateInfo):
        """
        用于接收后台发来的请求.
        参数:
            state: 机器人状态
            head: url的协议, http或者https.
            host: 机器人的host
            port: 机器人的端口
        """
        self.state = state

        self.bp = Blueprint("robot_api", __name__)

        self.bp.add_url_rule(
            "/api/robot/server/task",
            view_func=self.handle_request,
            methods = ["POST"]
        )

    def handle_request(self):
        """
        接口7: 机器人接收来自后台的请求, 并给出响应
        根据字段中的 taskStatus 判断为[任务下发]或者[任务取消]
        """
        data = request.get_json()

        taskStatus = data.get("taskInfo").get("status")

        # 下发任务
        if taskStatus == 20:
            return jsonify({"status": "ok"}), 200
        # 取消任务
        elif taskStatus == 60:
            return jsonify({"status": "ok"}), 200
        else:
            return jsonify({"status": "ok"}), 200



