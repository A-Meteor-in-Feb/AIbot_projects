import requests
import json


COMMAND_MOVE = '0'
COMMAND_DELIVER = '1'
COMMAND_PAUSE = '2'
COMMAND_RESUME = '3'
COMMAND_ABORT = '4'

RUNNING = True

def on_quit():
    global RUNNING
    print("The program is exiting ...")
    RUNNING = False


def send_command(base_url, token, command, robotId, parameters):
    url = f"{base_url}/api/robots/{robotId}/{command}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
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
    
    response = requests.post(url=url, headers=headers, json=payload, timeout=5)
    
    print(f"Got status code {response.status_code}")

    if response.ok:
        data = response.json()
        print("Success: ", data)
    
    #response.raise_for_status()


def move_control():
    base_url = "http://127.0.0.1:8000"
    token = "OneToken"
    command = "move"
    robotId = "R1234"
    parameters = {"taskId": 1234, "x": 11.11, "y": 22.22, "z": 33.33}

    try:
        send_command(base_url, token, command, robotId, parameters)  
    except requests.RequestException as e:
        print("error", e)


def deliver_control():
    base_url = "http://127.0.0.1:8000"
    token = "OneToken"
    command = "deliver"
    robotId = "R1234"
    parameters = {"taskId": 1234, "binId": 100}

    try:
        send_command(base_url, token, command, robotId, parameters)  
    except requests.RequestException as e:
        print("error", e)


def pause_control():
    base_url = "http://127.0.0.1:8000"
    token = "OneToken"
    command = "pause"
    robotId = "R1234"
    parameters = {}

    try:
        send_command(base_url, token, command, robotId, parameters)  
    except requests.RequestException as e:
        print("error", e)


def resume_control():
    base_url = "http://127.0.0.1:8000"
    token = "OneToken"
    command = "resume"
    robotId = "R1234"
    parameters = {}

    try:
        send_command(base_url, token, command, robotId, parameters)  
    except requests.RequestException as e:
        print("error", e)


def abort_control():
    base_url = "http://127.0.0.1:8000"
    token = "OneToken"
    command = "abort"
    robotId = "R1234"
    parameters = {}

    try:
        send_command(base_url, token, command, robotId, parameters)  
    except requests.RequestException as e:
        print("error", e)


if __name__ == "__main__":
    
    while RUNNING:
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
            on_quit()
        else:
            print("Invalid input, please input number from 0 - 4 :)")
