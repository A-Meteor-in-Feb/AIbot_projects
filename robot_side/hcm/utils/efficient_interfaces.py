from dataclasses import dataclass

@dataclass
class Position:
    x: float
    y: float
    z: float
    accuracy: float


def readPositionSensors() -> Position:
    # 从硬件处获得数值
    x_val = 1.1
    y_val = 1.2
    z_val = 1.3
    acc_val = 0.1
    return Position(x_val, y_val, z_val, acc_val)

@dataclass
class Battery:
    level: int
    voltage: float
    current: float
    temperature: float
    charging: bool
    estimated_runtime: int

def readBatteryInfo() -> Battery:
    #从硬件处获得数值
    level = 87
    voltage = 24.2
    current = 1.5
    temperature = 35.0
    charging = False
    estimated_runtime = 180