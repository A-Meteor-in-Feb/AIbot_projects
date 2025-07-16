from flask import Flask
from flask import request
from flask import jsonify


BACKEND_VALID_TOKENS = {
    "B1234": "12345ABCDEF"
}

ROBOT_ID = "R1234"
ROBOT_TOKEN = "ABCDEF12345"


app = Flask(__name__)

@app.route('/api/robots/<string:robotId>/<string:command>', methods=['POST'])
def handle_move_command(robotId, command):
    
    header = request.headers
    token = header.get('Authorization')[7:]
    if token != BACKEND_VALID_TOKENS["B1234"]:
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

    else:
        
        result = {"status": "This command is not defined."}
        return jsonify(result), 422



if __name__ == "__main__":
    context = ("cert.pem", "key.pem")
    app.run(host="127.0.0.1", port=8443, ssl_context=context)