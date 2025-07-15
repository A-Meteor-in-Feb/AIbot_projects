from flask import Flask, request, jsonify
import os, base64
from datetime import datetime 

app = Flask(__name__)

UPLOAD_DIR = 'images'
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.route('/api/robots/<string:robotId>/images', methods=['POST'])
def get_image(robotId):
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

    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000)