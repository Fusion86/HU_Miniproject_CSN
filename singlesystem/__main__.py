import RPi.GPIO as GPIO
import curses
from curses import wrapper
from time import sleep

LASER_GPIO = 17
SENSOR_GPIO = 23


def get_laser_visible():
    return not GPIO.input(SENSOR_GPIO)


def get_laser_enabled():
    return bool(GPIO.input(LASER_GPIO))


def main(stdscr):
    def draw(scr):
        # Clear
        scr.clear()

        # Draw
        scr.addstr(0, 0, "HU Miniproject V1O Groep 1 - CSN Alarmsysteem")
        scr.addstr(1, 0, "Version: v0.0.0 (commit 4B6174)")

        scr.addstr(3, 0, "Laser enabled: " + str(get_laser_enabled()))
        scr.addstr(4, 0, "Laser visible: " + str(get_laser_visible()))

        scr.addstr(6, 0, "t - toggle laser")
        scr.addstr(7, 0, "q - quit")

        scr.refresh()

    def toggle_laser():
        if (GPIO.input(LASER_GPIO)):
            GPIO.output(LASER_GPIO, GPIO.LOW)
        else:
            GPIO.output(LASER_GPIO, GPIO.HIGH)

    curses.curs_set(0)  # Disable cursor
    stdscr.nodelay(True)  # Make getch() non-blocking

    actions = {
        ord('t'): toggle_laser
    }

    # Main loop
    while True:
        draw(stdscr)

        c = stdscr.getch()

        if c == ord('q'):
            break
        elif c in actions:
            actions[c]()  # Execute action
        else:
            sleep(0.2)


if __name__ == '__main__':
    # Setup laser
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(LASER_GPIO, GPIO.OUT)

    # Setup ldr
    GPIO.setup(SENSOR_GPIO, GPIO.IN)

    # curses
    wrapper(main)

    # Cleanup GPIO
    GPIO.output(LASER_GPIO, GPIO.LOW)
    GPIO.cleanup()
