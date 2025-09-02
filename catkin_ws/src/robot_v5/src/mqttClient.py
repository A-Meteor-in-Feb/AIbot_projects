import paho.mqtt.client as mqtt
import json
import socket
import dataInfo
import time


class MqttClient:
    def __init__(self, host, port, robot_id, robotState: dataInfo.RobotStateInfo, instructionInfo: dataInfo.InstructionInfo, programStatus: dataInfo.ProgramStatus):
        """
        初始化机器人端MQTT client, 用于向后台发布各种话题.
        参数:
            host: MQTT broker host
            port: MQTT broker port
            robot_id: the id number of this robot
            robotState: 发布 state 话题需要的数据对象
            relocalizationInfo: 如果收到重定位指令, 需要存储到的数据对象
        """
        self.host = host
        self.port = port
        self.robotId = robot_id
        self.robotState = robotState
        self.instructionInfo = instructionInfo
        self.programStatus = programStatus

        self.connected = False

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

        self.mqtt_client.subscribe(topic=f"robots/{self.robotId}/command", qos=0)
        self.mqtt_client.message_callback_add(f"robots/{self.robotId}/command", self.command_handler)

        self.connected = True
        self.publish_connection(status="online", reason="connect")
        self.publish_ip()

    def on_disconnect(self, client, userdata, flags, reason_code, properties):
        """
        掉线重连的回调函数
        """
        self.connected = False
        print(f"MQTT disconnected with {reason_code}")


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
        self.mqtt_client.connect_async(self.host, self.port, keepalive=10)
        self.mqtt_client.loop_start()

    def stop(self):
        """
        控制机器人MQTT部分停止并退出执行
        """
        self.connected = False
        self.mqtt_client.loop_stop()
        self.mqtt_client.disconnect()
        print("shutdown, exiting...")

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
        self.robotState.update_ip(ip_addr=ip)
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
        self.robotState.update_connection(connection=status)
        if status == "online":
            self.robotState.update_robotStatus(robotStatus="rest")
        elif status == "offline":
            self.robotState.update_robotStatus(robotStatus="offline")

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
        robotState_info = self.robotState.get_state()
        message = json.dumps(robotState_info).encode("utf-8")
        self.mqtt_client.publish(f"robots/{self.robotId}/state", message, qos=0)
        print("\n Published the state topic: ", robotState_info)

    def command_handler(self, client, userdata, msg):
        """
        用于接收来自后台的特殊指令消息
        """
        self.robotState.update_robotStatus("rest")

        instructions = json.loads(msg.payload.decode("utf-8"))
        type = instructions.get("type")
        print(f"\n receive instruction from backend: {instructions}")

        if type == "reset_address":
            address = instructions.get("address")
            position = address.get("pose").get("dock")
            floor = address.get("floor")
            house = address.get("house")
            
            self.robotState.update_position(floor=floor, house=house)
            self.instructionInfo.update_relocalizationInfo(position=position, floor=floor, house=house)
            self.programStatus.update_programStatus(programStatus="reset_address")
        
        elif type == "move":
            addressList = json.loads(instructions.get("addressList"))

            print(f"\n addressList: {addressList}")
            for item in addressList:
                desc = item.get("identity").get("desc")
                dock = item.get("pose").get("dock")
                floor = item.get("floor")
                house = item.get("house")

                move_dict = {
                    "room": desc,
                    "dock": dock,
                    "floor": floor,
                    "house": house
                }

                self.instructionInfo.update_movePositions(move_dict=move_dict)

            self.programStatus.update_programStatus(programStatus="move")
        
        elif type == "switch_status":
            status = instructions.get("status")
            self.robotState.update_robotStatus(robotStatus=status)
        
        elif type == "execute_command":
            commandContent = instructions.get("commandContent")
            self.instructionInfo.update_command(commandContent=commandContent)
            self.programStatus.update_programStatus("execute_command")

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