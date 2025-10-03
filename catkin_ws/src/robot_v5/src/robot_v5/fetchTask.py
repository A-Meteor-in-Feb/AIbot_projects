import threading
import time
import rospy
import schedule


class FetchTask:
    def __init__(self, owner):
        """
        这个线程用于执行周期性地从后台拉取任务信息, 为了避免因为网络问题没有得到最新的任务状态
        参数:
            http_client: 用来调用机器人客户端接口
            state: 机器人自身的状态
            statusBackend: 后台分配任务的状态
            currentOrder: 机器人当前执行的任务的详细信息
            period:
            elevatorPlan: 
            stop_event: 线程终止时间标志
        """
        self.owner = owner

        self._stop = threading.Event()
        self._sched = schedule.Scheduler()
        self._job = None
        self._thread = threading.Thread(target=self.run, name="fetchTaskThread", daemon=True)

        self.level = {"1": 1, "2m": 2, "3": 3, "4": 4, "5": 5}

    def start(self):
        if self._thread.is_alive():
            return

        try:
            self.fetchTask()
        except Exception:
            pass

        self._job = self._sched.every(5).seconds.do(self.fetchTask)
        self._thread.start()

    def stop(self):
        self._stop.set()
        
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

    def fetchTask(self):
        """
        从后台获取任务信息, 并根据返回结果更新机器人状态

        流程：
            1. 获取机器人当前状态 (taskId、floor、house 等)
            2. 调用后台接口查询任务信息
            3. 根据返回的 taskId 和 status 与本地状态对比:
                - 如果有新任务，初始化 currentOrder 和 elevatorControl, 并更新机器人状态为 "task"
                - 如果任务被取消 (status==60)，重置任务信息并更新机器人状态为 "back"
                - 如果是补货任务 (status==90)，更新返回地址并设置状态为 "restock"
                - 如果补货后重新分配配送任务 (status==30, old==90)，恢复配送逻辑
            4. 遇到异常时，打印 ROS 日志
        
        返回:
            schedule.CancelJob: 如果 stop 被触发或 ROS 关闭，则取消定时任务
        """
        if self._stop.is_set() or rospy.is_shutdown():
            return schedule.CancelJob
        
        try:
            robotState = self.owner.robotState.get_state()
            robot_taskId_old = robotState.get("robotTaskId")
            robot_floor = robotState.get("floor")
            robot_house = robotState.get("house")
                
            response = self.owner.http_client.select_taskInfo(taskId=robot_taskId_old, floor=robot_floor, building=robot_house)
            response_code = response.get("code")

            status_old = self.owner.statusBackend.get_statusBackend().get("status")

            if response_code == 0:
                data = response.get("data")
                taskInfo = data.get("taskInfo") or {}

                if taskInfo != {}:

                    taskId_new = data.get("taskInfo").get("id")
                    status_new = data.get("taskInfo").get("status")

                    if robot_taskId_old != taskId_new and (status_new == 30 or status_new == 40):

                        self.owner.statusBackend.update_statusBackend(taskId=taskId_new, status=status_new)
                            
                        robotStatus = self.owner.robotState.get_state().get("robotStatus")
                        programStatus = self.owner.programStatus.get_programStatus()
                            
                        #有新任务且机器人处于可以接收新任务的状态
                        if robotStatus in ["idle", "back"] and programStatus not in ["moving_lift_inside", "at_lift_inside", "relocalization", "relocalizing", "ready_move"]:
                                
                            self.owner.currentOrder.reset_currentOrder()
                            self.owner.elevatorControl.reset_elevatorControlParams()

                            #更新任务信息
                            code = data.get("code")
                            self.owner.currentOrder.update_deliveryDetails(taskId=taskId_new, code=code)
                            goal_addrList = taskInfo.get("addressList")
                            self.store_goalPositions(goal=True, addrList=goal_addrList)
                            return_addrList = data.get("addressList")
                            self.store_goalPositions(goal=False, addrList=return_addrList)
                            spaceLists = taskInfo.get("spaceParams").get("spaceList")
                            self.store_deliveryInfo(spaceLists=spaceLists)

                            #更新机器人状态
                            self.owner.robotState.update_robotTaskId(taskId_new)
                            self.owner.robotState.update_robotStatus("task")
                            self.owner.programStatus.update_programStatus("assigned")
                                
                    elif robot_taskId_old == taskId_new and status_new == 60:
                            
                        self.owner.statusBackend.update_statusBackend(taskId=taskId_new, status=status_new)

                        robotStatus = self.owner.robotState.get_state().get("robotStatus")
                        programStatus = self.owner.programStatus.get_programStatus()

                        if robotStatus == "task" and programStatus not in ["moving_lift_inside", "at_lift_inside", "relocalization", "relocalizing", "ready_move"]:
                                
                            self.owner.currentOrder.reset_currentOrder()
                            self.owner.elevatorControl.reset_elevatorControlParams()

                            #更新机器人[返回地址]
                            return_addrList = data.get("addressList")
                            self.store_goalPositions(goal=False, addrList=return_addrList)

                            #更新机器人状态
                            self.owner.robotState.update_robotTaskId(0)
                            self.owner.robotState.update_robotStatus("back")
                            self.owner.programStatus.update_programStatus("cancel_delivery")

                    elif robot_taskId_old != taskId_new and status_new == 90:
                        self.owner.statusBackend.update_statusBackend(taskId=taskId_new, status=status_new)

                        self.owner.currentOrder.reset_currentOrder()
                        self.owner.elevatorControl.reset_elevatorControlParams()

                        #更新机器人[返回地址]
                        return_addrList = data.get("addressList")
                        self.store_goalPositions(goal=False, addrList=return_addrList)

                        self.owner.robotState.update_robotTaskId(taskId_new)
                        self.owner.robotState.update_robotStatus("back")
                        self.owner.programStatus.update_programStatus("restock")

                    elif robot_taskId_old == taskId_new and status_new == 30 and status_old == 90:

                        self.owner.statusBackend.update_statusBackend(taskId=taskId_new, status=status_new)

                        self.owner.currentOrder.reset_currentOrder()
                        self.owner.elevatorControl.reset_elevatorControlParams()

                        #更新任务信息
                        code = data.get("code")
                        self.owner.currentOrder.update_deliveryDetails(taskId=taskId_new, code=code)
                        goal_addrList = taskInfo.get("addressList")
                        self.store_goalPositions(goal=True, addrList=goal_addrList)
                        return_addrList = data.get("addressList")
                        self.store_goalPositions(goal=False, addrList=return_addrList)
                        spaceLists = taskInfo.get("spaceParams").get("spaceList")
                        self.store_deliveryInfo(spaceLists=spaceLists)

                        #更新机器人状态
                        self.owner.robotState.update_robotTaskId(taskId_new)
                        self.owner.robotState.update_robotStatus("task")
                        self.owner.programStatus.update_programStatus("assigned")
                        
            else:
                rospy.loginfo(f"Backend response with: {response_code}")
        except Exception as e:
            rospy.loginfo(f"Error: {e}")

    def store_goalPositions(self, goal, addrList):
        """
        存储更新订单目的地址以及机器人返回原点的地址详情
        参数:
            goal: bool, 代表当前更新的事配送目的地址(True) 还是 返回原点地址(False).
            addrList: 目标地址的详细信息
        """
        for item in addrList:
            desc = item.get("identity").get("desc")
            dock = item.get("pose").get("dock")
            floor = item.get("floor")
            house = item.get("house")

            pos_dict = {
                "room": desc,
                "dock": dock,
                "floor": floor,
                "house": house
            }

            if goal:
                self.owner.currentOrder.update_goalPositions(goal_pos_dict=pos_dict)
            else:
                self.owner.currentOrder.update_returnPositions(return_pos_dict=pos_dict)
        
    def store_deliveryInfo(self, spaceLists):
        """
        存储并更新订单的货品信息
        参数:
            spaceLists (list[dict]) 货仓空间信息，每个元素包含:
                * spaceNo: 货道编号
                * quantity: 数量
        """
        for item in spaceLists:
            binId = item.get("spaceNo")
            number = item.get("quantity")

            cargo_dict = {
                "binId":binId,
                "number": number
            }

            self.owner.currentOrder.update_deliveryInfo(cargo_dict=cargo_dict)