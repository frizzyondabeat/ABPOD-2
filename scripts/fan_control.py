#!/usr/bin/python3.10
import subprocess
import time
import RPi.GPIO as GPIO


ON_THRESHOLD = 55  # (degrees Celsius) Fan kicks on at this temperature.
OFF_THRESHOLD = 42  # (degress Celsius) Fan shuts off at this temperature.
SLEEP_INTERVAL = 5  # (seconds) How often we check the core temperature.
FAN_PIN = 8  # Which BOARD pin you're using to control the fan.

GPIO.setwarnings(False) # Ignore warning for now
GPIO.setmode(GPIO.BOARD)
GPIO.setup(FAN_PIN, GPIO.OUT, initial=GPIO.LOW)

def get_temp():
    """Get the core temperature.
    Run a shell script to get the core temp and parse the output.
    Raises:
        RuntimeError: if response cannot be parsed.
    Returns:
        float: The core temperature in degrees Celsius.
    """
    output = subprocess.run(['vcgencmd', 'measure_temp'], capture_output=True)
    temp_str = output.stdout.decode()
    try:
        return float(temp_str.split('=')[1].split('\'')[0])
    except (IndexError, ValueError):
        raise RuntimeError('Could not parse temperature output.')


if __name__ == '__main__':
    # Validate the on and off thresholds
    if OFF_THRESHOLD >= ON_THRESHOLD:
        raise RuntimeError('OFF_THRESHOLD must be less than ON_THRESHOLD')

    while True:
        temp = get_temp()
        degree_sign = u"\N{DEGREE SIGN}"
        # Start the fan if the temperature has reached the limit and the fan
        # isn't already running.
        # NOTE: `fan.value` returns 1 for "on" and 0 for "off"
        if temp > ON_THRESHOLD and not GPIO.input(FAN_PIN):
            print(f"System overheating!\nTemperature:\t{temp}{degree_sign}C\nSwitching ON cooling fan")
            GPIO.output(FAN_PIN, GPIO.HIGH)

        # Stop the fan if the fan is running and the temperature has dropped
        # to 10 degrees below the limit.
        elif GPIO.input(FAN_PIN) and temp < OFF_THRESHOLD:
            print(f"System cooled\nTemperature:\t{temp}{degree_sign}C\nTurning OFF the fan")
            GPIO.output(FAN_PIN, GPIO.LOW)

        time.sleep(SLEEP_INTERVAL)