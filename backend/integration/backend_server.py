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

TEST_ROBOT_HOST = "127.0.0.1"
TEST_ROBOT_PORT = 8443
TEST_BACKEND_HOST = "127.0.0.1"
TEST_BACKEND_PORT = 8444

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

@app.route('/api/robots/<string:robotId>/images', methods=['POST'])
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
    context = ("cert.pem", "key.pem")
    app.run(host=TEST_BACKEND_HOST, port=TEST_BACKEND_PORT, ssl_context=context)
