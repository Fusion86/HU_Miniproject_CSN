# Server connection
SERVER = "192.168.0.30"
SERVER_PORT = 5000

# LED
RED_LED_BCM = 5
BLUE_LED_BCM = 6

# Keypad
USE_KEYPAD = True
KEYPAD_MATRIX = [[1, 2, 3, "A"], [4, 5, 6, "B"], [7, 8, 9, "C"], ["*", 0, "#", "D"]]
KEYPAD_ROWS = [2, 3, 4, 17]
KEYPAD_COLS = [27, 22, 9, 10]
KEYPAD_CODE = ["#", 4, 2, 0] # Code to disable alarm
