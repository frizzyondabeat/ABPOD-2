#!/usr/bin/python3.10
import RPi.GPIO as GPIO
import subprocess
import time

GPIO.setmode(GPIO.BOARD) # use GPIO numbering
GPIO.setwarnings(False)

# Use GPIO 29 for the switch
SWITCH = 40

GPIO.setup(SWITCH, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def main():
    # Keep track of the state of the switch
    prev_state = False

    while True:
        # Read the current state of the switch
        curr_state = GPIO.input(SWITCH)

        # Check if the state of the switch has changed
        if curr_state != prev_state:
            print("Shutdown sequence initiated!\nYou have 10 seconds to abort the sequence")
            # Wait for 10secs incase the user changes choice
            time.sleep(10)

            # Read the state of the switch again to make sure it has settled
            curr_state = GPIO.input(SWITCH)

            # If the state of the switch has stabilized, and it is now in the "off" position
            if curr_state == True:
                for i in range(10, 0, -1):
                    countdown_message = f"Shutting down in {i} seconds..."
                    print(countdown_message, end='\r')
                    time.sleep(1)
                # Initiate a shutdown procedure on the Pi
                subprocess.call(['poweroff'], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            else:
                print("Shutdown aborted")
        # Update the previous state of the switch
        prev_state = curr_state

if __name__ == '__main__':
    main()
