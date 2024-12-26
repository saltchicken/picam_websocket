import io
import asyncio
import websockets
import cv2
import numpy as np
from picamera2 import Picamera2, Preview

# Initialize Picamera2
picam2 = Picamera2()
video_config = picam2.create_video_configuration(main={"size": (1920, 1080)})
fps = 30
frame_duration = int(1e6 / fps)
video_config["controls"]["FrameDurationLimits"] = (frame_duration, frame_duration)

picam2.configure(video_config)
picam2.start()

# Set up the WebSocket server
async def video_stream(websocket):
    print("Client connected")
    while True:
        # Capture a frame from the camera
        frame = picam2.capture_array()
        
        # Convert the frame to JPEG
        _, jpeg = cv2.imencode('.jpg', frame)
        jpeg_bytes = jpeg.tobytes()
        
        # Send the frame over WebSocket
        await websocket.send(jpeg_bytes)

async def main():
    # Start the WebSocket server
    server = await websockets.serve(video_stream, "0.0.0.0", 8765)
    print("WebSocket server started on ws://localhost:8765")
    
    
    await server.wait_closed()

# Start the event loop
asyncio.run(main())
