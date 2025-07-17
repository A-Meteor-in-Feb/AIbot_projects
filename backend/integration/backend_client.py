import requests


TEST_ROBOT_HOST = "127.0.0.1"
TEST_ROBOT_PORT = 8443


COMMAND_MOVE = '0'
COMMAND_DELIVER = '1'
COMMAND_PAUSE = '2'
COMMAND_RESUME = '3'
COMMAND_ABORT = '4'

TASKID_MOVE = 1234
TASKID_DELIVER = 1235

BACKEND_ID = "B1234"
BACKEND_TOKEN = "12345ABCDEF"
ROBOT_ID_1 = "R1234"




def send_command(base_url, command, robotId, parameters):
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

    if parameters == {}:
        payload = {
            "command": command
        }
    else:
        payload = {
            "command": command,
            "params": parameters
        }
    
    response = requests.post(
        url=url, 
        headers=headers, 
        json=payload, 
        timeout=5,
        verify="cert.pem"
    )

    if response.ok:
        data = response.json()
        print(f"Got status code {response.status_code} \n data: {data}")


def move_control():
    """
        Define the request details for posting move command.
    """
    base_url = f"https://{TEST_ROBOT_HOST}:{TEST_ROBOT_PORT}"

    command = "move"
    robotId = ROBOT_ID_1

    parameters = {"taskId": TASKID_MOVE, "x": 11.11, "y": 22.22, "z": 33.33}

    try:
        send_command(base_url, command, robotId, parameters)
    except requests.RequestException as e:
        print("error: ", e)


def deliver_control():
    """
        Define the request details for posting deliver command.
    """
    base_url = f"https://{TEST_ROBOT_HOST}:{TEST_ROBOT_PORT}"
    
    command = "deliver"
    robotId = ROBOT_ID_1

    parameters = {"taskId": TASKID_DELIVER, "binId": 100}

    try:
        send_command(base_url, command, robotId, parameters)  
    except requests.RequestException as e:
        print("error", e)


def pause_control():
    """
        Define the request details for posting pause command.
    """
    base_url = f"https://{TEST_ROBOT_HOST}:{TEST_ROBOT_PORT}"
    
    command = "pause"
    robotId = ROBOT_ID_1

    parameters = {}

    try:
        send_command(base_url, command, robotId, parameters)  
    except requests.RequestException as e:
        print("error", e)


def resume_control():
    """
        Define the request details for posting resume command.
    """
    base_url = f"https://{TEST_ROBOT_HOST}:{TEST_ROBOT_PORT}"
    
    command = "resume"
    robotId = ROBOT_ID_1

    parameters = {}

    try:
        send_command(base_url, command, robotId, parameters)  
    except requests.RequestException as e:
        print("error", e)


def abort_control():
    """
        Define the request details for posting abort command.
    """
    base_url = f"https://{TEST_ROBOT_HOST}:{TEST_ROBOT_PORT}"
    
    command = "abort"
    robotId = ROBOT_ID_1
    
    parameters = {}

    try:
        send_command(base_url, command, robotId, parameters)  
    except requests.RequestException as e:
        print("error", e)


if __name__ == "__main__":

    while True:
        command = input("Please enter your command id: ")
        if command == COMMAND_MOVE:
            move_control()
        elif command == COMMAND_DELIVER:
            deliver_control()
        elif command == COMMAND_PAUSE:
            pause_control()
        elif command == COMMAND_RESUME:
            resume_control()
        elif command == COMMAND_ABORT:
            abort_control()
        elif command == 'q':
            break
        else:
            print("Invalid input, please input number from 0 - 4 :)")
