import sys
import config
import asyncio
import websockets
import threading
import RPi.GPIO as GPIO
from time import sleep


IS_ALARMING = False
KEY_HISTORY = []
SERVER_CONN = None


async def alarm_aan():
    """Start making noise"""
    global IS_ALARMING

    print("Alarm aan")
    IS_ALARMING = True


async def alarm_uit():
    """Stop making noise"""
    global IS_ALARMING

    print("Alarm uit")
    IS_ALARMING = False


async def alarm_handler():
    """Should only be called once"""
    global IS_ALARMING

    while True:
        if IS_ALARMING:
            GPIO.output(config.RED_LED_BCM, GPIO.HIGH)
            GPIO.output(config.BLUE_LED_BCM, GPIO.LOW)
            await asyncio.sleep(0.2)
            GPIO.output(config.RED_LED_BCM, GPIO.LOW)
            GPIO.output(config.BLUE_LED_BCM, GPIO.HIGH)
        else:
            # Turn blue led on if it is off
            if GPIO.input(config.BLUE_LED_BCM) == False:
                GPIO.output(config.BLUE_LED_BCM, GPIO.HIGH)

        await asyncio.sleep(0.2)


message_handler = {"alarm aan": alarm_aan, "alarm uit": alarm_uit}


async def socket_handler(uri):
    global SERVER_CONN

    async with websockets.connect(uri) as ws:
        SERVER_CONN = ws

        try:
            while True:
                msg = await ws.recv()

                if msg in message_handler:
                    await message_handler[msg]()
                else:
                    print("Unknown message: {}".format(msg))
        except Exception as ex:
            print("Error: {}".format(ex))


async def keypad_handler():
    global KEY_HISTORY

    while True:
        # Only remember last x entries, where x is numbers/chars in config.KEYPAD_CODE
        if len(KEY_HISTORY) > len(config.KEYPAD_CODE):
            negative_nr = len(config.KEYPAD_CODE) * -1
            KEY_HISTORY = KEY_HISTORY[negative_nr:]

        for col in range(len(config.KEYPAD_COLS)):
            GPIO.output(config.KEYPAD_COLS[col], 0)

            for row in range(len(config.KEYPAD_ROWS)):
                if GPIO.input(config.KEYPAD_ROWS[row]) == GPIO.LOW:
                    print(config.KEYPAD_MATRIX[row][col])
                    KEY_HISTORY.append(config.KEYPAD_MATRIX[row][col])

                    # Sleep till key gets released
                    while GPIO.input(config.KEYPAD_ROWS[row]) == GPIO.LOW:
                        await asyncio.sleep(0.1)

            GPIO.output(config.KEYPAD_COLS[col], GPIO.HIGH)

        if KEY_HISTORY == config.KEYPAD_CODE:
            await alarm_uit()
            await SERVER_CONN.send("alarm uit")
            KEY_HISTORY.clear()

        await asyncio.sleep(0.05)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "remotedebug":
        import ptvsd

        ptvsd.enable_attach(address=("0.0.0.0", 5678), redirect_output=True)
        print("Waiting for debugger...")
        ptvsd.wait_for_attach()

    # GPIO setup
    GPIO.setmode(GPIO.BCM)

    # Setup leds
    for led in [config.RED_LED_BCM, config.BLUE_LED_BCM]:
        if led is not None:
            GPIO.setup(led, GPIO.OUT)

    # Setup keypad, if enabled
    if config.USE_KEYPAD:
        for i in range(len(config.KEYPAD_ROWS)):
            GPIO.setup(config.KEYPAD_COLS[i], GPIO.OUT)
            GPIO.output(config.KEYPAD_COLS[i], GPIO.HIGH)

        for i in range(len(config.KEYPAD_ROWS)):
            GPIO.setup(config.KEYPAD_ROWS[i], GPIO.IN, pull_up_down=GPIO.PUD_UP)

    # Connect to server
    print("Connecting to {}:{}".format(config.SERVER, config.SERVER_PORT))

    loop = asyncio.get_event_loop()
    asyncio.ensure_future(
        socket_handler("ws://{}:{}".format(config.SERVER, config.SERVER_PORT))
    )
    asyncio.ensure_future(alarm_handler())

    if config.USE_KEYPAD:
        asyncio.ensure_future(keypad_handler())

    try:
        loop.run_forever()
    except Exception as ex:
        print("Error: {}".format(ex))
    except KeyboardInterrupt:
        pass

    print("Stopping event loop")
    loop.stop()

    # Disabled all leds
    for led in [config.RED_LED_BCM, config.BLUE_LED_BCM]:
        if led is not None:
            GPIO.output(led, GPIO.LOW)

    GPIO.cleanup()

    print("Alarm is offline")
