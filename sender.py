import io
import asyncio
import websockets
import cv2
import numpy as np
import libcamera
from picamera2 import Picamera2, Preview
import ssl
import time

# Initialize Picamera2
picam2 = Picamera2()
video_config = picam2.create_video_configuration(main={"size": (640, 480), "format": 'RGB888'})
fps = 10
frame_duration = int(1e6 / fps)
video_config["controls"]["FrameDurationLimits"] = (frame_duration, frame_duration)
video_config["transform"] = libcamera.Transform(hflip=1, vflip=1)

picam2.configure(video_config)
picam2.start()
time.sleep(2)

size = picam2.capture_metadata()['ScalerCrop'][2:]
full_res = picam2.camera_properties['PixelArraySize']

print("size")
print(picam2.capture_metadata()['ScalerCrop'])
print(size)
print(full_res)



async def send_video(websocket):
    while True:
        frame = picam2.capture_array()
        _, jpeg = cv2.imencode('.jpg', frame)
        jpeg_bytes = jpeg.tobytes()
        
        try:
            await websocket.send(jpeg_bytes)
        except:
            print("I think this is caused by disconnecting")
        await asyncio.sleep(0.01)

async def receive_messages(websocket):
    async for message in websocket:
        print(f"Received from client: {message}")
        try:
            command = message.split("=")
            if command[0] == "focus" and len(command) == 2:
                new_focus = float(command[1])
                picam2.set_controls({"AfMode": 0, "LensPosition": int(new_focus)})
                print(int(new_focus))
                # await websocket.send(f"DEBUG: message received {new_frequency}")
            elif command[0] == "zoom" and len(command) == 2:
                current_offset = picam2.capture_metadata()['ScalerCrop'][:2]
                new_zoom = command[1]
                if new_zoom == "up":
                    current_offset[1] += 10
                    picam2.set_control({"ScalerCrop": (current_offset[0], current_offset[1], 3840, 2880)})
                    print("Zooming up")
                elif new_zoom == "down":
                    current_offset[1] -= 10
                    picam2.set_controls({"ScalerCrop": (current_offset[0], current_offset[1], 3840, 2880)})
                    print("Zooming down")

                else:
                    print("Invalid zoom direction")

                # picam2.set_controls({"ScalerCrop": (100, 100, 3840, 2880)})
                # print("Received zoom")
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
