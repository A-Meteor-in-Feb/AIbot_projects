from fastapi import FastAPI, Depends, HTTPException, Header
from starlette.responses import StreamingResponse
import requests
import uvicorn

ROBOT_IP = "127.0.0.1"
ROBOT_PORT = "8001"
BACKEND_TOKEN = "12345ABCDEF"

app = FastAPI()


@app.get("/api/robots/{robotId}/video-stream")
def proxy_mjpeg(robotId: str):
    
    url = f"http://{ROBOT_IP}:{ROBOT_PORT}/camera/stream"
    headers = {
        "Authorization": f"Bearer {BACKEND_TOKEN}"
    }
    response = requests.get(url=url, headers=headers ,stream=True, timeout=(5, None), verify=False)
    
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Robot stream error")

    content_type = response.headers.get("Content-Type","multipart/x-mixed-replace; boundary=--frame")
    
    return StreamingResponse(
        response.iter_content(chunk_size=1024),
        media_type=content_type
    )


if __name__ == "__main__":

    uvicorn.run(
        "video_get:app",
        host = "127.0.0.1",
        port = 8000,
        reload = True #Used in development, it will reload after your change your codes
    )