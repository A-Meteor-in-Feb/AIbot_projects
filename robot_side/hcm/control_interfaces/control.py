from flask import Flask
from flask import request
from flask import jsonify
from datetime import datetime
from datetime import timezone

from utils import response

DEFAULT_SPEED = 1

app = Flask(__name__)

@app.route('/api/hcm/move', methods=['POST'])
def moveToPosition():
    payload = request.get_json()

    if not payload:
        happen_tsp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-4]+"Z"
        error_resp = response.error_response(message="Invalid JSON body", code=400, timestamp=happen_tsp)
        return jsonify(error_resp), 400
    
    target = {
        "x": payload.get("x"),
        "y": payload.get("y"),
        "z": payload.get("z"),
        "coordinateType": payload.get("coordinateType"),
        "speed": payload.get("speed", DEFAULT_SPEED)
    }