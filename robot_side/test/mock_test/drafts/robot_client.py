import requests

ROBOT_ID = "R1234"


def get_authCode(task_id):
    """
        Get a new auth-code, or refresh one new auth-code.
    """
    taskId = task_id

    base_url = f"http://127.0.0.1:8889"
    url = f"{base_url}/api/JKROBOT/{ROBOT_ID}/auth-code"

    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ROBOT_TOKEN}"
    }
    """

    payload = {
        "taskId": taskId,
    }

    # ,verify="cert.pem"   headers=headers,
    response = requests.get(
        url=url,
        json=payload,
        timeout=5
    )

    if response.ok:
        data = response.json()
        print(f"Got the auth-code for the user from the backend. \n Info: {data}")

        return "ok"
    else:
        return "not ok"


def notify_taskComplete(task_id):
    """
        Notify the backend that one specific order is completed
    """
    taskId = task_id

    base_url = f"http://127.0.0.1:8889"
    url = f"{base_url}/api/JKROBOT/{ROBOT_ID}/task-complete"

    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ROBOT_TOKEN}"
    }
    """

    payload = {
        "taskId": taskId
    }

    # ,verify="cert.pem"   headers=headers,
    response = requests.post(
        url=url,
        json=payload,
        timeout=5
    )

    if response.ok:
        data = response.json()
        print(f"Notified the backend that the order has completed. \n Info: {data}")
        return "ok"
    else:
        return "not ok"