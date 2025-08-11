import requests
from enum import Enum
import time
import secrets
import hashlib
import json
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

#connection detailed parameters
HEAD = "http" #protocol
HOST = "10.25.0.15" #backend ip address
PORT = 18001 #backend port
BASE_URL = f"{HEAD}://{HOST}:{PORT}"

class TaskStatus(Enum):
    PENDING_RECEIPT = 40 #待签收
    DELIVERY_FAILED = 50 #配送失败
    DELIVERY_COMPLETE = 70 #配送完成

def md5_hex(s: str) -> str:
    return hashlib.md5(s.encode("utf-8")).hexdigest()

def build_auth_headers(robot_id: int, private_key: str) -> dict:
    R = secrets.token_hex(8)
    T = int(time.time()*1000)
    sign_str = f"{R}:{T}:{ROBOT_ID}:{private_key}"
    S = md5_hex(sign_str)
    return {
        "R": R,
        "T": str(T),
        "S": S,
        "Robot-Id": ROBOT_ID,
        "Content-Type": "application/json",
        "App-Id": "robot"
    }


def aes_cbc_decrypt(cipher_bytes: bytes, key: bytes, iv: bytes) -> bytes:
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(cipher_bytes), AES.block_size)

def aes_cbc_encrypt(plaintext: bytes, key: bytes, iv: bytes) -> bytes:
    #创建AES加密器, 模式为CBC
    cipher = AES.new(key, AES.MODE_CBC, iv)
    #返回密文, 如果加密长度不是16字节的倍数, 要用PKCS#7规则填充
    return cipher.encrypt(pad(plaintext, AES.block_size))


def encrypted_data(payload: dict):
    #首先把字典转为json字符串, 然后再转为字节串
    plaintext = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    #AES CBC 加密字节串得到密文
    cipher_bytes = aes_cbc_encrypt(plaintext, KEY, IV)
    #把密文转为可传输的字符串
    cipher_b64 = base64.b64encode(cipher_bytes).decode("ascii")
    return cipher_b64


def decrypt_response_data(data_b64: str) -> dict:
    cipher_bytes = base64.b64decode(data_b64)
    plain = aes_cbc_decrypt(cipher_bytes, KEY, IV)
    return json.loads(plain.decode("utf-8"))


def select_taskInfo():
    """
        接口1: 机器人主动获取任务信息
    """
    url = "http://10.25.0.15:18001/api/robot/client/selectTaskInfo"

    payload = {"taskId": 1234}
    data = encrypted_data(payload)
    body = {"data": data}

    #只发一次
    for i in range(1):
        try: 
            #每次发送都更新header
            HEADER = build_auth_headers(ROBOT_ID, PRIVATE_KEY)
            print("\n", HEADER, data, "\n\n")
            response = requests.post(url = url, headers = HEADER, json = body, timeout = 20)

            if response.ok:
                print(response.status_code)
                # 获取到相关data然后解析数据
                print(response.json())
                """
                data = response.json().get("data")
                result = decrypt_response_data(data)
                print(result)

                return result
                """
            
            else:
                print(f"第{i}次请求后台主动获取任务信息失败, 状态码: {response.status_code}")
        
        except requests.RequestException as e:
            print(f"第{i}次请求异常: {e}")

        time.sleep(2) #间隔两秒再试一次
    
    print("需要检查网络或后台状态")
    return None

"""
def update_taskStatus(taskStatus):
    
        接口2,3,4: 机器人主动向后台更新任务进度
        parameters:
            taskStatus: the number represents the status of the task.
    
    url = f"{BASE_URL}/api/JKROBOT/{ROBOT_ID}/reportTaskProcess"

    payload = {
        "taskId": 1234,
        "taskStatus": taskStatus, 
        "step": "step"
    }
    data = encrypted_data(payload)

    if taskStatus != 40:
        #对于接口3和4 请求失败要重试
        for i in range(5):
            try:
                HEADER = build_auth_headers(ROBOT_ID, PRIVATE_KEY)
                response = requests.post(url = url, headers = HEADER, json = data,timeout = 5)
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
        HEADER = build_auth_headers(ROBOT_ID, PRIVATE_KEY)
        response = requests.post(url = url, headers = HEADER, json = data, timeout = 5)
        return response.ok
"""

if __name__ == "__main__":
    #robot parameter
    ROBOT_ID = "18950214603"
    PRIVATE_KEY = "z/CszPJh61yWfA1eJhmDKg=="
    IV_VECTOR = "tBPz/vp+8x9ps4ikCj6btA=="
    KEY = base64.b64decode(PRIVATE_KEY)
    IV = base64.b64decode(IV_VECTOR)
    print(len(KEY), len(IV))

    try:
        select_taskInfo()
        """
        while True:
            select_taskInfo()
            time.sleep(3)
            """
    except KeyboardInterrupt:
        print("exiting")


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
