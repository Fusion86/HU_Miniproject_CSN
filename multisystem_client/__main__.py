import sys
import config
import asyncio
import websockets
import threading
import RPi.GPIO as GPIO
from time import sleep


IS_ALARMING = False


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
    async with websockets.connect(uri) as ws:
        try:
            while True:
                msg = await ws.recv()

                if msg in message_handler:
                    await message_handler[msg]()
                else:
                    print("Unknown message: {}".format(msg))
        except Exception as ex:
            print("Error: {}".format(ex))


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

    # Connect to server
    print("Connecting to {}:{}".format(config.SERVER, config.SERVER_PORT))

    try:
        asyncio.get_event_loop().run_until_complete(
            socket_handler("ws://{}:{}".format(config.SERVER, config.SERVER_PORT))
        )
    except Exception as ex:
        print("Error: {}".format(ex))
    except KeyboardInterrupt:
        pass

    print("Alarm is shutting down")

    # Disabled all leds
    for led in [config.RED_LED_BCM, config.BLUE_LED_BCM]:
        if led is not None:
            GPIO.output(led, GPIO.LOW)

    # GPIO cleanup
    GPIO.cleanup()

    print("Alarm is offline")
