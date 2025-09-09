import paho.mqtt.client as mqtt
import json
from robot_v5 import dataInfo


class VendingMqtt:
    def __init__(self, host, port, sn, programStatus: dataInfo.ProgramStatus):
        """
        这个类用于机器人与吐货机通信.
        """
        self.host = host
        self.port = port
        self.msg_client = 1
        self.msg_server = 0
        self.sn = sn
        self.programStatus = programStatus
        self.scanned_code = ""

        client_id = "robot"+str(self.sn)
        self.mqtt_client = mqtt.Client(client_id=client_id, callback_api_version=mqtt.CallbackAPIVersion.VERSION2, clean_session=False)
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_disconnect = self.on_disconnect
        self.mqtt_client.reconnect_delay_set(min_delay=1, max_delay=30)

    def on_connect(self, client, userdata, flags, reason_code, properties):
        """
        MQTT client 与 broker连接的回调函数
        若成功连接, 会发布上线通知以及ip通知给后台
        """
        print(f"MQTT client connected with rc: {reason_code}")

        self.mqtt_client.subscribe(topic="vending/server", qos=0)
        self.mqtt_client.message_callback_add("vending/server", self.server_handler)

    def on_disconnect(self, client, userdata, flags, reason_code, properties):
        """
        掉线重连的回调函数
        """
        print(f"MQTT disconnected with {reason_code}")

    def connect(self):
        """
        控制机器人MQTT部分开始执行
        """
        self.mqtt_client.connect_async(self.host, self.port, keepalive=10)
        self.mqtt_client.loop_start()

    def stop(self):
        """
        控制机器人MQTT部分停止并退出执行
        """
        self.mqtt_client.loop_stop()
        self.mqtt_client.disconnect()
        print("shutdown, exiting...")


    def publish_client(self, cmd, data):
        """
        发布话题 vending/client
        """
        if cmd == "shipment":
            self.msg_client += 1
            info = {
                "msg": self.msg_client,
                "sn": self.sn,
                "cmd": cmd,
                "data": data
            }
        else:
            info = {
                "msg": self.msg_server,
                "sn": self.sn,
                "cmd": cmd,
                "data": data
            }
        message = json.dumps(info).encode("utf-8")
        self.mqtt_client.publish("vending/client", message, qos=0)
        print(f"\n Published the state topic: {info} \n")
        if cmd == "shipment":
            self.msg_client += 1

    def server_handler(self, client, userdata, msg):
        """
        用于接收来自vending machine发布的消息 vending/server
        """
        params = json.loads(msg.payload.decode("utf-8"))
        msg_num = params.get("msg")
        self.msg_server = msg_num
        cmd = params.get("cmd")
        if cmd == "barcode":
            data = params.get("data")
            code_scanner = data.get("c")
            programStatus = self.programStatus.get_programStatus()
            if programStatus == "arrived":
                self.scanned_code = code_scanner
        elif cmd == "shipment":
            data = params.get("data")
            status = "cargo_delivery_complete"
            self.programStatus.update_programStatus(status)
            for item in data:
                r = item.get("r")
                if r != 0:
                    e = item.get("e")
                    status = f"{status}:{e}"
                    self.programStatus.update_programStatus(status)

        print(f"\n receive instruction from backend: {params}")


"""
if __name__ == "__main__":

    BROKER_HOST = "10.25.0.2"
    BROKER_PORT = 1883
    ROBOTID = "18950214603"

    state = dataInfo.StateInfo()

    robot_mqtt = MqttClient(host=BROKER_HOST, port=BROKER_PORT, robot_id=ROBOTID, state=state)
    robot_mqtt.connect()

    try:
        while True:
            time.sleep(2)
    except KeyboardInterrupt:
        pass
    finally:
        robot_mqtt.stop()
"""