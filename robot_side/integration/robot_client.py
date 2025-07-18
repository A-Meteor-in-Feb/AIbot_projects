import requests
import base64
from pathlib import Path
from datetime import datetime
from datetime import timezone

TEST_BACKEND_HOST = "127.0.0.1"
TEST_BACKEND_PORT = 8444
ROBOT_ID = "R1234"
ROBOT_TOKEN = "ABCDEF12345"

DELIVER_TYPE = '0'
PICKUP_TYPE = '1'


def upload_image_base64(taskId, type, image_path):
    """
        upload image in base64.
        taskId: the id of the task
        type: the image type (deliver or pickup).
        image_path: the specific image.
    """
    base_url = f"https://{TEST_BACKEND_HOST}:{TEST_BACKEND_PORT}"
    url = f"{base_url}/api/robots/{ROBOT_ID}/images"

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
    response = requests.post(
        url=url, 
        headers=headers, 
        json=payload, 
        timeout=10,
        verify="cert.pem"
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
    base_url= "https://127.0.0.1:8443"
    url = f"{base_url}/api/robots/{ROBOT_ID}/images"

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

    response = requests.post(
        url=url, 
        headers=headers, 
        files=files, 
        data=data, 
        timeout=10,
        verify="cert.pem"
    )
    
    response.raise_for_status()

    print("Server response:", response.json())


def deliver_type(image_path):
    """
        The deliver image will be uploaded.
        image_path: the specific image.
    """
    taskId = 1235
    type = "deliver"
    upload_image_base64(taskId, type, image_path)


def pickup_type(image_path):
    """
        The pickup image will be uploaded.
        image_path: the specific image.
    """
    taskId = 1236
    type = "pickup"
    upload_image_form(taskId, type, image_path)


if __name__ == "__main__":

    while True:
        type = input("Please choose deliver(0) or pickup(1):")
        if type == DELIVER_TYPE:
            deliver_image_path = "images/deliver.jpg"
            deliver_type(deliver_image_path)
        elif type == PICKUP_TYPE:
            pickup_image_path = "images/pickup.jpg"
            pickup_type(pickup_image_path)
        else:
            break