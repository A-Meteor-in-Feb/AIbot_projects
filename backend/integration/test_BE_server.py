#as a server
import os
import base64
import requests
from flask import Flask
from flask import request
from flask import jsonify
from flask import Response
from flask import abort
from flask import send_from_directory
from datetime import datetime
from datetime import timezone
from datetime import timedelta

# self-defined class
from backend_cargoInfo import Item, CargoBin, Inventory
from backend_cargoInfo import Order, Orders, OrderInfo

HTTP_HEAD = "https"
SIMULATOR_HOST = "rob1.ibc-ai.com"
SIMULATOR_PORT = 8443

ROBOT_ID_1 = "R1234"
ROBOT_VALID_TOKENS = {
    ROBOT_ID_1: "ABCDEF12345"
}
BACKEND_ID = "B1234"
BACKEND_TOKEN = "12345ABCDEF"


app = Flask(__name__)

@app.route('/api/JKROBOT/<string:robotId>/auth-code', methods=['GET'])
def get_authCode(robotId):


    data = request.get_json(force=True)
    
    utc_now = datetime.now(timezone.utc)
    # For now, set the message expiry time as 5 minutes later
    expiry = utc_now + timedelta(minutes=5) 
    expiry_timestamp = expiry.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    
    # Assign a new expiry timestamp and a new auth-code
    new_expiry_timestamp = expiry_timestamp
    new_auth_code = "AABBCC"
    

    result = {
        "success": True,
        "order_id": 1234,
        "auth_code": new_auth_code,
        "expires_at": new_expiry_timestamp
    }

    return jsonify(result), 200 if result["success"] == True else 400


@app.route('/api/JKROBOT/<string:robotId>/task-complete', methods=['POST'])
def taskComplete_notification(robotId):

    
    data = request.get_json(force=True)
    print(data)
    result = {
        "success": True
    }

    return jsonify(result), 200 if result["success"] == True else 400



if __name__ == "__main__":

    #context = ("cert.pem", "key.pem")
    #app.run(host=TEST_BACKEND_HOST, port=TEST_BACKEND_PORT, ssl_context=context)
    app.run(host="0.0.0.0", port=8889)