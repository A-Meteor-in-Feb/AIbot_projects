import time
import schedule
from types import SimpleNamespace
import hashlib
import requests
import uuid
import json


# 全局变量
baseScope = SimpleNamespace(
    robotId=18950214603,
    apiKey="z/CszPJh61yWfA1eJhmDKg==",
    apiIv="tBPz/vp+8x9ps4ikCj6btA==",
    status=None,
    currentAddress=None,
    lastAddress=None,
    addressList=None,
    addressListd=None,
    taskInfo=None,
    elevatorFlowInfo=None,
    commandInfo=None,
)


def get_current_milliseconds():
    return int(time.time() * 1000)


def str_to_md5(input_str):
    md5_hash = hashlib.md5()
    encoded_str = input_str.encode("utf-8")
    md5_hash.update(encoded_str)
    md5_hex = md5_hash.hexdigest()
    return md5_hex


def requestToBackendServer(url, params):
    r = str(uuid.uuid4()).replace("-", "")
    t = str(get_current_milliseconds())
    s = str_to_md5(f"{r}:{t}:{baseScope.robotId}:{baseScope.apiKey}")
    response = requests.post(
        "http://10.25.0.15:18001" + url,
        headers={
            "R": r,
            "T": t,
            "S": s,
            "App-Id": "robot",
            "Robot-Id": str(baseScope.robotId),
        },
        json=params,
    )
    print("requestToBackendServer", url, response.status_code, response.text)
    resp = json.loads(response.text)
    code = resp.get("code")
    msg = resp.get("msg")
    data = resp.get("data")
    if code != 0:
        raise Exception(code, msg)
    return data


# 设置电梯流程信息
def setElevatorFlowInfo(params):
    print("setElevatorFlowInfo")
    return requestToBackendServer(
        "/api/robot/client/setElevatorFlowInfo",
        {
            **params,
        },
    )["flowInfo"]


# 获取电梯流程信息
def getElevatorFlowInfo():
    if baseScope.elevatorFlowInfo == None:
        return
    elevatorFlowInfo = requestToBackendServer(
        "/api/robot/client/setElevatorFlowInfo",
        {
            "flowId": baseScope.elevatorFlowInfo["flowId"],
        },
    )["flowInfo"]


# 向机器人发送位置
def sendAddressToRobot(address):
    print("sendAddressToRobot", address)


# 向机器人发送重定位位置
def sendResetAddressToRobot(address):
    print("sendResetAddressToRobot", address)


# 重置机器人状态
def cleanBaseScope():
    baseScope.taskInfo = None
    baseScope.addressList = None
    baseScope.addressListd = []
    baseScope.commandInfo = None
    baseScope.elevatorFlowInfo = None


# 主动切换机器人状态
def switchStatus(status, addressList=None, taskInfo=None):
    print("switchStatus", status, addressList, taskInfo)
    cleanBaseScope()
    baseScope.status = status
    if status == "task":
        baseScope.taskInfo = taskInfo
        baseScope.addressList = addressList
        startNavigation()
    elif status == "back":
        baseScope.addressList = addressList
        startNavigation()


# 主动切换任务状态
def switchTaskStatus(taskStatus, taskInfo=None):
    print("switchTaskStatus", taskStatus, taskInfo)
    fromTaskStatus = (
        baseScope.taskInfo["status"] if baseScope.taskInfo != None else None
    )
    if fromTaskStatus == taskInfo["status"]:
        return
    baseScope.taskInfo = taskInfo
    requestToBackendServer(
        "/api/reportTaskPresses",
        {
            "taskId": baseScope.taskInfo["id"],
            "taskStatus": taskStatus,
        },
    )


# 启动电梯流程
def startElevatorFlow(fromAddress, toAddress):
    print("startElevatorFlow")
    flowId = str(uuid.uuid4()).replace("-", "")
    elevatorFlowInfo = setElevatorFlowInfo(
        {
            "flowId": flowId,
            "robotId": baseScope.robotId,
            "house": fromAddress.house,
            "fromFloor": fromAddress.floor,
            "toFloor": toAddress.floor,
            "status": 0,
        }
    )
    baseScope.elevatorFlowInfo = elevatorFlowInfo
    sendAddressToRobot(baseScope.elevatorFlowInfo["fromElevatorOutAddress"])
    switchElevatorFlowStatus(10)


# 切换电梯流程状态
def switchElevatorFlowStatus(flowStatus, flowInfo):
    print("switchElevatorFlowStatus", flowStatus, flowInfo)
    if baseScope.elevatorFlowInfo == None:
        return
    if flowStatus != baseScope.elevatorFlowInfo["status"]:
        return
    if flowStatus == 10:
        sendAddressToRobot(baseScope.elevatorFlowInfo["fromElevatorOutAddress"])

    if flowStatus == 40:
        sendAddressToRobot(baseScope.elevatorFlowInfo["fromElevatorInAddress"])
    if flowStatus == 80:
        sendResetAddressToRobot(baseScope.elevatorFlowInfo["fromElevatorInAddress"])


# 切换电梯
def switchElevatorFlowAddress():
    print("handleElevatorFlowAddress")
    if baseScope.elevatorFlowInfo == None:
        return


# 处理电梯流程结束逻辑
def handleElevatorFlowEnd():
    print("handleElevatorFlowEnd")
    baseScope.elevatorFlowInfo = None
    sendNextAddressToRobot()


# 获取任务信息
def requestTaskInfo():
    if (
        baseScope.status == "exce"
        or baseScope.status == "comm"
        or baseScope.elevatorFlowInfo != None
    ):
        return
    print("requestTaskInfo")
    data = requestToBackendServer(
        "/api/robot/client/selectTaskInfo",
        {
            "taskId": (
                baseScope.taskInfo["id"] if baseScope.status == "task" else None
            ),
        },
    )
    addressList = data["addressList"] if "addressList" in data else None
    taskInfo = data["taskInfo"] if "taskInfo" in data else None
    if baseScope.status == "task":
        # 任务丢失
        if taskInfo == None:
            switchStatus("back", addressList=addressList)
        # 是当前任务
        if taskInfo["id"] == baseScope.taskInfo["id"]:
            # 任务被取消
            if taskInfo["status"] not in [30, 40, 90]:
                switchStatus("back", addressList=addressList)
            if taskInfo["status"] > baseScope.taskInfo["status"]:
                switchTaskStatus(taskInfo["status"], taskInfo)

    elif taskInfo != None:
        switchStatus("task", addressList=taskInfo["addressList"], taskInfo=taskInfo)
    elif baseScope.status == None:
        switchStatus("back", addressList=addressList)


# 收到机器人到达信号
def handleRobotArrive(address):
    print("handleRobotArrive")
    baseScope.addressListd.append(address)
    if baseScope.elevatorFlowInfo != None:
        if baseScope.elevatorFlowInfo["status"] == 10:
            switchElevatorFlowStatus(20)
        if baseScope.elevatorFlowInfo["status"] == 50:
            switchElevatorFlowStatus(60)
    sendNextAddressToRobot()


# 收到机器人重置成功信号
def handleRobotReset():
    print("handleRobotReset")
    if (
        baseScope.elevatorFlowInfo != None
        and baseScope.elevatorFlowInfo["status"] == 80
    ):
        if baseScope.elevatorFlowInfo != None:
            if baseScope.elevatorFlowInfo["status"] == 90:
                switchElevatorFlowStatus(100)


# 向机器人发送下一个位置
def sendNextAddressToRobot():
    nextAddress = getNextAddress()
    if nextAddress != None:
        # todo：这里要判断是否需要做电梯
        sendAddressToRobot(nextAddress)
    else:
        handleNavigationEnd()


# 开始导航
def startNavigation():
    print("startNavigation")
    sendNextAddressToRobot()


# 处理导航结束逻辑
def handleNavigationEnd():
    print("handleNavigationEnd")
    if baseScope.status == "task":
        switchTaskStatus(40)
    elif baseScope.status == "back":
        switchStatus("idle")


# 获取下一地址
def getNextAddress():
    for address in baseScope.addressList:
        if address in baseScope.addressListd:
            return address


# 收到扫描二维码信号
def handleQrCoode(code):
    if (
        baseScope.status != "task"
        or baseScope.taskInfo == None
        or baseScope.taskInfo["status"] != 40
    ):
        return
    if code == "123456":
        switchTaskStatus(50)
        # todo: 吐货
        time.sleep(60)


if __name__ == "__main__":
    schedule.every(5).seconds.do(requestTaskInfo)
    schedule.every(1).seconds.do(getElevatorFlowInfo)

    while True:
        schedule.run_pending()
        time.sleep(1)
