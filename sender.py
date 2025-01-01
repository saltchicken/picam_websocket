import io
import asyncio
import websockets
import cv2
import numpy as np
from picamera2 import Picamera2, Preview
import ssl

# Initialize Picamera2
picam2 = Picamera2()
video_config = picam2.create_video_configuration(main={"size": (640, 480)})
fps = 10
frame_duration = int(1e6 / fps)
video_config["controls"]["FrameDurationLimits"] = (frame_duration, frame_duration)

picam2.configure(video_config)
picam2.start()




async def send_video(websocket):
    while True:
        frame = picam2.capture_array()
        _, jpeg = cv2.imencode('.jpg', frame)
        jpeg_bytes = jpeg.tobytes()
        
        await websocket.send(jpeg_bytes)
        await asyncio.sleep(0.01)

async def receive_messages(websocket):
    async for message in websocket:
        print(f"Received from client: {message}")
        try:
            command = message.split("=")
            if command[0] == "focus" and len(command) == 2:
                new_focus = float(command[1])
                print(new_focus)
                # await websocket.send(f"DEBUG: message received {new_frequency}")
            else:
                print("Invalid command")
        except ValueError:
            print("ValueError")
            # await websocket.send("Invalid command format")

async def handler(websocket):
    print("Client connected")
    sender_task = asyncio.create_task(send_video(websocket))
    receiver_task = asyncio.create_task(receive_messages(websocket))

    done, pending = await asyncio.wait(
            [sender_task, receiver_task],
            return_when=asyncio.FIRST_COMPLETED,
            )
    for task in pending:
        task.cancel()

    print("Client disconnected")

async def main():
    server = await websockets.serve(handler, "0.0.0.0", 8765)
    print("WebSocket server started on ws://localhost:8765")
    await server.wait_closed()

# Start the event loop
asyncio.run(main())
