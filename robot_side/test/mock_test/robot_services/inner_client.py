import requests
import os
import base64

def post_goal(taskId, binId, address, x, y, z):
    url = "http://127.0.0.1:8886/inner-robot/goal"

    payload = {
        "taskId": taskId,
        "binId": binId,
        "address": address,
        "x": x,
        "y": y,
        "z": z
    }

    response = requests.post(url=url, json=payload, timeout=5)

    return response.ok