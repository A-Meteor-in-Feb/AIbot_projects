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
        """
        获取电梯流程信息, 并更新 owner 对象

        - 调用后台 HTTP 接口获取电梯流程状态。
        - 记录返回数据到日志文件。
        - 更新 owner 的 elevatorStatus 和 elevatorControl 相关参数。
        - 当流程完成 (status==100 或 10000)，或 owner.programStatus 进入 "ready_move"，则终止任务。

        返回:
            schedule.CancelJob: 当流程结束或需要停止时返回该值以取消调度
        """
        if self._stop.is_set() or rospy.is_shutdown():
            return schedule.CancelJob
            
        try:
            response = self.owner.http_client.get_elevatorControlFlow(flowId=self.flow_id)
                   
            flow_info = response.get("data").get("flowInfo")
            elevatorStatus = flow_info.get("status")

            self.owner.elevatorStatus = elevatorStatus

            fromElevatorOutAddress = flow_info.get("fromElevatorOutAddress")
            fromElevatorInAddress = flow_info.get("fromElevatorInAddress")
            toElevatorOutAddress = flow_info.get("toElevatorOutAddress")
            toElevatorInAddress = flow_info.get("toElevatorInAddress")

            self.owner.elevatorControl.update_fromElevatorOutAddress(fromElevatorOutAddress=fromElevatorOutAddress)
            self.owner.elevatorControl.update_fromElevatorInAddress(fromElevatorInAddress=fromElevatorInAddress)
            self.owner.elevatorControl.update_toElevatorOutAddress(toElevatorOutAddress=toElevatorOutAddress)
            self.owner.elevatorControl.update_toElevatorInAddress(toElevatorInAddress=toElevatorInAddress)

            if elevatorStatus == 100 or elevatorStatus == 10000:
                self._stop.set()
                return schedule.CancelJob

            try:
                programStatus = self.owner.programStatus.get_programStatus
                if programStatus == "ready_move":
                    self._stop.set()
                    return schedule.CancelJob
            except Exception:
                pass
        except Exception as e:
            rospy.loginfo(f" <elevatorFlowGetter-62> error as: {e}")
            
