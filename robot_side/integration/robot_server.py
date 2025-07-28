from flask import Flask
from flask import request
from flask import jsonify
from flask import Response
from flask import abort
from pathlib import Path
import base64
import cv2
import os

# self-defined class
from robot_taskManager import TaskManager

HTTP = 80
HTTPS = 8443

TEST_ROBOT_HOST = "127.0.0.1"
TEST_ROBOT_PORT = HTTP

BACKEND_ID = "B1234"
BACKEND_VALID_TOKENS = {
    BACKEND_ID: "12345ABCDEF"
}


app = Flask(__name__)

@app.route('/api/JKROBOT/<string:robotId>/tasks', methods=['GET'])
def response_tasks(robotId):
    """
        Resonse to the get request.
        This part, we need get the accurate data from the execution part.
    """
    
    data = request.get_json(force=True)
    parameters = data.get('params', {})

    task_id = parameters.get('taskId')

    # get the queue from the robot side
    queue = task_manager.get_queue()

    config = {
        "multiTaskMode": True,
        "autonomousMode": False,
        "maxQueueSize": 6
    }

    result = {
        "success": True,
        "robotId": robotId,
        "queue": queue,
        "config": config
    }

    return jsonify(result), 200

    
@app.route('/api/JKROBOT/<string:robotId>/tasks/<string:taskId>', methods=['DELETE'])
def delete_task(robotId, taskId):
    """
        Delete the specific task if refered by the backend.
    """
    # search the specifc task by task id and then delete it in the execution part.
    task_deleted = int(taskId)

    data = request.get_json(force=True)
    parameters = data.get('params', {})
    task_id = parameters.get("taskId")

    # wait for the response from the robot's execution part.
    response_from_robot = task_manager.delete_task(task_id=task_deleted)
    print(f"task id is {task_deleted}")
    
    #if the task should be deleted is in the pending tasks' queue.
    if response_from_robot:  
        result = {
            "status": "accepted",
            "task_deleted": task_deleted,
            "taskId": task_id,
            "robotId": robotId
        }
    #if the task should be deleted is executing or have been done already.
    else: 
        result = {
            "status": "denied",
            "task_deleted": task_deleted,
            "taskId": task_id,
            "robotId": robotId
        }

    return jsonify(result), 200 if result["status"] == "accepted" else 400
    

@app.route('/api/robots/<string:robotId>/<string:command>', methods=['POST'])
def handle_command(robotId, command):
    """
        Process the command sent from the backend.
    """
    header = request.headers
    token = header.get('Authorization')[7:]
    if token != BACKEND_VALID_TOKENS[BACKEND_ID]:
        result = {"status": "Unauthorized"}
        return jsonify(result), 401
    else:
        print("Authentication Passed.")

    data = request.get_json(force=True)
    cmd = data.get('command')
    parameters = data.get('params', {})

    if cmd == 'move':
        task_id = parameters.get("taskId")
        coordinateType = parameters.get("coordinateType")
        x = parameters.get("x")
        y = parameters.get("y")
        z = parameters.get("z")

        task = {
            "taskId": task_id,
            "coordinateType": coordinateType,
            "x": x,
            "y": y,
            "z": z
        }

        print(f"Command: {cmd}. Task: {task}")

        #call the task manager pend this task into the pending queue
        task_manager.add_task2pending(task)

        #TODO: add another function call to get the real result back
        #result_from_robot = task_manager.get_result()

        result = {
            "status": "accepted",
            "taskId": task_id,
            "plannedPath": [{"x": 0.0, "y": 0.0, "z": 0.0},
                            {"x": 3.0, "y": 2.0, "z": 0.0},
                            {"x": 6.0, "y": 4.0, "z": 0.0},
                            {"x": 10.0, "y": 5.0, "z": 0.0}]
        }

        return jsonify(result), 200 if result["status"] == "accepted" else 400

    elif cmd == "deliver":
        task_id = parameters.get("taskId")
        bin_id = parameters.get("binId")
        number = parameters.get("number")

        task = {
            "taskId": task_id,
            "binId": bin_id,
            "number": number
        }
        print(f"Command: {cmd}, Task: {task}")

        #call the task manager pend this task into the pending queue
        task_manager.add_task2pending(task)

        #TODO: add another function call to get the real result back
        #result_from_robot = task_manager.get_result()

        result = {
            "status": "accepted",
            "taskId": task_id
        }

        return jsonify(result), 200 if result["status"] == "accepted" else 400

    elif cmd == "pause":
        task_id = parameters.get("taskId")

        task = {
            "taskId": task_id
        }

        print(f"Command: {cmd}, Task: {task}")

        #call the task manager pend this task into the pending queue
        task_manager.add_task2pending(task)

        #TODO: add another function call to get the real result back
        #result_from_robot = task_manager.get_result()

        result = {"status": "paused"}

        return jsonify(result), 200 if result["status"] == "paused" else 400

    elif cmd == "resume":
        task_id = parameters.get("taskId")

        task = {
            "taskId": task_id
        }

        print(f"Command {cmd}, Task: {task}")

        #call the task manager pend this task into the pending queue
        task_manager.add_task2pending(task)

        #TODO: add another function call to get the real result back
        #result_from_robot = task_manager.get_result()

        result = {"status": "resumed"}

        return jsonify(result), 200 if result["status"] == "resumed" else 400

    elif cmd == "abort":
        task_id = parameters.get("taskId")

        task = {
            "taskId": task_id
        }

        print(f"Command {cmd}, Task: {task}")

        #call the task manager pend this task into the pending queue
        task_manager.add_task2pending(task)

        #TODO: add another function call to get the real result back
        #result_from_robot = task_manager.get_result()

        result = {"status": "aborted"}

        return jsonify(result), 200 if result["status"] == "aborted" else 400
    
    elif cmd == "task":
        task_id = parameters.get("taskId")
        bin_id = parameters.get("binId")
        number = parameters.get("number")
        location = parameters.get("location")

        task = {
            "taskId": task_id,
            "binId": bin_id,
            "number": number,
            "location": location
        }

        print(f"Command {cmd}, Task: {task}")

        #call the task manager pend this task into the pending queue
        task_manager.add_task2pending(task)

        #TODO: add another function call to get the real result back
        #result_from_robot = task_manager.get_result()

        result = {"status": "accepted"}

        return jsonify(result), 200 if result["status"] == "accepted" else 400

    elif cmd == "restock":
        task_id = parameters.get("taskId")
        location = parameters.get("location")

        task = {
            "taskId": task_id,
            "location": location
        }

        print(f"Command: {cmd}, Task: {task}")

        #call the task manager pend this task into the pending queue
        task_manager.add_task2pending(task)

        #TODO: add another function call to get the real result back
        #result_from_robot = task_manager.get_result()

        result = {"status": "accepted"}

        return jsonify(result), 200 if result["status"] == "accepted" else 400

    elif cmd == "charge":
        task_id = parameters.get("taskId")
        location = parameters.get("location")

        task = {
            "taskId": task_id,
            "location": location
        }

        print(f"Command: {cmd}, Task: {task}")

        #call the task manager pend this task into the pending queue
        task_manager.add_task2pending(task)

        #TODO: add another function call to get the real result back
        #result_from_robot = task_manager.get_result()

        result = {"status": "accepted"}

        return jsonify(result), 200 if result["status"] == "accepted" else 400

    else:

        result = {"status": "This command is not defined."}
        return jsonify(result), 404
    

def frame_generator():
    """
        generate the video frame
    """
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    VIDEO_PATH = os.path.join(BASE_DIR, "videos", "test_video.mp4")
    cap = cv2.VideoCapture(VIDEO_PATH)
    if not cap.isOpened():
        raise RuntimeError("Cannot open test video file")

    try:
        while True:
            success, frame = cap.read()
            if not success:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue

            ret, jpeg = cv2.imencode('.jpg', frame)
            if not ret:
                continue
            data = jpeg.tobytes()

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + data + b"\r\n"
            )
    finally:
        cap.release()


# TODO: You haven't test for this function
@app.route('/camera/snapshot', methods=['GET'])
def snapshot():
    """
        Response to the snapshot request.
    """
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        abort(401, description="Missing authorization header")

    parts = auth_header.split()
    token = parts[1]

    if token != BACKEND_VALID_TOKENS[BACKEND_ID]:
        abort(401, description="Invalid token")

    image_path = "images/test.jpg"
    image_bytes = Path(image_path).read_bytes()
    image_base64 = base64.b64encode(image_bytes).decode('ascii')
    
    result = {
        "Content-Type": "application/json",
        "image": image_base64
    }

    return jsonify(result), 200
    

@app.route('/camera/stream', methods=['GET'])
def video_stream():
    """
        Response to the video stream request.
    """
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        abort(401, description="Missing authorization header")

    parts = auth_header.split()
    token = parts[1]

    if token != BACKEND_VALID_TOKENS[BACKEND_ID]:
        abort(401, description="Invalid token")

    return Response(
        frame_generator(),
        mimetype='multipart/x-mixed-replace; boundary=--frame'
    )


if __name__ == "__main__":
    task_manager = TaskManager()

    #context = ("cert.pem", "key.pem")
    #app.run(host=TEST_ROBOT_HOST, port=TEST_ROBOT_PORT, ssl_context=context)
    app.run(host=TEST_ROBOT_HOST, port=TEST_ROBOT_PORT)

