from datetime import datetime
import threading
import copy
from enum import Enum


def utc_now_ms():
    now = datetime.now()    
    timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")
    return timestamp_str


class TaskStatus(Enum):
    PENDING_RECEIPT = 40 #待签收
    DELIVERY_FAILED = 80 #配送失败
    DELIVERY_COMPLETE = 50 #配送完成


class StateInfo:
    def __init__(self):
        """
        state: 用于维护机器人自身的状态
        """
        self.lock = threading.Lock()
        
        self.state = {
            "position": {"x": 0, "y": 0, "theta": 0},
            "ip": "",
            "coordinateType": "map",
            "battery": 0,
            "taskStatus": "",
            "taskId": 0,
            "connection": "offline",
            "autonomousMode": True,
            "fault": False,
            "binsNum": 0
        }
        

    def get_state(self):
        """
        获得实时机器人自身状态
        """
        with self.lock:
            return copy.deepcopy(self.state)
    
    def update_position(self, new_x, new_y, new_theta):
        """ 
        用来更新机器人位置的函数
        参数:
            new_x: 新的x的值 - float
            new_y: 新的y的值 - float
            new_theta: 新的theta值 - float
        """
        with self.lock:
            self.state["position"].update({
                "x": new_x,
                "y": new_y,
                "theta": new_theta
            })

    def update_ip(self, ip_addr):
        """
        用来更新机器人的IP地址
        参数:
            ip_addr: str, 机器人IP地址
        """
        with self.lock:
            self.state["ip"] = ip_addr
    
    def update_battery(self, batteryPercentage):
        """
        用来更新机器人电池电量的函数
        参数: 
            batteryPercentage: 一个int值, 代表电池电量的百分比.
        """
        with self.lock:
            self.state["battery"] = batteryPercentage
    
    def update_fault(self, b_fault):
        """
        用来更新机器人是否发生故障的函数
        参数: 
            b_fault: 一个bool值, 代表是否发生故障.
            如果发生故障, 再具体地发布error主题.
        """
        with self.lock:
            self.state["fault"] = b_fault

    def update_taskStatus(self, status):
        """
        用来更新机器人的工作状态
        参数:
            status: string, 代表机器人的状态
            目前是4个状态: idle, delivering, arrived, delivered
        """
        with self.lock:
            self.state["taskStatus"] = status

    def update_taskId(self, task_id):
        """
        用来更新机器人执行的任务的任务代号
        参数:
            task_id: 一个数字, 代表任务
        """
        with self.lock:
            self.state["taskId"] = task_id

    def update_connection(self, connection):
        """
        用来更新机器人的网络连接状态
        参数:
            connection: string - "online" or "offline"
            "offile"为初始值, 上线后更新为online, 然后等到正常退出, 在变为offline.
        """
        with self.lock:
            self.state["connection"] = connection

    def update_binsNum(self, bins_num):
        """
        用来更新机器人的货仓数量, 但是其实我个人认为这应该是一个固定值
        参数:
            bins_num: int, 表示有多少货仓
        """
        with self.lock:
            self.state["binsNum"] = bins_num


class StatusBackend:
    def __init__(self):
        """
        statusBackend: 用于维护后台发来的任务状态, 用于实时核对任务状态的变化
        """
        self.lock = threading.Lock()

        self.statusBackend = {
            "taskId": 0,
            "status": 0
        }

    def get_statusBackend(self):
        """
        获得实时后台发布的任务状态
        """
        with self.lock:
            return copy.deepcopy(self.statusBackend)

    def update_statusBackend(self, taskId, status):
        """
        用于更新任务状态.
        参数:
            taskId: 任务Id
            status: int 一个数字, 代表后台现在对于任务执行状态的记录
        """
        with self.lock:
            self.statusBackend.update({
                "taskId": taskId,
                "status": status
            })


class CurrentOrder:
    def __init__(self):
        """
        currentOrder: 用于维护记录当前执行的任务的状态 --- 后面可能还会更新 
        """
        self.lock = threading.Lock()

        self.currentOrder = {
            "taskId": 0,
            "code": "",
            "goal_position": {"x": 0, "y": 0, "theta": 0},
            "floor": "",
            "room": "",
            "binId": 0
        }

    def get_currentOrder(self):
        """
        获得当前任务详细信息, 可能用于二维码核对, 打开相应货仓等等
        """
        with self.lock:
            return copy.deepcopy(self.currentOrder)    
    
    def update_currentOrder(self, taskId, code, goal_position, floor, room, binId):
        """
        用于更新当前执行的任务的信息
        参数:
            taskId: task ID
            code: 用于核对二维码的code
            goal_position: 目标地址
            floor: 目标地址楼层
            room: 目标地址门牌号
            binId: 货仓id
        """
        with self.lock:
            self.currentOrder.update({
                "taskId": taskId,
                "code": code,
                "goal_position": goal_position,
                "floor": floor,
                "room": room,
                "binId": binId
            })