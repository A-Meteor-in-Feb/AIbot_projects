from flask import Flask
from flask import Response
from flask import request
from flask import abort
import cv2
import os


BACKEND_VALID_TOKENS = {
    "B1234": "12345ABCDEF"
}

app = Flask(__name__)


def frame_generator():
    
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


@app.route('/camera/stream')
def video_stream():
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        abort(401, description="Missing authorization header")

    parts = auth_header.split()
    token = parts[1]

    if token != BACKEND_VALID_TOKENS.get("B1234"):
        abort(401, description="Invalid token")

    return Response(
        frame_generator(),
        mimetype='multipart/x-mixed-replace; boundary=--frame'
    )


if __name__ == '__main__':
    context = ("cert.pem", "key.pem")
    app.run(host='127.0.0.1', port=8443, ssl_context=context)