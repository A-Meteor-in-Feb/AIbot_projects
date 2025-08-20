from flask import Flask
from flask import request
from flask import jsonify
from flask import Blueprint
from flask import abort
import dataInfo

class HttpServer:
    def __init__(self, state: dataInfo.StateInfo, statusBackend: dataInfo.StatusBackend, currentOrder: dataInfo.CurrentOrder):
        """
        用于接收后台发来的请求.
        参数:
            state: 机器人执行相关状态
            statusBackend: 后台发送的任务相关状态信息
            currentOrder: 机器人当前执行的任务
            head: url的协议, http或者https.
            host: 机器人的host
            port: 机器人的端口
        """
        self.state = state
        self.statusBackend = statusBackend
        self.currentOrder = currentOrder

        self.bp = Blueprint("robot_api", __name__)

        self.bp.add_url_rule(
            "/api/robot/server/task",
            view_func=self.handle_request,
            methods = ["POST"]
        )

    def create_app(self):
        """
        暴露一个create_app() 在外部
        """
        app = Flask(__name__)
        app.register_blueprint(self.bp)
        return app

    def handle_request(self):
        """
        接口7: 机器人接收来自后台的请求, 并给出响应
        根据字段中的 taskStatus 判断为[任务下发]或者[任务取消]
        """
        data = request.get_json()

        print(f"Get request from the backend: {data}\n")

        status = data.get("taskInfo").get("status")
        taskId = data.get("taskId")
        print(f"receive:{status}, {taskId}\n")

        statusBackend = self.statusBackend.get_statusBackend()
        s = statusBackend.get("status")
        print(f"now: {s}\n")

        # 当前没有任务收到了后台发来的关于任务信息的请求
        if s == 0 and (status == 30 or status == 40): ###有修改
            """
            更新各个字段的值
            MQTT连接上之后机器人会变味idle状态
            主逻辑里判断如果 idle且taskId不为0 则用ros给tianxin发送goal 话题
            然后更改机器人为delivering状态
            """
            #get 相关值
            code = data.get("code")
            #binId = data.get("binId")  -- 先给删了

            addr = data.get("taskInfo").get("addressParams")
            goal_position = addr.get("pose").get("dock")
            goal_floor = addr.get("floor")
            room = addr.get("identity").get("desc")

            restArea = data.get("restArea")
            return_position = restArea.get("pose").get("dock")
            return_floor = restArea.get("floor")
            
            #更新相关状态
            self.statusBackend.update_statusBackend(taskId=taskId, status=status)
            self.currentOrder.update_currentOrder(taskId=taskId, code=code, goal_position=goal_position, goal_floor=goal_floor, room=room, return_position=return_position, return_floor=return_floor)
            self.state.update_taskId(task_id=taskId)

            return jsonify({"status": "ok"}), 200
        
        # 当前有任务且收到了来自后台发送的取消任务的请求 statusBackend.get("status") == 20 and
        elif status == 60:
            """
            收到这个取消任务请求的话, 就更新各个状态记录的字段为0
            然后更新机器人状态为 取消配送 - cancel_delivery
            然后给tianxin发信号之类的回初始化点位, 等待下一次配送
            如果是因为故障之类的, 就直接offline吧???? 这个还需要再想一下
            """
            self.state.update_taskStatus("cancel_delivery")
            self.statusBackend.update_statusBackend(taskId=taskId, status=status)

            return jsonify({"status": "ok"}), 200
        
        elif status == 20 or status == 30 or status == 40 or status == 50 or status == 70 or status == 80:

            return jsonify({"status": "received"}), 200
        else: 
            #其他情况都他妈的是bad request
            return jsonify({"status": "bad request"}), 400
