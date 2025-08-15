import requests
import secrets
import hashlib
import json
import base64
from Crypto.Cipher import AES 
from Crypto.Util.Padding import pad, unpad
import dataInfo
import time


class HttpClient:
    def __init__(self, head: str, host: str, port: str, robotId: str, private_key: str, iv_vector: str):
        self.head = head
        self.host = host
        self.port = port
        self.base_url = f"{self.head}://{self.host}:{self.port}"

        self.robotId = robotId
        self.private_key = private_key
        self.iv_vector = iv_vector
        self.key = base64.b64decode(self.private_key)
        self.iv = base64.b64decode(self.iv_vector)


    def md5_hex(self, s: str) -> str:
        """
        把字符串 s 转换成它的 MD5 摘要 (32位十六进制字符串)
        参数:
            s: string
        """
        return hashlib.md5(s.encode("utf-8")).hexdigest()
    
    def build_auth_headers(self) -> dict:
        """
        生成用于鉴权的 HTTP 头部
        返回:
            一个dict, 包含头部所需要的所有字段
        """
        R = secrets.token_hex(8)
        T = int(time.time()*1000)
        sign_str = f"{R}:{T}:{self.robotId}:{self.private_key}"
        S = self.md5_hex(sign_str)
        return {
            "R": R,
            "T": str(T),
            "S": S,
            "Robot-Id": self.robotId,
            "Content-Type": "application/json",
            "App-Id": "robot"
        }
    
    def aes_cbc_encrypt(self, plaintext: bytes) -> bytes:
        """
        利用 key 和 iv 将明文(plaintext)加密为密文并返回
        参数:
            plaintext: bytes, 需要被加密的明文
        """
        #创建AES加密器, 模式为CBC
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        #返回密文, 如果加密长度不是16字节的倍数, 要用PKCS#7规则填充
        return cipher.encrypt(pad(plaintext, AES.block_size))
    
    def encrypted_data(self, payload: dict):
        """
        将需要传输到后台的明文加密
        参数:
            payload: dict, HTTP json 部分明文
        """
        #首先把字典转为json字符串, 然后再转为字节串
        plaintext = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        #AES CBC 加密字节串得到密文
        cipher_bytes = self.aes_cbc_encrypt(plaintext)
        #把密文转为可传输的字符串
        cipher_b64 = base64.b64encode(cipher_bytes).decode("ascii")
        return cipher_b64
    
    def aes_cbc_decrypt(self, cipher_bytes: bytes) -> bytes:
        """
        将后台传输的密文解密为明文
        """
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        return unpad(cipher.decrypt(cipher_bytes), AES.block_size)

    def decrypt_response_data(self, data_b64: str) -> dict:
        """
        将后台传输的密文解密为明文后再转为dict类型
        """
        cipher_bytes = base64.b64decode(data_b64)
        plain = self.aes_cbc_decrypt(cipher_bytes)
        return json.loads(plain.decode("utf-8")) 
    
    def select_taskInfo(self):
        """
        接口1: 机器人主动获取任务信息
        返回值:
            正常情况下: 会返回后台响应数据, 且数据类型为dict; 可以在executor.py中直接使用, 无需类型转换.
            异常情况下: 尝试从后台获取任务信息连续5次都失败, 返回None; 供executor.py中主逻辑做异常判断
        """
        url = f"{self.base_url}/api/robot/client/selectTaskInfo"

        payload = {"taskId": 19582642036}
        data = self.encrypted_data(payload)
        body = {"data": data}

        #只发一次
        for i in range(1):
            try: 
                #每次发送都更新header
                HEADER = self.build_auth_headers()
                response = requests.post(url = url, headers = HEADER, json = body, timeout = 1)
                #response = requests.post(url = url, json = body, timeout = 1)

                if response.ok:
                    print(response.status_code)
                    # 获取到相关data然后解析数据
                    data = response.text
                    print(data)
                    result = self.decrypt_response_data(data)
                    #result = response.json()
                    print(result)
                    return result
                        
                else:
                    print(f"第{i}次请求后台主动获取任务信息失败, 状态码: {response.status_code}")
        
            except requests.RequestException as e:
                print(f"第{i}次请求异常: {e}")

            time.sleep(2) #间隔两秒再试一次
    
        print("需要检查网络或后台状态")
        return None

    def update_taskStatus(self, taskId, taskStatus):
        """
        接口2,3,4: 机器人主动向后台更新任务进度
        参数:
            taskStatus: 代表不同任务执行情况的数字值
        返回:
            正常情况下成功响应:
            异常情况下: 
        """
        url = f"{self.base_url}/api/robot/client/reportTaskProcess"

        payload = {
            "taskId": taskId,
            "taskStatus": taskStatus, 
            "step": "step",
            "createTime": dataInfo.utc_now_ms()
        }
        data = self.encrypted_data(payload)
        body = {"data": data}

        #请求失败要重试
        for i in range(5):
            try:
                HEADER = self.build_auth_headers()
                response = requests.post(url = url, headers = HEADER, json = body, timeout = 5)
                #response = requests.post(url = url, json = body, timeout = 5)
                if not response.ok:
                    print(f"第{i}次向后台更新任务进度失败, 状态码: {response.status_code}")
                else:
                    print(response)
                    return response.ok
            except requests.RequestException as e:
                print(f"第{i}次请求异常: {e}")

            time.sleep(2) #间隔两秒再试一次

        print("需要检查网络或后台状态")
        return None