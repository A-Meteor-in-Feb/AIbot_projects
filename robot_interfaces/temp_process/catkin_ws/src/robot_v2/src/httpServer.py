from flask import Flask
from flask import request
from flask import jsonify
from flask import Blueprint
from flask import abort
import secrets
import hashlib
import json
import base64
from Crypto.Cipher import AES 
from Crypto.Util.Padding import pad, unpad
import time


def now_ms() -> int:
    return int(time.time() * 1000)

class HttpServer:
    def __init__(self, state, head: str, host: str, port: str, robotId: str, private_key: str, iv_vector: str, skew_ms: int):
        """
        用于接收后台发来的请求.
        参数:
            head: url的协议, http或者https.
            host: 机器人的host
            port: 机器人的端口
            robotId: 机器人的id号
            private_key: 私钥由后台分布
            iv_vector: iv由后台分布
            skew_ms: 防重放时间
        """
        self.state = state

        self.head = head
        self.host = host
        self.port = port
        self.base_url = f"{self.head}://{self.host}:{self.port}"
        self.skew_ms = skew_ms

        self.robotId = robotId
        self.private_key = private_key
        self.iv_vector = iv_vector
        self.key = base64.b64decode(self.private_key)
        self.iv = base64.b64decode(self.iv_vector)

        self.bp = Blueprint("robot_api", __name__)
        self.bp.add_url_rule(
            "/api/robot/server/task",
            view_func=self.handle_task,
            methods = ["POST"]
        )

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
        plain = self.aes_cbc_decrypt(cipher_bytes, self.key, self.iv)
        return json.loads(plain.decode("utf-8"))
    
    def verify_headers(self, headers):
        """
        校验规则与客户端一致：
        S = md5(f"{R}:{T}:{robotId}:{private_key_b64_string}")
        并检查时间戳 T 与当前时间差不超过 skew_ms
        """
        R = headers.get("R")
        T = headers.get("T")
        S = headers.get("S")
        rid = headers.get("Robot-Id")

        if not all([R, T, S, rid]):
            abort(self.make_error(401, "Missing auth headers"))

        if rid != self.robotId:
            abort(self.make_error(401, "Robot-Id mismatch"))

        # 时间戳检查
        try:
            T = int(T)
        except ValueError:
            abort(self.make_error(401, "Invalid T header"))
        if abs(now_ms() - T) > self.skew_ms:
            abort(self.make_error(401, "Timestamp skew too large"))

        # 重新计算签名
        sign_str = f"{R}:{T}:{rid}:{self.private_key_b64}"
        calc = self.md5_hex(sign_str)
        if calc != S:
            abort(self.make_error(401, "Signature invalid"))
    
    def handle_task(self):
        """
        机器人做server, 接收后台请求并响应.
        """
        #headers = request.headers
        #然后就要检验头部
        #self.verify_headers(headers)
        data = request.get_json()
        print(data)
        #data = request.get_data().decode("utf-8")
        #result = self.decrypt_response_data(data)
        # TODO - 这个地方根据字段来做判断吧, 如果已经更新字段了, 就判断信息一不一致
        # 如果httpClient那边还没有更新到相关字段, 就直接赋值
        status = data.get("taskInfo").get("status")
        if status == 20:
            print(f"后台发送请求, 状态码为20")
            return jsonify({"status":"ok"}), 200
        elif status == 60:
            print("收到取消取消取消请求")
            #self.state.update_taskStatus("returning")
            #self.state.update_taskId(0)
            return jsonify({"status":"ok"}), 200
            
        return jsonify({"status":"ok"}), 200

        


    def make_error(self, status_code: int, message: str):
        # 使用 abort(xxx) 时调用
        response = jsonify({"code": status_code, "error": message})
        response.status_code = status_code
        return response

