import time
import board
import adafruit_dht
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initial the dht device, with data pin connected to:
dhtDevice = adafruit_dht.DHT11(board.D4)

while True:
    try:
        # Print the values to the serial port
        temperature = dhtDevice.temperature
        humidity = dhtDevice.humidity
        logging.info(
            f"Temp: {temperature:.1f} C    Humidity: {humidity}% "
        )

    except RuntimeError as error:
        # Errors happen fairly often, DHT's are hard to read, just keep going
        logging.error(error.args[0])
        time.sleep(2.0)
        continue
    except Exception as error:
        dhtDevice.exit()
        logging.exception("An unexpected error occurred:")
        raise error

    time.sleep(2.0)
