import requests
import os
import base64
from datetime import datetime
from datetime import timezone

HTTP = 80
HTTPS = 8443

HTTP_HEAD = "http"
HTTPS_HEAD = "https"

TEST_ROBOT_HOST = "127.0.0.1"
TEST_ROBOT_PORT = HTTP

COMMAND_TASK = '0'
COMMAND_MOVE = '1'
COMMAND_DELIVER = '2'
COMMAND_PAUSE = '3'
COMMAND_RESUME = '4'
COMMAND_ABORT = '5'
COMMAND_RESTOCK = '6'
COMMAND_CHARGE = '7'
COMMAND_TASKS = '8'
COMMAND_DELETE = '9'
COMMAND_SNAPSHOT = '10'

TASKID_TASK = 1000
TASKID_MOVE = 1001
TASKID_DELIVER = 1002
TASKID_PAUSE = 1003
TASKID_RESUME = 1004
TASKID_ABORT = 1005
TASKID_RESTOCK = 1006
TASKID_CHARGE = 1007
TASKID_TASKS = 1008
TASKID_DELETE = 1009
TASKID_SNAPSHOT = 1010

BACKEND_ID = "B1234"
BACKEND_TOKEN = "12345ABCDEF"
ROBOT_ID_1 = "R1234"

UPLOAD_DIR = 'snapshots'
os.makedirs(UPLOAD_DIR, exist_ok=True)


def post_command(base_url, command, robotId, parameters):
    """
        send control commands to the specific robot
        base_url: url of the robot(https://ip:port)
        command: the specific control command
        robotId: the specific robot id
        parameters: the request parameters
    """

    url = f"{base_url}/api/robots/{robotId}/{command}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {BACKEND_TOKEN}"
    }

    payload = {
        "command": command,
        "params": parameters
    }
        
    #,verify="cert.pem"
    response = requests.post(
        url=url, 
        headers=headers, 
        json=payload, 
        timeout=5
    )

    if response.ok:
        data = response.json()
        print(f"Got status code {response.status_code} \n data: {data}")


def task_control():
    """
        Define the request details for posting task command.
    """
    base_url = f"{HTTP_HEAD}://{TEST_ROBOT_HOST}:{TEST_ROBOT_PORT}"

    command = "task"
    robotId = ROBOT_ID_1

    parameters = {
        "taskId": TASKID_TASK,
        "binId": 2,
        "number": 1,
        "location":{
            "address": "1-2-101",
            "coordinateType": "geodetic",
            "position":{
                "x": 10.0,
                "y": 5.0,
                "z": 0.0
            }
        }
    }

    try:
        post_command(base_url, command, robotId, parameters)
    except requests.RequestException as e:
        print("error: ", e)

def move_control():
    """
        Define the request details for posting move command.
    """
    base_url = f"{HTTP_HEAD}://{TEST_ROBOT_HOST}:{TEST_ROBOT_PORT}"

    command = "move"
    robotId = ROBOT_ID_1

    parameters = {
        "taskId": TASKID_MOVE, 
        "coordinateType": "gendetic",
        "x": 11.11, 
        "y": 22.22, 
        "z": 33.33
    }

    try:
        post_command(base_url, command, robotId, parameters)
    except requests.RequestException as e:
        print("error: ", e)


def deliver_control():
    """
        Define the request details for posting deliver command.
    """
    base_url = f"{HTTP_HEAD}://{TEST_ROBOT_HOST}:{TEST_ROBOT_PORT}"
    
    command = "deliver"
    robotId = ROBOT_ID_1

    parameters = {
        "taskId": TASKID_DELIVER, 
        "binId": 100,
        "number": 1
    }

    try:
        post_command(base_url, command, robotId, parameters)  
    except requests.RequestException as e:
        print("error", e)


def pause_control():
    """
        Define the request details for posting pause command.
    """
    base_url = f"{HTTP_HEAD}://{TEST_ROBOT_HOST}:{TEST_ROBOT_PORT}"
    
    command = "pause"
    robotId = ROBOT_ID_1

    parameters = {"taskId": TASKID_PAUSE}

    try:
        post_command(base_url, command, robotId, parameters)  
    except requests.RequestException as e:
        print("error", e)


def resume_control():
    """
        Define the request details for posting resume command.
    """
    base_url = f"{HTTP_HEAD}://{TEST_ROBOT_HOST}:{TEST_ROBOT_PORT}"
    
    command = "resume"
    robotId = ROBOT_ID_1

    parameters = {"taskId": TASKID_RESUME}

    try:
        post_command(base_url, command, robotId, parameters)  
    except requests.RequestException as e:
        print("error", e)


def abort_control():
    """
        Define the request details for posting abort command.
    """
    base_url = f"{HTTP_HEAD}://{TEST_ROBOT_HOST}:{TEST_ROBOT_PORT}"
    
    command = "abort"
    robotId = ROBOT_ID_1
    
    parameters = {"taskId": TASKID_ABORT}

    try:
        post_command(base_url, command, robotId, parameters)  
    except requests.RequestException as e:
        print("error", e)


def restock_control():
    """
        Define the request details for posting restock command.
    """
    base_url = f"{HTTP_HEAD}://{TEST_ROBOT_HOST}:{TEST_ROBOT_PORT}"
    
    command = "restock"
    robotId = ROBOT_ID_1

    parameters = {
        "taskId": TASKID_RESTOCK,
        "location":{
            "address": "仓库A-补货区",
            "coordinateType": "geodetic",
            "position":{
                "x": 1.2950,
                "y": 103.7800,
                "z": 0.0
            }
        }
    }

    try:
        post_command(base_url, command, robotId, parameters)  
    except requests.RequestException as e:
        print("error", e)


def charge_control():
    """
        Define the request details for posting charge command.
    """

    base_url = f"{HTTP_HEAD}://{TEST_ROBOT_HOST}:{TEST_ROBOT_PORT}"
    
    command = "charge"
    robotId = ROBOT_ID_1

    parameters = {
        "taskId": TASKID_CHARGE,
        "location": {
            "address": "充电站B-3号位",
            "coordinateType": "geodetic",
            "position":{
                "x": 1.2930,
                "y": 103.7850,
                "z": 0.0
            }
        }
    }

    try:
        post_command(base_url, command, robotId, parameters)  
    except requests.RequestException as e:
        print("error", e)


def get_tasks():
    """ 
        Send GET request to the robot side to get the tasks' states.
    """
    base_url = f"{HTTP_HEAD}://{TEST_ROBOT_HOST}:{TEST_ROBOT_PORT}"
    robotId = ROBOT_ID_1
    url = f"{base_url}/api/JKROBOT/{robotId}/tasks"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {BACKEND_TOKEN}"
    }

    parameters = {
        "taskId": TASKID_TASKS
    }

    payload = {
        "command": "tasks",
        "params": parameters
    }
    
    #,verify="cert.pem"
    response = requests.get(
        url=url, 
        headers=headers, 
        json=payload, 
        timeout=5
    )

    if response.ok:
        data = response.json()

        print(f"Got status code {response.status_code} \n tasks' queue: {data}")


def delete_task(taskId):
    """
        Delete the specific task
        taskId: get the specific task id that will be deleted.
    """
    base_url = f"{HTTP_HEAD}://{TEST_ROBOT_HOST}:{TEST_ROBOT_PORT}"
    robotId = ROBOT_ID_1
    url = f"{base_url}/api/JKROBOT/{robotId}/tasks/{taskId}"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {BACKEND_TOKEN}"
    }

    parameters = {
        "taskId": taskId
    }

    payload = {
        "command": "delete",
        "params": parameters
    }

    #, verify="cert.pem"
    response = requests.delete(
        url=url,
        headers=headers,
        json=payload,
        timeout=5
    )

    if response.ok:
        data = response.json()
        print(f"Got status code {response.status_code} \n data: {data}")


# TODO: You haven't test for this function
def get_current_snapshot():
    """
        Request for the current snapshot from the backend
    """
    base_url = f"{HTTP_HEAD}://{TEST_ROBOT_HOST}:{TEST_ROBOT_PORT}"
    robotId = ROBOT_ID_1
    url = f"{base_url}/camera/snapshot"
    base64_flag = True

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {BACKEND_TOKEN}"
    }

    parameters = {
        "taskId": TASKID_SNAPSHOT,
        # If it is True, then the robot upload the image by base64
        # Otherwise, image/jpeg
        "base64": base64_flag
    }

    payload = {
        "params": parameters
    }

    #, verify="cert.pem"
    response = requests.get(
        url=url,
        headers=headers,
        json=payload,
        timeout=5
    )

    if response.ok:
        print(f"Got status code {response.status_code}")

        utc_now = datetime.now(timezone.utc)
        utc_timestamp = utc_now.replace(microsecond=0).isoformat().replace("+00:00", "Z")
        file_name = f"{robotId}_snapshot_{utc_timestamp}.jpg"
        path = os.path.join(UPLOAD_DIR, file_name)

        if base64_flag:
            data = response.json()
            img_base64 = data.get("image")
            img_data = base64.b64decode(img_base64)
            
            with open(path, 'wb') as f:
                f.write(img_data)
                print("stored snaphot image already")
        else:
            with open(path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)


if __name__ == "__main__":

    while True:
        command = input("Please enter your command id: ")
        if command == COMMAND_TASK:
            task_control()
        elif command == COMMAND_MOVE:
            move_control()
        elif command == COMMAND_DELIVER:
            deliver_control()
        elif command == COMMAND_PAUSE:
            pause_control()
        elif command == COMMAND_RESUME:
            resume_control()
        elif command == COMMAND_ABORT:
            abort_control()
        elif command == COMMAND_RESTOCK:
            restock_control()
        elif command == COMMAND_CHARGE:
            charge_control()
        elif command == COMMAND_TASKS:
            get_tasks()
        elif command == COMMAND_DELETE:
            delete_task(taskId=1005)
        elif command == COMMAND_SNAPSHOT:
            get_current_snapshot()
        elif command == 'q':
            break
        else:
            print("Invalid input, please input number from 0 - 9 :)")
