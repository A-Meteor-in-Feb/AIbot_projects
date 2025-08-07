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

    return response.ok


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

    return response.ok