import requests
import json

def send_command(base_url, token, command, robotId, parameters):
    url = f"{base_url}/api/robots/{robotId}/{command}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
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

    return response

if __name__ == "__main__":
    robot_url = "http://127.0.0.1:8000"
    token = "OneToken"
    command = "move"
    robotId = "R1234"
    parameters = {"taskId": 1234, "x": 11.11, "y": 22.22, "z": 33.33}

    try:
        response = send_command(robot_url, token, command, robotId, parameters)
        data = response.json()
    except requests.RequestException as e:
        print("error", e)