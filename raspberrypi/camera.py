import requests
import cv2
import os
import socket

# Constants
SERVER_URL = 'http://192.168.3.30:5000/upload'
CAMERA_INDEX = 0
HOST = '127.0.0.1'
PORT = 65432

# Initialize camera
cap = cv2.VideoCapture(CAMERA_INDEX)
if cap.isOpened():
    print("\033[92m {}\033[00m".format("Camera Connected!"))
else:
    print("\033[91m {}\033[00m".format("No Camera Found!"))

def send_message(message):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            s.sendall(message.encode('utf-8'))
    except Exception as e:
        print(f"\033[91m {e}\033[00m")

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        response = requests.post(SERVER_URL, data=frame_bytes).json()

        if response.get('greet'):
            send_message('greet')
            print("\033[92m {}\033[00m".format("Greet!"))

        if response.get('quit'):
            print("\033[91m {}\033[00m".format("Server Stopped!"))
            break

        if response['persons'] != 0:
            send_message('stop')
            print("\033[91m {}\033[00m".format("Person Detected!"))
        else:
            send_message('move')

        print(response)

except Exception as e:
    print(f"\033[91m {e}\033[00m")
    print("\033[91m {}\033[00m".format("Connection Closed!"))
finally:
    cap.release()