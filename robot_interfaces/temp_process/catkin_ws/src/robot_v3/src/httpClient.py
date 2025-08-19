import json
import dataInfo
import uuid
import requests
import encryption
import time
from pathlib import Path
import base64

class HttpClient:
    def __init__(self, head, host, port, httpEncryption: encryption.HttpEncryption):
        """
        机器人客户端初始化.
        目的: 方便机器人随时调用向后台发送请求的接口.
        """
        self.base_url = f"{head}://{host}:{port}"
        self.retries = 5
        self.httpEncyption = httpEncryption


    def post_request(self, url, data):
        """
        功能函数: 用于发送各种post请求
        参数:
            url: 不同接口的地址
            data: 不同请求的对应请求体数据(加密/不加密均可)
        """
        resp_code = None

        for i in range(self.retries):
            try:
                header = self.httpEncyption.build_auth_headers()

                response = requests.post(url=url, headers=header, json=data, timeout=10)

                if response.ok:
                    #需要解密
                    #data = response.text
                    #result = self.httpEncyption.decrypt_response_data(data)
                    #不需要解密
                    result = response.json()
                    return result
                #这里的情况包括服务器端各种异常比如 500, 404, 401 等等
                else:
                    resp_code = response.status_code
                    print(f"第{i}次 [主动获取任务信息] 失败, 状态码: {response.status_code}")
            
            #网络异常、请求超时等等 网络错误
            except requests.RequestException as e:
                print(f"第{i}次调用接口异常: {e}")

            time.sleep(2) #间隔两秒再试一次

        print("需要检查网络或后台状态")
        self.report_httpError(code=resp_code)

        return None


    def select_taskInfo(self, taskId):
        """
        接口1: 机器人主动获取任务信息
        返回值:
            正常情况下: 会返回后台响应数据, 且数据类型为dict; 可以在executor.py中直接使用, 无需类型转换.
            异常情况下: 尝试从后台获取任务信息连续5次都失败, 返回None; 供executor.py中主逻辑做异常判断
        """
        url = f"{self.base_url}/api/robot/client/selectTaskInfo"

        uuid_str = str(uuid.uuid4())
        payload = {
            "taskId": taskId,
            "timestamp": dataInfo.utc_now_ms(),
            "uuid": uuid_str
        }

        #加密
        encypted_payload = self.httpEncyption.encrypted_data(payload)
        data = {"data": encypted_payload}

        response = self.post_request(url=url, data=data)
        print("\n send request \n")
        #正常情况
        if response:
            return response
        # 发生错误
        else:
            return None
    

    def update_taskStatus(self, taskId, taskStatus):
        """
        接口2: 机器人向后台更新任务进度
        参数:
            taskId: 目前的任务id
            taskStatus: 目前任务状态
        返回:
            正常情况下成功响应
            异常情况下...
        """
        url = f"{self.base_url}/api/robot/client/reportTaskProcess"

        uuid_str = str(uuid.uuid4())
        payload = {
            "taskId": taskId,
            "taskStatus": taskStatus,
            "step": "step",
            "timestamp": dataInfo.utc_now_ms(),
            "uuid": uuid_str
        }

        #加密
        encypted_payload = self.httpEncyption.encrypted_data(payload)
        data = {"data": encypted_payload}

        response = self.post_request(url=url, data=data)

        if response:
            return response
        else:
            return None
    

    def report_image(self):
        """
        接口3: 机器人主动向后台上传关键节点的图像
        (也就是说到了关键节点你要自己主动控制摄像头拍照然后上传到后台)
        (TODO: 判断关键节点 -> 控制摄像头拍照 -> 上传给后台)
        """
        url = f"{self.base_url}/api/robot/client/reportRobotCollect"

        image_bytes = Path("images/deliver.jpg").read_bytes()
        image_base64 = base64.b64encode(image_bytes).decode("ascii")
        timestamp = dataInfo.utc_now_ms()
        uuid_str = str(uuid.uuid4())

        payload = {
            "type": "image",
            "data": image_base64,
            "timestamp": timestamp,
            "uuid": uuid_str
        }

        #加密
        encrypted_payload = self.httpEncyption.encrypted_data(payload)
        data = {"data": encrypted_payload}

        response = self.post_request(url=url, data=data)

        if response:
            return response
        else:
            return None


    def report_video(self):
        """
        接口4: 机器人主动向后台上传相关视频
        (也就是说到了关键节点你要自己主动控制摄像头开始拍视频然后上传到后台)
        (TODO: 判断关键节点 -> 控制摄像头拍视频 -> 上传给后台)
        
        这个接口里的具体请求参数定义 TODO !!!!!!
        """
        url = f"{self.base_url}/api/robot/client/reportRobotCollect"     

        payload = {
            "type": "video"
        }


    def report_httpError(self, code):
        """
        接口5: 机器人主动向后台上报 HTTP 错误???
        有点疑惑, 这个接口为什么要这样定义? 定义这个接口有什么用呢?
        """
        url = f"{self.base_url}/api/robot/client/reportRobotCollect"
        
        payload = {
            "type": "error",
            "code": code
        }

        #然后加密传输??????我的老天奶
        


    def report_warn(self, taskId, type):
        """
        接口6: 当机器人遇到需要人为干预才能解决的故障时, 调用这个接口上报故障
        参数:
            taskId: 正在执行的任务id, 如果没有就是0, 如果有的话后台会直接把这个任务停掉
            type: 需要人为帮助的类型, 英文传输喔
        """ 
        url = f"{self.base_url}/api/robot/client/reportRobotWarn"

        timestamp = dataInfo.utc_now_ms()
        uuid_str = str(uuid.uuid4())
        
        payload = {
            "taskId": taskId,
            "type": type,
            "timestamp": timestamp,
            "uuid": uuid_str
        }

        #加密
        encrypted_payload = self.httpEncyption.encrypted_data(payload)
        data = {"data": encrypted_payload}

        response = self.post_request(url=url, data=data)

        if response:
            return response
        else:
            return None
        
"""
if __name__ == "__main__":
    #后台指定的参数
    ROBOTID = "18950214603"
    PRIVATE_KEY = "z/CszPJh61yWfA1eJhmDKg=="
    IV_VECTOR = "tBPz/vp+8x9ps4ikCj6btA=="

    #控制参数
    HEARTBEAT = 5 #控制MQTT 状态话题的周期性发送

    #连接参数
    BROKER_HOST = "10.25.0.2"
    BROKER_PORT = 1883
    HTTP_HEAD = "http"
    BACKEND_HOST = "10.25.0.15"   # "192.168.10.249"
    BACKEND_PORT = "18001"        # "8889"

    httpEncryption = encryption.HttpEncryption(robotId=ROBOTID, private_key=PRIVATE_KEY, iv_vector=IV_VECTOR)

    httpClient = HttpClient(head=HTTP_HEAD, host=BACKEND_HOST, port=BACKEND_PORT, httpEncryption=httpEncryption)

    httpClient.select_taskInfo(19908332614)
"""