import threading
import time
import rospy
import schedule
import logging

class ElevatorFlowGetter:
    def __init__(self, owner, flow_id: str, period: float = 5):
        """
        owner: executor
        flow_id: 本次电梯流程的 flowId
        period: 轮询周期（秒）
        """
        self.owner = owner
        self.flow_id = flow_id
        self.period = period
        self._stop = threading.Event()
        self._sched = schedule.Scheduler()
        self._job = None
        self._thread = threading.Thread(target=self.run, name=f"ElevatorFlowWatcher-{flow_id}", daemon=True)

        self.file_logger2 = logging.getLogger("backend_logger2")
        self.file_logger2.setLevel(logging.INFO)
        fh2 = logging.FileHandler("backend_response2.log", mode="a", encoding="utf-8")
        fh2.setLevel(logging.INFO)
        self.file_logger2.addHandler(fh2)
        

    def start(self):
        if self._thread.is_alive():
            return
        # 注册定时任务：每 period 秒调用一次 _tick

        try:
            self.get()
        except Exception:
            pass

        self._job = self._sched.every(self.period).seconds.do(self.get)
        self._thread.start()

    def stop(self):
        self._stop.set()
        # 取消当前 job（如果已经创建）
        if self._job is not None:
            try:
                self._sched.cancel_job(self._job)
            except Exception:
                pass
            self._job = None

    def run(self):
        while not self._stop.is_set() and not rospy.is_shutdown():
            self._sched.run_pending()
            self._stop.wait(0.1)

    def get(self):
        if self._stop.is_set() and  rospy.is_shutdown():
            return schedule.CancelJob
            
        try:
            response = self.owner.http_client.get_elevatorControlFlow(flowId=self.flow_id)

            self.file_logger2.info(f"<httpClient-51> backend response: {response}\n")
                   
            flow_info = response.get("data").get("flowInfo")
            elevatorStatus = flow_info.get("status")

            self.owner.elevatorStatus = elevatorStatus

            fromElevatorOutAddress = flow_info.get("fromElevatorOutAddress")
            fromElevatorInAddress = flow_info.get("fromElevatorInAddress")
            toElevatorOutAddress = flow_info.get("toElevatorOutAddress")
            toElevatorInAddress = flow_info.get("toElevatorInAddress")

            self.owner.elevatorControlParams.update_fromElevatorOutAddress(fromElevatorOutAddress=fromElevatorOutAddress)
            self.owner.elevatorControlParams.update_fromElevatorInAddress(fromElevatorInAddress=fromElevatorInAddress)
            self.owner.elevatorControlParams.update_toElevatorOutAddress(toElevatorOutAddress=toElevatorOutAddress)
            self.owner.elevatorControlParams.update_toElevatorInAddress(toElevatorInAddress=toElevatorInAddress)

            if elevatorStatus == 100 or elevatorStatus == 10000:
                self._stop.set()
                return schedule.CancelJob

            try:
                task_status = (self.owner.state.get_state() or {}).get("taskStatus")
                if task_status == "idle_toGo" or task_status == "return_toGo":
                    self._stop.set()
                    return schedule.CancelJob
            except Exception:
                pass
        except Exception as e:
            rospy.loginfo(f" <elevatorFlowGetter-62> error as: {e}")
            
