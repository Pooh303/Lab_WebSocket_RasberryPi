import asyncio
import websockets
import spidev
import RPi.GPIO as GPIO

# WebSocket handling
connected_clients = set()
last_message = None

async def handle_client(websocket, path):
    global last_message
    connected_clients.add(websocket)
    try:
        async for message in websocket:
            last_message = float(message)  # Convert message to float
            print(f"Received message: {last_message}")
            await asyncio.gather(*[client.send(message) for client in connected_clients])
    finally:
        connected_clients.remove(websocket)

async def main():
    server = await websockets.serve(handle_client, "0.0.0.0", 8765)
    print("WebSocket server started, waiting for communication...")

    # Set up SPI
    spi = spidev.SpiDev()
    spi.open(0, 0)
    spi.max_speed_hz = 1350000

    # GPIO setup
    LED_PIN = 18
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(LED_PIN, GPIO.OUT)
    pwm = GPIO.PWM(LED_PIN, 1000)  # Set frequency to 1kHz
    pwm.start(0)

    try:
        while True:
            if last_message is not None:
                duty_cycle = max(0, min(100, last_message))  # Ensure duty cycle is within the valid range (0-100%)
                pwm.ChangeDutyCycle(duty_cycle)
                print(f"Set PWM Duty Cycle to: {duty_cycle}%")
            
            await asyncio.sleep(0.5)  # Use asyncio.sleep to yield control
    except KeyboardInterrupt:
        pass
    finally:
        pwm.stop()
        GPIO.cleanup()
        spi.close()

    # Wait for WebSocket server to close
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
