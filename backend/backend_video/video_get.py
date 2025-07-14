from fastapi import FastAPI, Depends, HTTPException, Header
from starlette.responses import StreamingResponse
import requests
import uvicorn

app = FastAPI()


def verify_token(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    token = authorization.split(" ", 1)[1]
    # TODO: examine whether it is available
    return token

@app.get("/camera/video-stream")
def proxy_mjpeg():
    
    url = f"http://127.0.0.1:8001/camera/video-stream"

    response = requests.get(url, stream=True, timeout=(5, None), verify=False)
    
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Robot stream error")

    content_type = response.headers.get(
        "Content-Type",
        "multipart/x-mixed-replace; boundary=--frame"
    )

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