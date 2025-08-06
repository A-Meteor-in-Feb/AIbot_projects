from datetime import datetime
from datetime import timezone

def getCurrentPosition():
    position = {
        "x": 12.34,
        "y": 5.67,
        "z": 0.00,
        "accuracy": 0.5
    }
    return position

def getBatteryStatus():
    battery = {
        "level": 87,
        "voltage": 24.2,
        "current": 1.5,
        "temperature": 35.0,
        "charging": False,
        "estimated_runtime": 180
    }
    return battery

def getAllSensorStatus():
    lidars = {
        "status": "active",
        "range": 10.5,
        "last_update": "2025-08-02T12:00:00Z"
    }
    camera = {
        "status": "active",
        "resolution": "1080p",
        "last_update": "2025-08-02T12:00:00Z"
    }
    imu = {
        "status": "active",
        "orientation": {
            "roll": 0.1,
            "pitch": 0.2,
            "yaw": 45.0
        },
        "last_update": "2025-08-02T12:00:00Z"
    }
    sensors = {
        "lidars": lidars,
        "camera": camera,
        "imu": imu
    }
    return sensors

def getMotionStatus():
    motion = {
        "moving": False,
        "speed": 0.0,
        "direction": 0.0,
        "target_position": None
    }
    return motion

def checkSystemFault():
    return False

def getCurrentTimestamp():
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-4]+"Z"
    return timestamp