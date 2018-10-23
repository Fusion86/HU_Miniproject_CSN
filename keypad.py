import RPi.GPIO as GPIO
from time import sleep

GPIO.setmode(GPIO.BCM)

MATRIX = [[1, 2, 3, "A"], [4, 5, 6, "B"], [7, 8, 9, "C"], ["*", 0, "#", "D"]]

ROWS = [2, 3, 4, 17]
COLS = [27, 22, 9, 10]

for i in range(len(ROWS)):
    GPIO.setup(COLS[i], GPIO.OUT)
    GPIO.output(COLS[i], GPIO.HIGH)

for i in range(len(ROWS)):
    GPIO.setup(ROWS[i], GPIO.IN, pull_up_down=GPIO.PUD_UP)

try:
    while True:
        for i in range(len(COLS)):
            GPIO.output(COLS[i], 0)

            for j in range(len(ROWS)):
                if GPIO.input(ROWS[j]) == GPIO.LOW:
                    print(MATRIX[j][i])

                    while GPIO.input(ROWS[j]) == GPIO.LOW:
                        sleep(0.1)

            GPIO.output(COLS[i], GPIO.HIGH)
except KeyboardInterrupt:
    pass
except Exception as ex:
    print("Error: {}".format(ex))

GPIO.cleanup()
