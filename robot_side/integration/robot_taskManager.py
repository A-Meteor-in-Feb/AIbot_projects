from collections import deque

#deque - double ended queue, efficient operation in double ends. O(1)

class TaskManager:
    """
        The class is to manage the tasks
    """

    def __init__(self):
        self.pending = deque()
        self.current = None
        self.completed = []

    # Robot restful side call this function to add tasks into the pending queue first
    def add_task2pending(self, task):
        self.pending.append(task)

    # Robot execution side call this function to get the next to-do task
    def add_task2current(self):
        if self.pending:
            self.current = self.pending.popleft()
        else:
            None

    # Robot execution side call this function to announce the current task is done.
    def finish_current(self):
        # One task is completed and then call this function.
        # add the task into the completed queue
        self.completed.append(self.current)
        self.current = None

    # Robot restful side call this function to delete the task in the pending queue.
    def delete_task(self, task_id):
        # Look for the specific task to be deleted if it is in the pending queue.
        for index, task in enumerate(self.pending):
            if task.get("taskId") == task_id:
                del self.pending[index]
                return True
        #if no such task in the pending queue, return False.
        return False
    
    # Robot restful side call this function to get the tasks' queue
    def get_queue(self):
        return {
            "currentTask": self.current or {},
            "pendingTasks": list(self.pending),
            "completedTasks": self.completed
        }