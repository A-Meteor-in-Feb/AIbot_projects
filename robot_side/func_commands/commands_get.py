from flask import Flask
from flask import request
from flask import jsonify

app = Flask(__name__)

@app.route('/api/robots/<string:robotId>/<string:command>', methods=['POST'])
def handle_move_command(robotId, command):
    data = request.get_json(force=True)
    print(data)
    cmd = data.get('command')
    parameters = data.get('params', {})

    if cmd == 'move':
        task_id = parameters.get("taskId")
        x = parameters.get("x")
        y = parameters.get("y")
        z = parameters.get("z")

        print("Command: ", cmd, "task_Id:", task_id, "x:", x, "y:", y, "z:", z)

        #robot move function and get results/

        result = {
            "status": "accepted",
            "task_id": 1234,
            "plannedPath": [{"x": 0.0, "y": 0.0, "z": 0.0},
                            {"x": 3.0, "y": 2.0, "z": 0.0},
                            {"x": 6.0, "y": 4.0, "z": 0.0},
                            {"x": 10.0, "y": 5.0, "z": 0.0}]
        }
    
    elif cmd == "deliver":
        #TODO
        task_id = parameters.get("taskId")
        bin_id = parameters.get("binId")
    elif cmd == "pause":
        #TODO

        result = {"status": "paused"}
    elif cmd == "resume":
        #TODO

        result = {"status": "resumed"}
    elif cmd == "abort":
        #TODO
        result = {"status": "aborted"}
    else:
        #TODO - return the command is not allowed.
        print("no process of this command")

    
    return jsonify(result), 200 if result["status"] == "accepted" else 400

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000)