from flask import Flask
from flask import request
from flask import jsonify
from flask import Response
from flask import abort
import cv2
import os

TEST_ROBOT_HOST = "127.0.0.1"
TEST_ROBOT_PORT = 8443

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
    
    body = request.get_json(silent=True) or {}
    params = body.get('params', {})

    task_id = params.get('taskId') or request.args.get('taskId')

    # TODO: according to the taskid to execute the module to get the real data
    
    # example response data:
    current_task = {
        "taskId": task_id,
        "status": "delivering",
        "startTime": "2025-07-02T10:30:00Z"
    }

    pending_tasks = [{
        "taskId": "task_20250702_103100_robot001",
        "binId": 3,
        "location": {"x": 1.23, "y": 4.56, "z": 0.00},
        "priority": 1
    }]

    completed_tasks = [{
        "taskId": "task_20250702_102000_robot001",
        "completedTime": "2025-07-02T10:25:00Z"
    }]

    queue = {
        "currentTask": current_task,
        "pendingTasks": pending_tasks,
        "completedTasks": completed_tasks
    }

    config = {
        "multiTaskMode": True,
        "autonomousMode": False,
        "maxQueueSize": 6
    }

    response_body = {
        "success": True,
        "robotId": robotId,
        "queue": queue,
        "config": config
    }

    return jsonify(response_body), 200

    
@app.route('/api/JKROBOT/<string:robotId>/tasks/<string:taskId>', methods=['DELETE'])
def delete_task(robotId, taskId):
    """
        Delete the specific task if refered by the backend.
    """
    


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
    print(data)
    cmd = data.get('command')
    parameters = data.get('params', {})

    if cmd == 'move':
        task_id = parameters.get("taskId")
        x = parameters.get("x")
        y = parameters.get("y")
        z = parameters.get("z")

        print(f"Command: {cmd}. Task: {task_id} \n x: {x}, y: {y}, z: {z}")

        #robot move function and get results/

        result = {
            "status": "accepted",
            "taskId": 1234,
            "plannedPath": [{"x": 0.0, "y": 0.0, "z": 0.0},
                            {"x": 3.0, "y": 2.0, "z": 0.0},
                            {"x": 6.0, "y": 4.0, "z": 0.0},
                            {"x": 10.0, "y": 5.0, "z": 0.0}]
        }

        return jsonify(result), 200 if result["status"] == "accepted" else 400

    elif cmd == "deliver":
        task_id = parameters.get("taskId")
        bin_id = parameters.get("binId")
        print(f"Command: {cmd}, Task: {task_id}, Bin: {bin_id}")

        result = {
            "status": "accepted",
            "taskId": 1235
        }

        return jsonify(result), 200 if result["status"] == "accepted" else 400

    elif cmd == "pause":
        print(f"Command {cmd}")

        result = {"status": "paused"}

        return jsonify(result), 200 if result["status"] == "paused" else 400

    elif cmd == "resume":
        print(f"Command {cmd}")

        result = {"status": "resumed"}

        return jsonify(result), 200 if result["status"] == "resumed" else 400

    elif cmd == "abort":
        print(f"Command {cmd}")

        result = {"status": "aborted"}

        return jsonify(result), 200 if result["status"] == "aborted" else 400
    
    elif cmd == "task":
        print(f"Receive command {cmd}")

        result = {"status": "accepted"}

        return jsonify(result), 200 if result["status"] == "accepted" else 400

    elif cmd == "restock":
        print(f"Receive command {cmd}")

        result = {"status": "accepted"}

        return jsonify(result), 200 if result["status"] == "accepted" else 400

    elif cmd == "charge":
        print(f"Receive command {cmd}")

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
    context = ("cert.pem", "key.pem")
    app.run(host=TEST_ROBOT_HOST, port=TEST_ROBOT_PORT, ssl_context=context)
