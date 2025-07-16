from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import StreamingResponse
import cv2
import uvicorn
import os


BACKEND_VALID_TOKENS = {
    "B1234": "12345ABCDEF"
}


app = FastAPI()


def frame_generator():

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    VIDEO_PATH = os.path.join(BASE_DIR, "videos", "test_video.mp4")
    #cap = cv2.VideoCapture(0)
    cap = cv2.VideoCapture(VIDEO_PATH)
    if not cap.isOpened():
        raise RuntimeError("Cannot open test video file")
    
    try:
        while True:
            success, frame = cap.read()

            if not success:
                #Read to the ending, reset to the start and continue playing
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

@app.get("/camera/stream")
def video_stream(authorization: str = Header(None)):

    if authorization is None:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    authorization_parts = authorization.split()
    token = authorization_parts[1]

    if token != BACKEND_VALID_TOKENS["B1234"]:
        raise HTTPException(status_code=401, detail="Invalid token")

    return StreamingResponse(
        frame_generator(),
        media_type="multipart/x-mixed-replace; boundary=--frame"
    )

if __name__ == "__main__":
    uvicorn.run(
        "video_stream:app",
        host = "127.0.0.1",
        port = 8001,
        reload = True
    )