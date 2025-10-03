from datetime import datetime
from enum import Enum
import threading
import copy

def utc_now_ms():
    """
    获取当前 UTC 时间并返回字符串格式
    返回:
        str: 当前 UTC 时间的字符串表示，格式为 "YYYY-MM-DD HH:MM:SS"
    """
    now = datetime.now()
    timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")
    return timestamp_str

class TaskStatus(Enum):
    """
    任务状态枚举类, 用于表示订单或配送任务在不同阶段的状态值

    Attributes:
        DELIVERING (int): 配送中（值为 30)
        PENDING_RECEIPT (int): 待收货（值为 40)
        DELIVERY_COMPLETE (int): 配送完成（值为 50)
        CANCELLED (int): 已取消（值为 60)
        DELIVERY_FAILED (int): 配送失败（值为 80)
        RESTOCKING (int): 补货中（值为 90)
    """
    DELIVERING = 30
    PENDING_RECEIPT = 40
    DELIVERY_COMPLETE = 50
    CANCELLED = 60
    DELIVERY_FAILED = 80
    RESTOCKING = 90

class RobotStateInfo:
    def __init__(self):
        """
        用于维护、记录、存储机器人当前所有状态.
        包括:
            localization: 机器人的定位信息
            ip: 机器人IP地址
            floor: 机器人当前所在楼层
            house: 机器人当前所在楼
            coordinateType: 所在坐标地图
            robotStatus: 机器人当前状态
            robotTaskId: 机器人当前执行的任务ID
            connection: 机器人在线状态
            battery: 机器人电池电量
            fault: 机器人是否发生故障
        """
        self.lock = threading.Lock()

        self.robotState = {
            "localization": {"x": 0, "y": 0, "theta": 0},
            "ip": "",
            "floor": "",
            "house": "",
            "coordinateType": "map",
            "robotStatus": "offline",
            "robotTaskId": 0,
            "connection": "offline",
            "battery": 0,
            "fault": False
        }
    
    def get_state(self):
        """
        获得机器人实时状态
        """
        with self.lock:
            return copy.deepcopy(self.robotState)
        
    def update_localization(self, new_x, new_y, new_theta):
        """
        用来更新机器人的实时位置.
        参数:
            new_x: 新的x的值 - float
            new_y: 新的y的值 - float
            new_theta: 新的theta值 - float
        """
        with self.lock:
            self.robotState["localization"].update({
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
            self.robotState["ip"] = ip_addr

    def update_position(self, floor, house):
        """
        用来更新机器人所在楼层
        参数:
            floor: str, 机器人所在楼层
            building: str, 机器人所在建筑物
        """
        with self.lock:
            self.robotState["floor"] = floor
            self.robotState["house"] = house

    def update_robotTaskId(self, taskId):
        """
        用来更新机器人执行的任务的任务代号
        参数:
            taskId: 一个数字, 代表任务
        """
        with self.lock:
            self.robotState["robotTaskId"] = taskId
        
    def update_robotStatus(self, robotStatus):
        """
        用来更新机器人的状态值
        参数:
            robotStatus: 一个数字, 代表机器人的状态
        """
        with self.lock:
            self.robotState["robotStatus"] = robotStatus

    def update_connection(self, connection):
        """
        用来更新机器人的网络连接状态
        参数:
            connection: string - "online" or "offline"
            "offile"为初始值, 上线后更新为online, 然后等到正常退出, 在变为offline.
        """
        with self.lock:
            self.robotState["connection"] = connection

    def update_battery(self, batteryPercentage):
        """
        用来更新机器人电池电量的函数
        参数: 
            batteryPercentage: 一个int值, 代表电池电量的百分比.
        """
        with self.lock:
            self.robotState["battery"] = batteryPercentage

    def update_fault(self, b_fault):
        """
        用来更新机器人是否发生故障的函数
        参数: 
            b_fault: 一个bool值, 代表是否发生故障.
            如果发生故障, 再具体地发布error主题.
        """
        with self.lock:
            self.robotState["fault"] = b_fault
        

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
        currentOrder: 用于维护记录当前执行的任务的详细信息 --- 后面可能还会更新 
        包括:
            taskId: 当前执行任务的ID
            code: 当前任务的对应二维码
            goal_positions: 要走到的对应地址位置信息
            return_positions: 返回的对应地址位置信息
            delivery_info: 要配送的货品的数量与货道号 
        """
        self.lock = threading.Lock()
        self.currentOrder = {
            "taskId": 0,
            "code": "",
            "goal_positions":[],
            "return_positions":[],
            "delivery_info":[]
        }

    def get_currentOrder(self):
        """
        获得当前任务详细信息, 可能用于二维码核对, 打开相应货仓等等
        """
        with self.lock:
            return copy.deepcopy(self.currentOrder)    
    
    def update_deliveryDetails(self, taskId, code):
        """
        用于更新当前执行的任务的信息
        参数:
            taskId: task ID
            code: 用于核对二维码的code
        """
        with self.lock:
            self.currentOrder["taskId"] = taskId
            self.currentOrder["code"] = code

    def update_goalPositions(self, goal_pos_dict):
        """
        用于更新当前任务的目标地址的所有信息
        参数:
            goal_pos_dict = {"room": "", "dock": {}, "floor": "", "house":""}
        """
        with self.lock:
            self.currentOrder["goal_positions"].append(goal_pos_dict)

    def update_returnPositions(self, return_pos_dict):
        """
        用于更新当前任务结束后机器人返回地址的详细信息.
        参数:
            return_pos_dict = {"room": "", "dock": {}, "floor": "", "house":""}
        """
        with self.lock:
            self.currentOrder["return_positions"].append(return_pos_dict)

    def update_deliveryInfo(self, cargo_dict):
        """
        用于更新当前任务的详细货物信息
        参数:
            cargo_dict = {"binId": binId, "number": number}
        """
        with self.lock:
            self.currentOrder["delivery_info"].append(cargo_dict)

    def reset_currentOrder(self):
        """
        任务结束后重置.
        """
        with self.lock:
            self.currentOrder = {
                "taskId": 0,
                "code": "",
                "goal_positions": [],
                "return_positions": [],
                "delivery_info": []
            }


class InstructionInfo:
    def __init__(self):
        """
        用于记录机器人重定位地址信息
        """
        self.lock = threading.Lock()

        self.relocalizationInfo = {
            "relocalization_position": {"x": 0.0, "y": 0.0, "theta": 0.0},
            "floor": "",
            "house": ""
        }
        
        self.movePositions = []

        self.command = ""
    
    def get_relocalizationInfo(self):
        """
        用于获取机器人重定位地址信息
        """
        with self.lock:
            return copy.deepcopy(self.relocalizationInfo)
        
    def get_movePositions(self):
        """
        用于获取机器人需要移动到的位置信息
        movePositions = [ {"room": "", "dock": {}, "floor": "", "house":""}, ... ]
        """
        with self.lock:
            return copy.deepcopy(self.movePositions)
        
    def get_command(self):
        """
        获得后台传过来的指令
        """
        with self.lock:
            return self.command
        
    def update_command(self, commandContent):
        """
        更新后台传过来的指令
        """
        with self.lock:
            self.command = commandContent
    
    def update_relocalizationInfo(self, position, floor, house):
        """
        用于更新机器人重定位地址信息
        参数:
            position: 重定位地址坐标
            floor: 重定位楼层信息
            house: 重定位楼的信息
        """
        with self.lock:
            self.relocalizationInfo.update({
                "relocalization_position": position,
                "floor": floor,
                "house": house
            })

    def update_movePositions(self, move_dict):
        """
        更新move指令下, 机器人需要走的点位
        参数:
            move_dict = {"room": "", "dock": {}, "floor": "", "house":""}
        """
        with self.lock:
            self.movePositions.append(move_dict)

    def reset_relocalizationInfo(self):
        """
        当一个重定位结束后, 重置重定位信息
        """
        with self.lock:
            self.relocalizationInfo.update({
                "relocalization_position": {"x": 0.0, "y": 0.0, "theta": 0.0},
                "floor": "",
                "house": ""
            })
    
    def reset_movePositions(self):
        """
        机器人走到指定地点后要重置数据
        """
        with self.lock:
            self.movePositions = []

    def reset_command(self):
        """
        将存储的指令重置
        """
        with self.lock:
            self.command = ""
    

class ProgramStatus:
    def __init__(self):
        """
        用来记录程序执行的状态
        """
        self.lock = threading.Lock()
        self.programStatus = ""
        self.cond = threading.Condition(self.lock)
    
    def update_programStatus(self, programStatus):
        """
        更新程序执行的状态
        """
        with self.lock:
            self.programStatus = programStatus
            self.cond.notify_all()

    def get_programStatus(self):
        """
        得到程序执行的状态
        ps: str 为 immutable 类型, 所以不需要考虑deepcopy
        """
        with self.lock:
            return self.programStatus
    
    def reset_programStatus(self):
        """
        重置程序执行的状态
        """
        with self.lock:
            self.programStatus = ""  
            self.cond.notify_all()


class ElevatorControl:
    def __init__(self):
        """
        用来记录机器人与电梯进行交互时需要的状态以及相关数据
        包括:
            status: 目前电梯的执行状态
            robotId: 机器人ID
            taskId: 正在执行的任务ID
            house: 现在机器人所在的楼
            fromFloor: 机器人出发楼层
            toFloor: 机器人要走到的楼层
            fromElevatorOutAddress: 要走到的电梯门口的点位
            fromElevatorInAddress: 要走到店内内部的点位
            toElevatorOutAddress: 没什么用
            toElevatorInAddress: 要重定位的点位
        """
        self.lock = threading.Lock()

        self.elevatorControlParams = {
            "status": 0,
            "robotId": 0,
            "taskId": 0,
            "house": "",
            "fromFloor": "",
            "toFloor": "",
            "fromElevatorOutAddress": {},
            "fromElevatorInAddress": {},
            "toElevatorOutAddress": {},
            "toElevatorInAddress": {}
        }

    def get_elevatorControlParams(self):
        """
        获得当前用于电梯的详细信息
        """
        with self.lock:
            return copy.deepcopy(self.elevatorControlParams)
        
    def update_basicInfo(self, robotId, taskId):
        """
        用于更新机器人基本信息
        """
        with self.lock:
            self.elevatorControlParams["robotId"] = robotId
            self.elevatorControlParams["taskId"] = taskId

    def update_elevatorStatus(self, elevatorStatus):
        """
        用于更新电梯的现在的状态
        """
        with self.lock:
            self.elevatorControlParams["status"] = elevatorStatus

    def update_floorInfo(self, fromFloor, toFloor):
        """
        用于更新机器人要从哪层(fromFloor)到哪层(toFloor)
        """
        with self.lock:
            self.elevatorControlParams["fromFloor"] = fromFloor
            self.elevatorControlParams["toFloor"] = toFloor

    def update_fromElevatorOutAddress(self, fromElevatorOutAddress):
        """
        用于更新机器人要上的电梯的外部坐标信息
        """
        with self.lock:
            self.elevatorControlParams["fromElevatorOutAddress"] = fromElevatorOutAddress

    def update_fromElevatorInAddress(self, fromElevatorInAddress):
        """
        用于更新机器人要上的电梯的外部坐标信息
        """
        with self.lock:
            self.elevatorControlParams["fromElevatorInAddress"] = fromElevatorInAddress

    def update_toElevatorOutAddress(self, toElevatorOutAddress):
        """
        用于更新机器人要上的电梯的外部坐标信息
        """
        with self.lock:
            self.elevatorControlParams["toElevatorOutAddress"] = toElevatorOutAddress

    def update_toElevatorInAddress(self, toElevatorInAddress):
        """
        用于更新机器人要上的电梯的外部坐标信息
        """
        with self.lock:
            self.elevatorControlParams["toElevatorInAddress"] = toElevatorInAddress

    def reset_elevatorControlParams(self):
        """
        任务结束后清空记录
        """
        with self.lock:
            self.elevatorControlParams = {
                "status": 0,
                "robotId": 0,
                "taskId": 0,
                "house": "ntuitive",
                "fromFloor": "",
                "toFloor": "",
                "fromElevatorOutAddress": {},
                "fromElevatorInAddress": {},
                "toElevatorOutAddress": {},
                "toElevatorInAddress": {}
            }


class Signal:
    """
    好像没用来着....
    """
    def __init__(self):
        self.lock = threading.lock()
        self.signal = ""

    def update_signal(self, signal):
        with self.lock:
            self.signal = signal

    def get_signal(self):
        with self.lock:
            return self.signal
    
    def reset_signal(self):
        with self.lock:
            self.signal = ""