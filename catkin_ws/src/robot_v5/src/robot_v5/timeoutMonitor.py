import time
import threading
import rospy
import schedule
import logging

class TimeoutMonitor:
    def __init__(self, owner):
        """
        这个线程用于记录并判断某个事件是否执行超时.
        参数:
            owner: executor
            programStatus: 程序执行状态
        """
        self.owner = owner
        self.lock = threading.Lock()
        self.active = {} #{"stopStatus": str, "deadline": float, "on_timeout": callable}
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()
        

    def record(self, startStatus, stopStatus, timeout, on_timeout=None):
        """
        记录一条超时监控项

        逻辑: 从记录时刻起, 若在 timeout 秒内未从 startStatus 过渡到 stopStatus, 则判定超时并触发回调

        参数:
            startStatus (str): 监控的起始状态名 (键); 通常为当前 programStatus
            stopStatus (str): 期望在超时前到达的结束状态名
            timeout (float): 超时时间，单位秒；从调用时刻开始计时
            on_timeout (Callable[[str, str], None], optional): 自定义超时回调 -callback(startStatus, stopStatus)
                不提供则调用默认 on_timeout
        """
        startTime = time.monotonic()
        print(f"\n\n deadline: {startTime+timeout}")
        with self.lock:
            self.active[startStatus] = {
                "stopStatus": stopStatus,
                "deadline": startTime + timeout,
                "on_timeout": on_timeout
            }
    
    def cancel_record(self, startStatus):
        """
        取消某个起始状态对应的超时监控项

        参数:
            startStatus (str): 要取消的起始状态键
        """
        with self.lock:
            self.active.pop(startStatus, None)

    def clear_record(self):
        """
        清空所有超时监控项
        """
        with self.lock:
            self.active.clear()

    def stop(self):
        self.stop_event.set()
        self.thread.join(timeout=1)

    def run(self):
        """
        后台检测主循环:
            - 每次循环读取当前 programStatus
            - 若某项监控已达到 stopStatus, 则移除
            - 若当前时间超过 deadline, 则触发超时回调并移除
            - 循环间隔 0.1 秒直到 stop_event 触发
        """
        while not self.stop_event.is_set():
            now = time.monotonic()
            timeout_event = []

            with self.lock:
                for startStatus, info in list(self.active.items()):
                    programStatus = self.owner.programStatus.get_programStatus()

                    if programStatus == info["stopStatus"]:
                        self.active.pop(startStatus, None)
                        continue
                        
                    if now >= info["deadline"]:
                        timeout_event.append((startStatus, info))
                        self.active.pop(startStatus, None)

            for startStatus, info in timeout_event:
                try:
                    callback = info["on_timeout"] or self.on_timeout
                    callback(startStatus, info["stopStatus"])
                except Exception as e:
                    rospy.loginfo(f"\n timeout callback error {e} \n")
        
            time.sleep(0.1)

    def on_timeout(self, startStatus, stopStatus):
        """
        默认的超时处理回调
        将 programStatus 更新为 "{startStatus}:timeout"
        通过 owner.publish_goal 触发一次“停止/让路/回退”等安全动作（具体由实现决定）
        将 robotStatus 更新为 "exce"

        参数:
            startStatus (str): 超时的起始状态名
            stopStatus (str): 原计划应达到的结束状态名（仅用于记录或诊断）
        """

        self.owner.programStatus.update_programStatus(f"{startStatus}:timeout")
        programStatus = self.owner.programStatus.get_programStatus()
        self.owner.publish_goal(goal_pos=None,goal_floor="",goal_house="",relocation=False,programStatus_old=programStatus,stop=True)
        self.owner.robotState.update_robotStatus("exce")