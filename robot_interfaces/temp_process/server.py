from flask import Flask
from flask import request
from flask import jsonify
from flask import Blueprint
import time

from flask import Flask, jsonify
from werkzeug.serving import make_server
from threading import Thread

def now_ms() -> int:
    return int(time.time() * 1000)

class HttpServer:
    def __init__(self, head: str, host: str, port: str, robotId: str, skew_ms: int):
        self.head = head
        self.host = host
        self.port = port
        self.base_url = f"{self.head}://{self.host}:{self.port}"
        self.skew_ms = skew_ms

        self.robotId = robotId

        self.bp = Blueprint("robot_api", __name__)
        self.bp.add_url_rule(
            "/api/robot/server/task",
            view_func=self.handle_task,
            methods = ["POST"]
        )
    
    def handle_task(self):
        """
        content-type 不写是json的话会报415的错误
        """
        #headers = request.headers
        data = request.get_json()
        #data = request.get_data().decode("utf-8")
        print(data)
        return jsonify({"status": "ok"}), 200


def create_flask_app(server_bp):
    app = Flask(__name__)
    app.register_blueprint(server_bp)

    @app.route("/healthz")
    def healthz():
        return jsonify({"status": "ok"}), 200
    
    return app

def start_flask_in_thread(flask_app, host, port):
    class ServerThread(Thread):
        def __init__(self):
            super().__init__(daemon=False)
            self.srv = make_server(host, port, flask_app)
            self.ctx = flask_app.app_context()
            self.ctx.push()

        def run(self):
            self.srv.serve_forever()

        def shutdown(self):
            self.srv.shutdown()

    thr = ServerThread()
    thr.start()
    return thr


if __name__ == "__main__":
    ROBOTID = "18950214603"
    SKEW_MS = 2 * 60 * 1000

    srv = HttpServer("http", "10.25.0.5", 8000, ROBOTID, SKEW_MS)
    flask_app = create_flask_app(srv.bp)
    flask_thread = start_flask_in_thread(flask_app, "10.25.0.5", 8000)

    try:
        flask_thread.join()  # 阻塞在这里
    except KeyboardInterrupt:
        flask_thread.shutdown()