import requests

ROBOT_ID = "R1234"
BASE_URL = "http://192.168.10.249:8889/api/JKROBOT"


def get_authCode(task_id) -> bool:
    taskId = task_id

    url = f"{BASE_URL}/{ROBOT_ID}/auth-code"

    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ROBOT_TOKEN}"
    }
    """
    # ,verify="cert.pem"   headers=headers,
    response = requests.get(
        url=url,
        json={"taskId": taskId},
        timeout=5
    )
    data = response.json()
    print(data)
    #return response.ok


def notify_taskComplete(task_id) -> bool:
    taskId = task_id

    url = f"{BASE_URL}/{ROBOT_ID}/task-complete"

    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ROBOT_TOKEN}"
    }
    """

    # ,verify="cert.pem"   headers=headers,
    response = requests.post(
        url=url,
        json={"taskId": taskId},
        timeout=5
    )
    data = response.json()
    print(data)
    #return response.ok



def goal_arrived(task_id) -> bool:
    taskId = task_id

    url = f"{BASE_URL}/{ROBOT_ID}/createTaskProcess"

    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ROBOT_TOKEN}"
    }
    """
    # ,verify="cert.pem"   headers=headers,
    response = requests.post(
        url=url,
        json={"taskId": taskId, "step": "arrived"},
        timeout=5
    )
    data = response.json()
    print(data)
    #return response.ok


def check_authCode(task_id) -> bool:
    taskId = task_id

    url = f"{BASE_URL}/{ROBOT_ID}/authTaskCode"

    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ROBOT_TOKEN}"
    }
    """
    # ,verify="cert.pem"   headers=headers,
    response = requests.post(
        url=url,
        json={"taskId": taskId, "code": "ABCDE"},
        timeout=5
    )
    data = response.json()
    print(data)
    #return response.ok


if __name__ == "__main__":
     while True:
        command = input("Please enter your command id: ")
        if command == "a":
            get_authCode(1234567)
        elif command == "b":
            notify_taskComplete(1234567)
        elif command == 'c':
            goal_arrived(1234567)
        elif command == 'd':
            check_authCode(1234567)