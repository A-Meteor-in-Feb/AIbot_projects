from flask import Flask
from flask import request
from flask import jsonify
from flask import Blueprint
from flask import abort
import dataInfo

class HttpServer:
    def __init__(self, state: dataInfo.StateInfo, statusBackend: dataInfo.StatusBackend, currentOrder: dataInfo.CurrentOrder, elevatorPlan: dataInfo.ElevatorPlan):
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
        self.elevatorPlan = elevatorPlan

        self.bp = Blueprint("robot_api", __name__)

        self.bp.add_url_rule(
            "/api/robot/server/task",
            view_func=self.handle_request,
            methods = ["POST"]
        )

        self.level = {"1": 1, "2m": 2, "3": 3, "4": 4, "5": 5}

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

        status_new = data.get("taskInfo").get("status")
        taskId_new = data.get("taskId")
        print(f"receive:{status_new}, {taskId_new}\n")

        statusBackend = self.statusBackend.get_statusBackend()
        status_old = statusBackend.get("status")
        taskId_old = statusBackend.get("taskId")
        print(f"now: {status_old}\n")

        # 当前 任务状态 与 新任务状态不符, 且 任务ID不同, 说明是新分配了一个任务
        if status_old != status_new and taskId_old != taskId_new: ###有修改
            """
            更新各个字段的值
            MQTT连接上之后机器人会变味idle状态
            主逻辑里判断如果 idle且taskId不为0 则用ros给tianxin发送goal 话题
            然后更改机器人为delivering状态
            """
            #get 相关值
            code = data.get("code")

            #更新配送需要的信息
            self.currentOrder.update_deliveryDetails(taskId=taskId_new, code=code)

            goal_addrList = data.get("taskInfo").get("addressList")
            len_goal_addrList = len(goal_addrList)
            self.store_goalPositions(goal=True, addrList=goal_addrList)
            if len_goal_addrList == 3:
                self.store_elevatorCommand(goal=True)

            
            return_addrList = data.get("addressList")
            len_return_addrList = len(return_addrList)
            self.store_goalPositions(goal=False, addrList=return_addrList)
            if len_return_addrList == 3:
                self.store_elevatorCommand(goal=False)

            #机器人可以开始执行新任务
            self.state.update_taskId(task_id=taskId_new)
            self.state.update_taskStatus("idle")
            #记录后台让机器人执行的任务的状态
            self.statusBackend.update_statusBackend(taskId=taskId_new, status=status_new)

            return jsonify({"status": "ok"}), 200
        
        # 当前有任务且收到了来自后台发送的取消任务的请求 statusBackend.get("status") == 20 and
        elif taskId_new == taskId_old and status_new != status_old:
            """
            收到这个取消任务请求的话, 就更新各个状态记录的字段为0
            然后更新机器人状态为 取消配送 - cancel_delivery
            然后给tianxin发信号之类的回初始化点位, 等待下一次配送
            如果是因为故障之类的, 就直接offline吧???? 这个还需要再想一下
            """
            self.statusBackend.update_statusBackend(taskId=taskId_old, status=status_new)
            if status_new == 60:
                self.state.update_taskId(0)
                self.state.update_taskStatus("cancel_delivery")

            return jsonify({"status": "ok"}), 200
        
        elif status_new == 20 or status_new == 30 or status_new == 40 or status_new == 50 or status_new == 70 or status_new == 80:

            return jsonify({"status": "received"}), 200
        else: 
            #其他情况都他妈的是bad request
            return jsonify({"status": "bad request"}), 400
        

    def store_goalPositions(self, goal, addrList):
        """
        存储更新订单目的地址以及机器人返回原点的地址详情
        参数:
            goal: bool, 代表当前更新的事配送目的地址(True) 还是 返回原点地址(False).
            addrList: 目标地址的详细信息
        """
        addr_len = len(addrList)

        lift_out = {}
        lift_in = {}
        pos = {}
        out_lift_name = ""
        in_lift_name = ""
        flr = ""
        room = ""
        house = ""

        #机器人和目标位置在同一楼层
        if addr_len == 1:
            empty_pos = {"x": 0, "y": 0, "theta": 0}
            lift_out = empty_pos
            lift_in = empty_pos
            pos = addrList[0].get("pose").get("dock")
            flr = addrList[0].get("floor")
            room = addrList[0].get("identity").get("desc")
            house = addrList[0].get("house")

        #机器人和目标位置不在同一楼层
        elif addr_len == 3:
            for item in addrList:
                desc = item.get("identity").get("desc")
                dock = item.get("pose").get("dock")
                if "ELEVATOR_out" in desc:
                    lift_out = dock
                    out_lift_name = desc
                elif "ELEVATOR_in" in desc:
                    lift_in = dock
                    in_lift_name = desc
                else:
                    pos = dock
                    flr = item.get("floor")
                    room = desc
                    house = item.get("house")

        #后台传输参数有错
        else:
            print("Error - Backend response bad parameters.")

        if goal:
            self.currentOrder.update_goalPositions(outside_lift=lift_out, inside_lift=lift_in, goal_position=pos, out_lift_name=out_lift_name, in_lift_name=in_lift_name, goal_floor=flr, goal_room=room, house=house)
        else:
            self.currentOrder.update_returnPositions(outside_lift=lift_out, inside_lift=lift_in, return_position=pos, out_lift_name=out_lift_name, in_lift_name=in_lift_name, return_floor=flr, return_room=room, house=house)

    def store_elevatorCommand(self, goal):
        """
        用于更新机器人和电梯交互的指令
        参数:
            goal: True or False, True 代表要更新送货需要的指令, False 代表要更新返回需要的指令
        """
        BUILDING = ""
        ROBOT_FLOOR = ""
        ELEVATOR_NAME_OUT = ""
        ELEVATOR_NAME_IN = ""
        MOVE = ""
        TO = ""

        robot_info = self.state.get_state()

        if goal:
            info = self.currentOrder.get_currentOrder().get("goal_positions")
            TO = info.get("goal_floor")
        else:
            info = self.currentOrder.get_currentOrder().get("return_positions")
            TO = info.get("return_floor")

        ROBOT_FLOOR = robot_info.get("floor")
        ROBOT_FLOOR_int = self.level.get(ROBOT_FLOOR)

        TO_int = self.level.get(TO)

        if ROBOT_FLOOR_int > TO_int:
            MOVE = "d"
        else:
            MOVE = "u"

        ELEVATOR_NAME_OUT = info.get("out_lift_name")
        ELEVATOR_NAME_IN = info.get("in_lift_name")
        BUILDING = info.get("house")

        command_1 = f"{BUILDING}:{ROBOT_FLOOR}:{ELEVATOR_NAME_OUT}:{MOVE}"
        command_2 = f"{BUILDING}:{ROBOT_FLOOR}:{ELEVATOR_NAME_IN}:{TO}"

        if goal:
            self.elevatorPlan.update_deliveringCommand(command_1=command_1, command_2=command_2)
        else:
            self.elevatorPlan.update_returningCommand(command_1=command_1, command_2=command_2)


if __name__ == "__main__":
    # 初始化三个依赖对象（这里只是举例，实际要根据 dataInfo 里的定义来）
    state = dataInfo.StateInfo()
    statusBackend = dataInfo.StatusBackend()
    currentOrder = dataInfo.CurrentOrder()

    # 实例化 HttpServer
    server = HttpServer(state, statusBackend, currentOrder)

    # 创建 Flask app
    app = server.create_app()

    # 启动服务，端口 8000
    app.run(host="0.0.0.0", port=8000, debug=True)
