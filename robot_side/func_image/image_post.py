import requests
import base64
from pathlib import Path
from datetime import datetime, timezone, timedelta


#By json base64
def upload_image_base64(base_url, token, robotId, taskId, type, timestamp, img_path):
    url = f"{base_url}/api/robots/{robotId}/images"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    img_bytes = Path(img_path).read_bytes()
    payload = {
        "taskId": taskId,
        "type": type,
        "timestamp": timestamp,
        "image": base64.b64encode(img_bytes).decode('ascii')
    }

    #You have to write "json=payload", otherwise, there will be an error
    response = requests.post(url, headers=headers, json=payload, timeout=10)

    response.raise_for_status()

    print("Server response:", response.json())


#by form-data
def upload_image_form(base_url, token, robotId, taskId, type, timestamp, img_path):
    url = f"{base_url}/api/robots/{robotId}/images"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    files = {
        "file": open(img_path, "rb")
    }
    data = {
        "taskId": taskId,
        "type": type,
        "timestamp": timestamp
    }

    response = requests.post(url, headers=headers, files=files, data=data, timeout=10)

    response.raise_for_status()

    print("Server response:", response.json())


if __name__ == "__main__":
    #Singapore time
    #sg_time = timezone(timedelta(hours=8))
    #sg_time_now = datetime.now(sg_time)
    #timestamp = sg_time_now.isoformat()

    utc_now = datetime.now(timezone.utc)
    utc_timestamp = utc_now.replace(microsecond=0).isoformat().replace("+00:00", "Z")


    upload_image_base64(
        base_url= "http://127.0.0.1:8000",
        token = "OneToken",
        robotId = "R1234",
        taskId = 1235,
        type = "deliver",
        timestamp = utc_timestamp,
        img_path = "images/deliver.jpg"
    )

    utc_now = datetime.now(timezone.utc)
    utc_timestamp = utc_now.replace(microsecond=0).isoformat().replace("+00:00", "Z")

    upload_image_form(
        base_url = "http://127.0.0.1:8000",
        token = "OneToken",
        robotId = "R1234",
        taskId = 1235,
        type = "pickup",
        timestamp = utc_timestamp,
        img_path = "images/pickup.jpg"
    )