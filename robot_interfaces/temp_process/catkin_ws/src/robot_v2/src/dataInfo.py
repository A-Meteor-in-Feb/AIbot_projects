from datetime import datetime
import threading
import copy


def utc_now_ms():
    now = datetime.now()    
    timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")
    return timestamp_str


class StateInfo:
    def __init__(self):
        self.lock = threading.Lock()
        self.state = {
            "position": {"x": 0, "y": 0, "theta": 0},
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

    #def 