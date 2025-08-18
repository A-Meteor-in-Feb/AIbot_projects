import secrets
import hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import time
import base64
import json

class HttpEncryption:
    def __init__(self, robotId, private_key, iv_vector):
        """
        这个类用于给HTTP响应和请求添加头部, 并且将payload加密.
        参数:
            robotId: 机器人编号, 由后台分配
            private_key: 密钥, 由后台分配
            iv_vector: 初始化向量, 由后台分配
        """
        self.robotId = robotId
        self.private_key = private_key
        self.iv_vector = iv_vector
        self.key = base64.b64decode(private_key)
        self.iv = base64.b64decode(iv_vector)

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

    def verify_headers(self, headers):
        """
        校验规则与客户端一致：
        S = md5(f"{R}:{T}:{robotId}:{private_key}")
        参数:
            headers: 后台发送请求携带的header
        """
        R = headers.get("R")
        T = headers.get("T")
        S = headers.get("S")
        rid = headers.get("Robot-Id")

        # 重新计算签名
        sign_str = f"{R}:{T}:{rid}:{self.private_key}"
        cal_sign = self.md5_hex(sign_str)
        if cal_sign != S:
            code = 401
            error = "signature invalide"
            #调用那个上报HTTP error的接口
            return False
        else:
            return True