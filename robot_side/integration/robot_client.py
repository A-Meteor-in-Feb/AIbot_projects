import requests
import base64
from pathlib import Path
from datetime import datetime
from datetime import timezone

BACKEND_HTTP = 81
BACKEND_HTTPS = 8444

HTTP_HEAD = "http"
HTTPS_HEAD = "https"

TEST_BACKEND_HOST = "127.0.0.1"
TEST_BACKEND_PORT = BACKEND_HTTP

ROBOT_ID = "R1234"
ROBOT_TOKEN = "ABCDEF12345"

TASK_IMAGE_DELIVER_TYPE = '0'
TASK_IMAGE_PICKUP_TYPE = '1'
TASK_BINID = '2'
TASK_INVENTORY = '3'
TASK_ORDERS = '4'
TASK_NOTIFY = '5'
TASK_AUTHCODE = '6'
TASK_COMPLETE = '7'

TASKID_IMAGE = 1010
TASKID_BINID = 1011
TASKID_INVENTORY = 1012
TASKID_ORDERS = 1013
TASKID_NOTIFY = 1014
TASKID_AUTHCODE = 1015
TASKID_COMPLETE = 1016


def upload_image_base64(taskId, type, image_path):
    """
        upload image in base64.
        taskId: the id of the task
        type: the image type (deliver or pickup).
        image_path: the specific image.
    """
    base_url = f"{HTTP_HEAD}://{TEST_BACKEND_HOST}:{TEST_BACKEND_PORT}"
    url = f"{base_url}/api/JKROBOT/{ROBOT_ID}/images"

    image_bytes = Path(image_path).read_bytes()
    image_base64 = base64.b64encode(image_bytes).decode('ascii')

    utc_now = datetime.now(timezone.utc)
    utc_timestamp = utc_now.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ROBOT_TOKEN}"
    }
    
    payload = {
        "taskId": taskId,
        "type": type,
        "timestamp": utc_timestamp,
        "image": image_base64
    }

    #You have to write "json=payload", otherwise, there will be an error
    #,verify="cert.pem"
    response = requests.post(
        url=url, 
        headers=headers, 
        json=payload, 
        timeout=10
    )

    response.raise_for_status()

    print("Server response:", response.json())


def upload_image_form(taskId, type, image_path):
    """
        upload image in multipart/form-date
        taskId: the id of the task
        type: the image type (deliver or pickup).
        image_path: the specific image.
    """
    base_url= f"{HTTP_HEAD}://{TEST_BACKEND_HOST}:{TEST_BACKEND_PORT}"
    url = f"{base_url}/api/JKROBOT/{ROBOT_ID}/images"

    utc_now = datetime.now(timezone.utc)
    utc_timestamp = utc_now.replace(microsecond=0).isoformat().replace("+00:00", "Z")

    
    headers = {
        "Authorization": f"Bearer {ROBOT_TOKEN}"
    }
    files = {
        "file": open(image_path, "rb")
    }
    data = {
        "taskId": taskId,
        "type": type,
        "timestamp": utc_timestamp
    }

    #,verify="cert.pem"
    response = requests.post(
        url=url, 
        headers=headers, 
        files=files, 
        data=data, 
        timeout=10
    )
    
    response.raise_for_status()

    print("Server response:", response.json())


def deliver_type(image_path):
    """
        The deliver image will be uploaded.
        image_path: the specific image.
    """
    taskId = TASKID_IMAGE
    type = "deliver"
    upload_image_base64(taskId, type, image_path)


def pickup_type(image_path):
    """
        The pickup image will be uploaded.
        image_path: the specific image.
    """
    taskId = TASKID_IMAGE
    type = "pickup"
    upload_image_form(taskId, type, image_path)


def search_cargo_binId(bin_id):
    """
        search for the specific cargo information from the backend.
    """
    taskId = TASKID_BINID
    binId = bin_id
    robotId = ROBOT_ID

    base_url = f"{HTTP_HEAD}://{TEST_BACKEND_HOST}:{TEST_BACKEND_PORT}"
    url = f"{base_url}/api/JKROBOT/{robotId}/cargo"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ROBOT_TOKEN}"
    }

    parameters = {
        "binId": binId
    }

    payload = {
        "taskId": taskId,
        "params": parameters
    }

    # ,verify="cert.pem"   
    response = requests.get(
        url=url,
        headers=headers,
        json=payload,
        timeout=5
    )

    if response.ok:
        data = response.json()
        print(f"Got the specific cargo {binId}'s information. \n Info: {data}")


def search_cargo_inventory():
    """
        Search for the cargo information of all inventory
    """
    taskId = TASKID_INVENTORY
    robotId = ROBOT_ID

    base_url = f"{HTTP_HEAD}://{TEST_BACKEND_HOST}:{TEST_BACKEND_PORT}"
    url = f"{base_url}/api/JKROBOT/{robotId}/cargo/inventory"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ROBOT_TOKEN}"
    }

    payload = {
        "taskId": taskId
    }
    
    # ,verify="cert.pem"   
    response = requests.get(
        url=url,
        headers=headers,
        json=payload,
        timeout=5
    )

    if response.ok:
        data = response.json()
        print(f"Got the cargo inventory's information. \n Info: {data}")


def get_orders():
    """
        Robot gets the uncompleted orders from the backedn by itself.
    """
    taskId = TASKID_ORDERS
    robotId = ROBOT_ID

    base_url = f"{HTTP_HEAD}://{TEST_BACKEND_HOST}:{TEST_BACKEND_PORT}"
    url = f"{base_url}/api/JKROBOT/orders"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ROBOT_TOKEN}"
    }

    parameters = {
        "taskId": taskId,
        "robotId": robotId,
        "status": "assigned"
    }

    payload = {
        "taskId": taskId,
        "params": parameters
    }

    # ,verify="cert.pem"   
    response = requests.get(
        url=url,
        headers=headers,
        json=payload,
        timeout=5
    )

    if response.ok:
        data = response.json()
        print(f"Got the robot's uncompleted orders. \n Info: {data}")


def notify_pickup(order_id):
    """
        According to the order id, post notification request to the backend.
        Backend will notify the user by message or in app.
    """
    taskId = TASKID_NOTIFY
    order_id = order_id
    robotId = ROBOT_ID

    base_url = f"{HTTP_HEAD}://{TEST_BACKEND_HOST}:{TEST_BACKEND_PORT}"
    url = f"{base_url}/api/JKROBOT/{robotId}/notify-pickup"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ROBOT_TOKEN}"
    }

    parameters = {
        "taskId": taskId,
        "order_id": order_id
    }

    payload = {
        "taskId": taskId,
        "params": parameters
    }

    # ,verify="cert.pem"   
    response = requests.post(
        url=url,
        headers=headers,
        json=payload,
        timeout=5
    )

    if response.ok:
        data = response.json()
        print(f"Got the notification for the user from the backend. \n Info: {data}")


def get_authCode(order_id):
    """
        Get a new auth-code, or refresh one new auth-code.
    """
    taskId = TASKID_AUTHCODE
    robotId = ROBOT_ID
    order_id = order_id

    base_url = f"{HTTP_HEAD}://{TEST_BACKEND_HOST}:{TEST_BACKEND_PORT}"
    url = f"{base_url}/api/JKROBOT/{robotId}/auth-code"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ROBOT_TOKEN}"
    }

    parameters = {
        "taskId": taskId,
        "order_id": order_id
    }

    payload = {
        "taskId": taskId,
        "params": parameters
    }

    # ,verify="cert.pem"   
    response = requests.get(
        url=url,
        headers=headers,
        json=payload,
        timeout=5
    )

    if response.ok:
        data = response.json()
        print(f"Got the auth-code for the user from the backend. \n Info: {data}")


def notify_taskComplete(order_id):
    """
        Notify the backend that one specific order is completed
    """
    taskId = TASKID_COMPLETE
    robotId = ROBOT_ID
    order_id = order_id

    base_url = f"{HTTP_HEAD}://{TEST_BACKEND_HOST}:{TEST_BACKEND_PORT}"
    url = f"{base_url}/api/JKROBOT/{robotId}/task-complete"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ROBOT_TOKEN}"
    }

    parameters = {
        "taskId": taskId,
        "order_id": order_id
    }

    payload = {
        "taskId": taskId,
        "params": parameters
    }

    # ,verify="cert.pem"   
    response = requests.post(
        url=url,
        headers=headers,
        json=payload,
        timeout=5
    )

    if response.ok:
        data = response.json()
        print(f"Notified the backend that the order has completed. \n Info: {data}")


if __name__ == "__main__":

    while True:
        task = input("Please enter your command id (0-7): ")
        if task == TASK_IMAGE_DELIVER_TYPE:
            deliver_image_path = "images/deliver.jpg"
            deliver_type(deliver_image_path)
        elif task == TASK_IMAGE_PICKUP_TYPE:
            pickup_image_path = "images/pickup.jpg"
            pickup_type(pickup_image_path)
        elif task == TASK_BINID:
            search_cargo_binId(1)
        elif task == TASK_INVENTORY:
            search_cargo_inventory()
        elif task == TASK_ORDERS:
            get_orders()
        elif task == TASK_NOTIFY:
            notify_pickup("ORD20250707123001")
        elif task == TASK_AUTHCODE:
            get_authCode("ORD20250707123001")
        elif task == TASK_COMPLETE:
            notify_taskComplete("ORD20250707123001")
        elif task == 'q':
            break
        else:
            print("Invalid input, please input number from 0 - 9 :)")