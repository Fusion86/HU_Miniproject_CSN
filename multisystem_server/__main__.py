import sys
import time
import config
import asyncio
import threading
import websockets
from time import sleep
from websockets.server import WebSocketServerProtocol
import RPi.GPIO as GPIO


# Globals are bad mkay, but make the code simpler in this case
PI_COUNTER = 0
CLIENTS = []
CLIENT_LOST_CONNECTION = False


def get_laser_visible():
    """Returns True if laser is visible. Also returns True when the laser is not connected."""
    return not GPIO.input(config.LIGHT_SENSOR_BCM)


def get_button_pressed():
    """Returns True if button is pressed"""
    return GPIO.input(config.BUTTON_BCM) == GPIO.HIGH


async def alarm_handler():
    """Should only be called once"""
    global CLIENT_LOST_CONNECTION

    # Alarm state, no need to make this global
    is_alarming = False
    prev_is_alarming = False

    while True:
        # Enable alarming state when laser is not visible
        if get_laser_visible() == False:
            is_alarming = True

        # Enable alarming state when a client lost connection
        if CLIENT_LOST_CONNECTION:
            is_alarming = True
            CLIENT_LOST_CONNECTION = False

        # Disable alarming state when button is pressed
        if is_alarming and get_button_pressed():
            is_alarming = False

        # If state changed, tell all clients
        if is_alarming != prev_is_alarming:
            msg = "alarm aan"

            if not is_alarming:
                msg = "alarm uit"

            print("Sending '{}' to {} clients".format(msg, len(CLIENTS)))
            for client in CLIENTS:
                await client.send(msg)

        if is_alarming:
            GPIO.output(config.RED_LED_BCM, GPIO.HIGH)
            GPIO.output(config.BLUE_LED_BCM, GPIO.LOW)
            await asyncio.sleep(0.2)
            GPIO.output(config.RED_LED_BCM, GPIO.LOW)
            GPIO.output(config.BLUE_LED_BCM, GPIO.HIGH)
        else:
            # Turn blue led on if it is off
            if GPIO.input(config.BLUE_LED_BCM) == False:
                GPIO.output(config.BLUE_LED_BCM, GPIO.HIGH)

        prev_is_alarming = is_alarming

        # Keep our CPU happy + timer for blue led if it's on
        await asyncio.sleep(0.2)


async def socket_handler(ws: WebSocketServerProtocol, path):
    """This method is called for each client connection"""
    global PI_COUNTER
    global CLIENT_LOST_CONNECTION
    # global CLIENTS is not needed because it is mutable

    # Give ws an identifier
    ws.identifier = "Raspberry {}".format(PI_COUNTER)
    PI_COUNTER = PI_COUNTER + 1

    CLIENTS.append(ws)

    print("Connected to: {}".format(ws.identifier))

    while True:
        try:
            _ = await asyncio.wait_for(ws.recv(), timeout=4)
        except asyncio.TimeoutError:
            # Received no data for 4 seconds, check the connection
            try:
                print(
                    "[{}] Received no data in the last 4 seconds, sending ping...".format(
                        ws.identifier
                    )
                )

                # Wait for pong
                pong_waiter = await ws.ping()
                await asyncio.wait_for(pong_waiter, timeout=4)
                print("[{}] Received pong".format(ws.identifier))
            except asyncio.TimeoutError:
                # Pong timeout, aka connection lost
                print("[{}] Pong not received, connection lost".format(ws.identifier))
                CLIENT_LOST_CONNECTION = True
                CLIENTS.remove(ws)
                break  # Stop
        except Exception as ex:
            # Other exception
            print("[{}] Error: {}".format(ws.identifier, ex))
            CLIENT_LOST_CONNECTION = True
            CLIENTS.remove(ws)
            break  # Stop


if __name__ == "__main__":
    # Check if we want to wait for a debugger to attach
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

    # Setup button
    if config.BUTTON_BCM is not None:
        GPIO.setup(config.BUTTON_BCM, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    # Setup light sensor
    if config.LIGHT_SENSOR_BCM is not None:
        GPIO.setup(config.LIGHT_SENSOR_BCM, GPIO.IN)

    # Setup websocket server
    socket_server = websockets.serve(socket_handler, "0.0.0.0", config.PORT, timeout=4)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(socket_server)

    # Setup alarm handler
    asyncio.ensure_future(alarm_handler())

    # Main loop
    try:
        print("Starting server main loop")
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    # Stop event loop
    print("Stopping event loop")
    loop.stop()  # Throws some errors, but who cares about those

    print("GPIO cleanup")

    # Disabled all leds
    for led in [config.RED_LED_BCM, config.BLUE_LED_BCM]:
        if led is not None:
            GPIO.output(led, GPIO.LOW)

    # GPIO cleanup
    GPIO.cleanup()

    print("Server is offline")
