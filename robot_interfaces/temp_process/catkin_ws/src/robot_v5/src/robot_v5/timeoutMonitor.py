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
        startTime = time.monotonic()
        print(f"\n\n deadline: {startTime+timeout}")
        with self.lock:
            self.active[startStatus] = {
                "stopStatus": stopStatus,
                "deadline": startTime + timeout,
                "on_timeout": on_timeout
            }
    
    def cancel_record(self, startStatus):
        with self.lock:
            self.active.pop(startStatus, None)

    def clear_record(self):
        with self.lock:
            self.active.clear()

    def stop(self):
        self.stop_event.set()
        self.thread.join(timeout=1)

    def run(self):
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
        self.owner.programStatus.update_programStatus(f"{startStatus}:timeout")
        programStatus = self.owner.programStatus.get_programStatus()
        self.owner.publish_goal(goal_pos=None,goal_floor="",goal_house="",relocation=False,programStatus_old=programStatus,stop=True)
        self.owner.robotState.update_robotStatus("exce")