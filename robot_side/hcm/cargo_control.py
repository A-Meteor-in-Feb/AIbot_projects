from flask import Flask
from flask import request
from flask import jsonify
from flask import Response
from flask import abort
from flask import make_response
import base64
import time

app = Flask(__name__)

@app.route('/api/hcm/cargo/open', methods=['POST'])
def openCargoBin():
    payload = request.get_json()

    binId = payload.get("bin_id")
    reason = request.get("reason", "unknown")
    taskId = request.get("task_id", getCurrentTaskId())

    if (binId < 1 or binId > 6):
        


@app.route('/api/hcm/cargo/close', methods=['POST'])



@app.route('/api/hcm/cargo/status', methods=['GET'])

