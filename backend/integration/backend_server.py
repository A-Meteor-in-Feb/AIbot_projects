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

ROBOT_HTTP = 80
ROBOT_HTTPS = 8443
BACKEND_HTTP = 81
BACKEND_HTTPS = 8444

TEST_ROBOT_HOST = "127.0.0.1"
TEST_ROBOT_PORT = ROBOT_HTTP
TEST_BACKEND_HOST = "127.0.0.1"
TEST_BACKEND_PORT = BACKEND_HTTP

ROBOT_ID_1 = "R1234"
ROBOT_VALID_TOKENS = {
    ROBOT_ID_1: "ABCDEF12345"
}
BACKEND_ID = "B1234"
BACKEND_TOKEN = "12345ABCDEF"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_folder=BASE_DIR, static_url_path='')

UPLOAD_DIR = 'images'
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.route('/api/JKROBOT/<string:robotId>/images', methods=['POST'])
def get_image(robotId):
    """
        Process the image uploaded from the robot.
    """
    header = request.headers
    token = header.get('Authorization')[7:]
    if token != ROBOT_VALID_TOKENS[robotId]:
        result = {"status": "Unauthorized"}
        return jsonify(result), 401
    else:
        print("Authentication Passed.")

    #JSON Base64
    if request.is_json:
        data = request.get_json(force=True)
        taskId = data.get("taskId")
        type = data.get("type")
        timestamp = data.get("timestamp")
        img_base64 = data.get("image")

        try:
            img_data = base64.b64decode(img_base64)
        except Exception:
            return jsonify({"status:": "error", "message":"Base64 Decode Failed"}), 400

        timestamp_str = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).strftime('%Y%m%dT%H%M%SZ')
        file_name = f"{robotId}_{taskId}_{type}_{timestamp_str}.jpg"
        path = os.path.join(UPLOAD_DIR, file_name)
        with open(path, 'wb') as f:
            f.write(img_data)
            print("stored image already")

    elif 'file' in request.files:
        file = request.files['file']
        taskId = request.form.get("taskId")
        type = request.form.get("type")
        timestamp = request.form.get("timestamp")

        timestamp_str = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).strftime('%Y%m%dT%H%M%SZ')
        file_name = f"{robotId}_{taskId}_{type}_{timestamp_str}.jpg"
        path = os.path.join(UPLOAD_DIR, file_name)
        file.save(path)

        print("stored image already")
    
    else:
        return jsonify({"status": "Unsupported Media Type"}), 415

    return jsonify({"status": "ok"}), 200


@app.route('/api/JKROBOT/<string:robotId>/cargo', methods=['GET'])
def get_cargo_binId(robotId):

    data = request.get_json(force=True)
    parameters = data.get('params', {})

    bin_id = parameters.get("binId")

    #TODO: call the function to get the specific info of the cargo

    utc_now = datetime.now(timezone.utc)
    utc_timestamp = utc_now.replace(microsecond=0).isoformat().replace("+00:00", "Z")

    result = {
        "success": True,
        "robotId": robotId,
        "binId": bin_id,
        "cargo":{
            "items": [{
                "name": "商品",
                "quantity": 5,
                "weight": 1.2,
                "category": "food"
            }],
            "totalWeight": 6.0,
            "capacity": 10,
            "utilization": 0.5
        },
        "timestamp": utc_timestamp
    }

    return jsonify(result), 200 if result["success"] == True else 400


@app.route('/api/JKROBOT/<string:robotId>/cargo/inventory', methods=['GET'])
def get_cargo_inventory(robotId):
    """
        Return the cargo information of the inventory
    """
    #TODO: call the function to get the specific info of the cargo's inventory

    utc_now = datetime.now(timezone.utc)
    utc_timestamp = utc_now.replace(microsecond=0).isoformat().replace("+00:00", "Z")

    result = {
        "success": True,
        "robotId": "robot001",
        "inventory": {
            "bins": [{
                "binId": 1,
                "items": [],
                "totalWeight": 0,
                "capacity": 10,
                "utilization": 0
            },
            {
                "binId": 2,
                "items": [{
                    "name": "商品A",
                    "quantity": 5,
                    "weight": 1.2
                }],
                "totalWeight": 6.0,
                "capacity": 10,
                "utilization": 0.5
            }],
            "totalCapacity": 60,
            "totalUtilization": 0.1
        },
        "timestamp": utc_timestamp
    }

    return jsonify(result), 200 if result["success"] == True else 400


@app.route('/api/JKROBOT/orders', methods=['GET'])
def get_orders():
    data = request.get_json(force=True)
    parameters = data.get('params', {})

    robotId = parameters.get("robotId")
    taskId = parameters.get("taskId")
    status = parameters.get("status")

    #TODO: call the function to get the specific info of the result

    utc_now = datetime.now(timezone.utc)
    utc_timestamp = utc_now.replace(microsecond=0).isoformat().replace("+00:00", "Z")

    result = {
        "success": True,
        "orders": [{
            "order_id": "ORD20250707123001",
            "cargo_bind_id": "COKE_001",
            "customer_name": "张三",
            "delivery_address": "1-2-101",
            "delivery_lat": 1.2966,
            "delivery_lng": 103.7764,
            "quantity": 2,
            "status": status,
            "assigned_robot_id": robotId,
            "created_at": utc_timestamp
        }]
    }

    return jsonify(result), 200 if result["success"] == True else 400


@app.route('/api/JKROBOT/<string:robotId>/notify-pickup', methods=['POST'])
def notify_pickup(robotId):
    data = request.get_json(force=True)
    parameters = data.get('params', {})

    order_id = parameters.get("order_id")

    #TODO: call the function to get the specific info of the result

    utc_now = datetime.now(timezone.utc)
    # For now, set the message expiry time as 5 minutes later
    expiry = utc_now + timedelta(minutes=5) 
    expiry_timestamp = expiry.replace(microsecond=0).isoformat().replace("+00:00", "Z")

    result = {
        "success": True,
        "order_id": order_id,
        "auth_code": "A1B2C3",
        "expires_at": expiry_timestamp,
        "message": "通知已发送, 验证码有效"
    }

    return jsonify(result), 200 if result["success"] == True else 400


@app.route('/api/JKROBOT/<string:robotId>/auth-code', methods=['GET'])
def get_authCode(robotId):

    data = request.get_json(force=True)
    parameters = data.get('params', {})

    order_id = parameters.get("order_id")

    #TODO: call the function to get the specific info of the result

    utc_now = datetime.now(timezone.utc)
    # For now, set the message expiry time as 5 minutes later
    expiry = utc_now + timedelta(minutes=5) 
    expiry_timestamp = expiry.replace(microsecond=0).isoformat().replace("+00:00", "Z")

    result = {
        "success": True,
        "order_id": order_id,
        "auth_code": "A1B2C3",
        "expires_at": expiry_timestamp
    }

    return jsonify(result), 200 if result["success"] == True else 400


@app.route('/api/JKROBOT/<string:robotId>/task-complete', methods=['POST'])
def taskComplete_notification(robotId):

    data = request.get_json(force=True)
    parameters = data.get('params', {})

    order_id = parameters.get("order_id")

    #TODO: call the function to change the order's status and get the accurate result

    result = {
        "success": True
    }

    return jsonify(result), 200 if result["success"] == True else 400


@app.route('/', defaults={'path': 'test.html'})
def serve(path):
    """
        Access to the test.html 
    """
    full_path = os.path.join(BASE_DIR, path)
    if os.path.isfile(full_path):
        return send_from_directory(BASE_DIR, path)
    else:
        abort(404)


@app.route('/api/robots/<robotId>/video-stream', methods=['GET'])
def proxy_mjpeg(robotId):
    """
        Get video stream from robot side, then forward to the fronend.
    """
   
    url = f"https://{TEST_ROBOT_HOST}:{TEST_ROBOT_PORT}/camera/stream"

    headers = {
        "Authorization": f"Bearer {BACKEND_TOKEN}"
    }

    response = requests.get(
        url=url,
        headers=headers,
        stream=True,
        timeout=(5, None),
        verify="cert.pem"
    )

    if response.status_code != 200:
        abort(response.status_code, description="Robot stream error")

    content_type = response.headers.get(
        "Content-Type",
        "multipart/x-mixed-replace; boundary=--frame"
    )

    return Response(
        response.iter_content(chunk_size=1024),
        mimetype=content_type
    )

if __name__ == "__main__":
    #context = ("cert.pem", "key.pem")
    #app.run(host=TEST_BACKEND_HOST, port=TEST_BACKEND_PORT, ssl_context=context)
    app.run(host=TEST_BACKEND_HOST, port=TEST_BACKEND_PORT)