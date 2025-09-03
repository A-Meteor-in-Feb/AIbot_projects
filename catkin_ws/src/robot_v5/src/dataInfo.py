from datetime import datetime
from enum import Enum
import threading
import copy

def utc_now_ms():
    now = datetime.now()
    timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")
    return timestamp_str

class TaskStatus(Enum):
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
            "floor": "2m",
            "house": "ntuitive",
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
        
        with self.lock:
            self.robotState["fault"] = b_fault
        """

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
        with self.lock:
            return self.command
        
    def update_command(self, commandContent):
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
        with self.lock:
            self.command = ""
    

class ProgramStatus:
    def __init__(self):
        """
        用来记录程序执行的状态
        """
        self.lock = threading.Lock()
        self.programStatus = ""
    
    def update_programStatus(self, programStatus):
        """
        更新程序执行的状态
        """
        with self.lock:
            self.programStatus = programStatus

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


class ElevatorControl:
    def __init__(self):
        self.lock = threading.Lock()

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