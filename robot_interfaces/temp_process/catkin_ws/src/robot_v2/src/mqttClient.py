import paho.mqtt.client as mqtt
import json
import socket
import dataInfo


class MqttClient:
    def __init__(self, host, port, robot_id, state: dataInfo.StateInfo):
        """
        初始化机器人端MQTT client, 用于向后台发布各种话题.
        参数:
            host: MQTT broker host
            port: MQTT broker port
            robot_id: the id number of this robot
            state_info: 发布 state 话题需要的数据对象
        """
        self.host = host
        self.port = port
        self.robotId = robot_id
        self.state = state

        self.mqtt_client = mqtt.Client(client_id=robot_id, callback_api_version=mqtt.CallbackAPIVersion.VERSION2, clean_session=False)
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_disconnect = self.on_disconnect
        self.mqtt_client.reconnect_delay_set(min_delay=1, max_delay=30)

        self.set_lastWill()

    def on_connect(self, client, userdata, flags, reason_code, properties):
        """
        MQTT client 与 broker连接的回调函数
        若成功连接, 会发布上线通知以及ip通知给后台
        """
        print(f"MQTT client connected with rc: {reason_code}")
        self.publish_connection(status="online", reason="connect")
        self.publish_ip()

    def on_disconnect(self, client, userdata, flags, reason_cond, properties):
        """
        掉线重连的回调函数
        """
        print(f"MQTT disconnected with {reason_cond}, reconnecting...")

    def set_lastWill(self):
        """
        last will 设置, 当机器人异常下线--程序崩溃停止运行, 或者彻底断线, 无法重连时发从此消息
        """
        payload = {"status": "offline", "reason": "disconnect"}
        message = json.dumps(payload).encode("utf-8")
        self.mqtt_client.will_set(f"robots/{self.robotId}/connection", message, qos=1, retain=True)

    def connect(self):
        """
        控制机器人MQTT部分开始执行
        """
        self.mqtt_client.connect_async(self.host, self.port, keepalive=60)
        self.mqtt_client.loop_start()

    def stop(self):
        """
        控制机器人MQTT部分停止并退出执行
        """
        self.mqtt_client.loop_stop()
        self.mqtt_client.disconnect()

    def get_ip(self):
        """
        这个函数就是用来获得与MQTT broker通信的IP地址
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect((self.host, self.port))
                return s.getsockname()[0]
        except Exception as e:
            print(f"when try to get ip, got error: ", e)
            return ""

    def publish_ip(self):
        """
        发布话题 robots/{robotId}/network/ip
        """
        ip = self.get_ip()
        #self.state.update_ip(ip) 没写这个字段和这个功能, 可以考虑以后加上
        payload = {
            "interface": "wireguard",
            "ip": ip,
            "timestamp": dataInfo.utc_now_ms()
        }
        message = json.dumps(payload).encode("utf-8")

        self.mqtt_client.publish(f"robots/{self.robotId}/network/ip", message, qos=1, retain=False)
        print("Publish the network/ip topic, ip: ", ip)

    def publish_connection(self, status, reason):
        """
        发布话题 robots/{robotId}/connection
        参数:
            status: string, 机器人的连接状态(online 或者 offline)
            reason: string, 机器人连接状态产生的原因
        """
        #先把机器人连接状态和任务状态更新
        self.state.update_connection(connection=status)
        if status == "online":
            self.state.update_taskStatus(status="idle")

        payload = {
            "status": status,
            "reason": reason
        }
        message = json.dumps(payload).encode("utf-8")

        self.mqtt_client.publish(f"robots/{self.robotId}/connection", message, qos=1, retain=True)
        print("Publish the connection topic and update the state")

    def publish_state(self):
        """
        发布话题 robots/{robotId}/state
        """
        state_info = self.state.get_state()
        message = json.dumps(state_info).encode("utf-8")
        self.mqtt_client.publish(f"robots/{self.robotId}/state", message, qos=0)
        print("Published the state topic: ", state_info)