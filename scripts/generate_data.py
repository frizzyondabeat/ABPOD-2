from pyfirmata import Arduino, util, INPUT
import time
import termios
import sys
import tty
from l298n import L298N
import cv2
import pandas as pd
import os


port = "/dev/ttyACM0"
board = Arduino(port)
motor = L298N(board=board, in1=2, in2=4, ena=3, in3=7, in4=8, enb=5)

csv_filename = "driving_data.csv"
csv_columns = ["Frame", "Steering Angle", "Speed"]
csv_data = []


it = util.Iterator(board)
it.start()
board.analog[0].mode = INPUT
#%% setup servo on pin 9
servo = board.get_pin('d:9:s') # pin to communicate to the servo with

# Keyboard control
def getch():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch


def map_value(value, in_min, in_max, out_min, out_max):
    return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


def forward(speed, delay):
    motor.forward(speed, delay)


def reverse(speed, delay):
    motor.backward(speed, delay)


def stop(delay):
    motor.full_stop(delay)

def precise_angle(angle):
    if angle >= -40 and angle <= 40:
        servo.write(map_value(angle, -90, 90, 0, 180))

def precise_speed(speed:float):
    if speed >= 0.0 and speed <= 1.0:
        motor.drive_motors(speed)

def capture_frames(steering_angle, speed):
    # Capture frame from camera
    cap = cv2.VideoCapture('/dev/video0', cv2.CAP_V4L)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if cap.isOpened():
        _, frame = cap.read()

        filename = f"images/frame_{time.time()}.jpg"
        filename = os.path.abspath(filename)
        # Save the frame to a file
        cv2.imwrite(filename, frame)

        csv_data.append({"Frame": filename, "Steering Angle": steering_angle, "Speed": speed})


angle = 0
speed = 0.4
print("Starting control")
servo.write(map_value(angle, -90, 90, 0, 180))

try:
    while True:
        feedback = board.analog[0].read()
        if feedback is None:
            feedback = 0.0

        capture_frames(feedback, speed)

        key = getch().lower() # ensure every letter pressed is in lowercase
        if key == "a": # check if a is pressed
            print("Steering left")
            if angle > -40:     # check to make sure new angle will not exceed 180 degrees
                angle = angle - 2   # if new angle is OK, change to it
                servo.write(map_value(angle, -90, 90, 0, 180))    # set servo position to new angle by calling the function we made earlier
                time.sleep(0.1)      # wait a little bit (0.1 seconds) before checking again

        elif key == "d":
            print("Steering right")
            if angle < 40:         # check to make sure new angle will not exceed 0 degrees
                angle = angle + 2
                servo.write(map_value(angle, -90, 90, 0, 180))
                time.sleep(0.1)

        elif key == "w":
            print("Forward")
            forward(speed, 1)

        elif key == "s":
            print("Reverse")
            reverse(speed, 1)

        elif key == "e":
            print("Braking")
            motor.drive_motors(0)
            stop(0)

        elif key == "+":
            if speed < 1:         # check to make sure new angle will not exceed 0 degrees
                speed = speed + 0.01
                print(f"Increasing speed to {speed}")
                motor.drive_motors(speed)

        elif key == "-":
            if speed > 0:
                speed = speed - 0.01
                print(f"Reducing speed to {speed}")
                motor.drive_motors(speed)

        elif key == "p":
            angle = int(input("Enter the precise steering angle:\t"))
            precise_angle(angle)

        elif key == "j":
            speed = float(input("Enter the precise speed:\t"))
            precise_speed(speed)

        elif key == "q":
            # Convert CSV data to DataFrame
            df = pd.DataFrame(csv_data, columns=csv_columns)

            # Write DataFrame to CSV file
            df.to_csv(csv_filename, index=False)

            # Print completion message
            print("Data saved to", csv_filename)
            print("Quitting")
            sys.exit(0)

        capture_frames(feedback, speed)


except Exception as e:
    df = pd.DataFrame(csv_data, columns=csv_columns)

    # Write DataFrame to CSV file
    df.to_csv(csv_filename, index=False)

    # Print completion message
    print("\nData saved to", csv_filename)
    print("Quitting")
    print(f"Exception: {e}")
