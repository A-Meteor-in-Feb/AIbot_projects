from flask import Flask
from flask import Response
from flask import request
from flask import abort
from flask import send_from_directory
import requests
import os

ROBOT_IP = "127.0.0.1"
ROBOT_PORT = "8443"
BACKEND_TOKEN = "12345ABCDEF"


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, static_folder=BASE_DIR, static_url_path='')


@app.route('/', defaults={'path': 'test.html'})
def serve(path):
    full_path = os.path.join(BASE_DIR, path)
    if os.path.isfile(full_path):
        return send_from_directory(BASE_DIR, path)
    else:
        abort(404)


@app.route('/api/robots/<robotId>/video-stream', methods=['GET'])
def proxy_mjpeg(robotId):
   
    url = f"https://{ROBOT_IP}:{ROBOT_PORT}/camera/stream"

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


if __name__ == '__main__':
    context = ("cert.pem", "key.pem")
    app.run(host='127.0.0.1', port=8444, ssl_context=context)