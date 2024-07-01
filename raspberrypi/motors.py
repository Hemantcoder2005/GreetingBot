import RPi.GPIO as GPIO
import time
import pygame
import socket
import os
from random import randint

# Constants
OBSTACLE_DISTANCE = 15  # cm(by changing this, you can control when to stop or what is the threshold radius of the robot(modify this according to your robot's speed))
DISTANCE_SLEEP = 0.05
MOTOR_CONTROL_SLEEP = 0.1
TURN_DURATION = 0.5
PLAYBACK_DELAY = 1
HOST = '127.0.0.1'
PORT = 65432

# GPIO setup
GPIO.setmode(GPIO.BOARD)
SENSOR_PINS = {
    'central': {'trigger': 16, 'echo': 18}, #these PINs are physical PINs(odd on the left side and even the right side if you hold it from the USB side )
    'right': {'trigger': 33, 'echo': 35},
    'left': {'trigger': 38, 'echo': 40}
}
MOTOR_PINS = {
    'motora_in1': 11,
    'motora_in2': 13,
    'motorb_in3': 15,
    'motorb_in4': 37
}

for sensor in SENSOR_PINS.values():
    GPIO.setup(sensor['trigger'], GPIO.OUT)
    GPIO.setup(sensor['echo'], GPIO.IN)

for pin in MOTOR_PINS.values():
    GPIO.setup(pin, GPIO.OUT)

# Initialize pygame mixer
pygame.mixer.init()

# Load sounds
SOUND_DIRECTORY = os.path.join(os.curdir, 'sounds/')
sound_files = [file for file in os.listdir(SOUND_DIRECTORY) if file.endswith(('.mp3', '.wav'))]
InitializedSounds = [pygame.mixer.Sound(os.path.join(SOUND_DIRECTORY, sound)) for sound in sound_files]

print("\033[92m {}\033[00m".format("Audio Files Loaded Successfully!"))

# Function to measure distance
def distance(trigger, echo):
    # Ensure trigger is low
    GPIO.output(trigger, False)
    time.sleep(0.05)

    # Send a short 10us pulse to trigger
    GPIO.output(trigger, True)
    time.sleep(0.00001)
    GPIO.output(trigger, False)

    start_time = time.time()
    stop_time = time.time()

    # Save start_time
    while GPIO.input(echo) == 0:
        start_time = time.time()

    # Save stop_time
    while GPIO.input(echo) == 1:
        stop_time = time.time()

    # Time difference between start and arrival
    elapsed_time = stop_time - start_time

    # Calculate distance
    dist = (elapsed_time * 34300) / 2
    return dist
# Motor control functions
def set_motor_state(forward_left, backward_left, forward_right, backward_right):
    GPIO.output(MOTOR_PINS['motora_in1'], forward_left)
    GPIO.output(MOTOR_PINS['motora_in2'], backward_left)
    GPIO.output(MOTOR_PINS['motorb_in3'], forward_right)
    GPIO.output(MOTOR_PINS['motorb_in4'], backward_right)

def stop():
    set_motor_state(False, False, False, False)

def forward():
    set_motor_state(True, False, True, False)

def backward():
    set_motor_state(False, True, False, True)

def left():
    set_motor_state(True, False, False, True)

def right():
    set_motor_state(False, True, True, False)

def move(dist_central, dist_left, dist_right):
    print("Central: {:.2f} cm, Left: {:.2f} cm, Right: {:.2f} cm".format(dist_central, dist_left, dist_right))
    if dist_central < OBSTACLE_DISTANCE:
        print("Obstacle detected")
        stop()
        time.sleep(0.5)
        if dist_left < dist_right:
            right()
            print("Turning right")
            time.sleep(TURN_DURATION)
        else:
            left()
            print("Turning left")
            time.sleep(TURN_DURATION)
    elif dist_left < OBSTACLE_DISTANCE:
        right()
        print("Turning right")
        time.sleep(TURN_DURATION)
    elif dist_right < OBSTACLE_DISTANCE:
        left()
        print("Turning left")
        time.sleep(TURN_DURATION)
    else:
        forward()
        print("Moving forward")
    time.sleep(MOTOR_CONTROL_SLEEP)

def server_program():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        conn, addr = s.accept()
        with conn:
            print(f"\033[92m Connected by {addr}\033[00m")
            sound_stack = []
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                message = data.decode('utf-8')
                if message == 'stop':
                    stop()
                elif message == 'move':
                    dist_central = distance(SENSOR_PINS['central']['trigger'], SENSOR_PINS['central']['echo'])
                    dist_left = distance(SENSOR_PINS['left']['trigger'], SENSOR_PINS['left']['echo'])
                    dist_right = distance(SENSOR_PINS['right']['trigger'], SENSOR_PINS['right']['echo'])
                    if not pygame.mixer.get_busy():
                        move(dist_central, dist_left, dist_right)
                elif message == 'greet':
                    sound_stack.append(InitializedSounds[randint(0, len(InitializedSounds) - 1)])
                    if sound_stack and not pygame.mixer.get_busy():
                        time.sleep(PLAYBACK_DELAY)
                        play = sound_stack.pop().play()

try:
    while True:
       server_program()
except Exception as e:
    print(f"\033[91m {e}\033[00m")
finally:
    GPIO.cleanup()
