import requests
from enum import Enum
import time

#connection detailed parameters
HEAD = "http" #protocol
HOST = "127.0.0.1" #backend ip address
PORT = 8888 #backend port
BASE_URL = f"{HEAD}://{HOST}:{PORT}"

#robot parameter
ROBOT_ID = "robot01"

"""要不要加headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer xxxxxx"
    }
"""


class TaskStatus(Enum):
    PENDING_RECEIPT = 40 #待签收
    DELIVERY_FAILED = 50 #配送失败
    DELIVERY_COMPLETE = 70 #配送完成


def select_taskInfo():
    """
        接口1: 机器人主动获取任务信息
    """
    url = f"{BASE_URL}/api/JKROBOT/{ROBOT_ID}/selectTaskInfo"

    payload = {"taskId": 1234}

    for i in range(5):
        try: 
            response = requests.post(url = url,json = payload,timeout = 5)

            if response.ok:
                # 获取到相关data然后解析数据
                data = response.json()
                return data
            else:
                print(f"第{i}次请求后台主动获取任务信息失败, 状态码: {response.status_code}")
        
        except requests.RequestException as e:
            print(f"第{i}次请求异常: {e}")

        time.sleep(2) #间隔两秒再试一次
    
    print("需要检查网络或后台状态")
    return None


def update_taskStatus(taskStatus):
    """
        接口2,3,4: 机器人主动向后台更新任务进度
        parameters:
            taskStatus: the number represents the status of the task.
    """
    url = f"{BASE_URL}/api/JKROBOT/{ROBOT_ID}/reportTaskProcess"

    payload = {
        "taskID": 1234,
        "taskStatus": taskStatus, 
        "step": "step"
    }

    if taskStatus != 40:
        #对于接口3和4 请求失败要重试
        for i in range(5):
            try:
                response = requests.post(url = url,json = payload,timeout = 5)
                if not response.ok:
                    print(f"第{i}次向后台更新任务进度失败, 状态码: {response.status_code}")
                else:
                    return response.ok
            except requests.RequestException as e:
                print(f"第{i}次请求异常: {e}")

            time.sleep(2) #间隔两秒再试一次

        print("需要检查网络或后台状态")
        return None
    else:
        #接口2 请求失败不需要重试
        response = requests.post(url = url,json = payload,timeout = 5)
        return response.ok


if __name__ == "__main__":
    print(1)
    # 机器人在哪一步获取任务信息 (调用接口1) 呢???

    # a - 机器人到达收货地点
    # 你怎么判断机器人到达收货地点? 
    # 用位置 -- ROS话题接收到位置信息, 如果与goal位置一样, 则由delivering更新为arrived
    # 先发送MQTT 状态消息给后台, 
    # 然后再调用这个<接口2>  update_taskStatus(TaskStatus.PENDING_RECEIPT.value)
    # 同时进行步骤2


    # b - 之后就开始计时, 并开始扫描核对二维码, 如果二维码检验成功, 则开仓转54行, 否则转55行.
    # 假设检验成功了, 这个时候就是送货成功, 机器人状态更新为 delivered/idle.
    # 然后调用<接口3> update_taskStatus(TaskStatus.DELIVERY_FAILED.value)
    # 假设没有验证成功, 或者一直都读不到验证码, 根据时间判断是不是调用接口4
    # 时间到时 则调用<接口4> update_taskStatus(TaskStatus.DELIVERY_FAILED.value)


    # c - 机器人调用接口2通知后台已到达 
    # 这个地方有问题, 假设是在断网的情况下发的request, 后台没有收到怎么办, 
    # 所以判断取货是否超时的逻辑就不能通过这个接口的response来开始计时
