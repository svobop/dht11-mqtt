import time
import board
import adafruit_dht
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initial the dht device, with data pin connected to:
dhtDevice = adafruit_dht.DHT11(board.D4)


def get_average_reading(num_readings=5):
    """
    Gets an average temperature and humidity reading from the DHT sensor.

    Args:
        num_readings (int): The number of readings to take for averaging.  Defaults to 5.

    Returns:
        tuple: A tuple containing the average temperature and humidity.  Returns (None, None) on error.
    """
    temperatures = []
    humidities = []

    for _ in range(num_readings):
        try:
            temperature = dhtDevice.temperature
            humidity = dhtDevice.humidity
            if temperature is not None and humidity is not None:
                temperatures.append(temperature)
                humidities.append(humidity)
            time.sleep(0.5)  # Short delay between readings
        except RuntimeError as error:
            # Errors happen fairly often, DHT's are hard to read, just keep going
            logging.error(error.args[0])
            time.sleep(2.0)
            continue
        except Exception as error:
            dhtDevice.exit()
            logging.exception("An unexpected error occurred:")
            raise error

    if temperatures and humidities:
        avg_temperature = sum(temperatures) / len(temperatures)
        avg_humidity = sum(humidities) / len(humidities)
        return avg_temperature, avg_humidity
    else:
        return None, None


while True:
    avg_temperature, avg_humidity = get_average_reading()

    if avg_temperature is not None and avg_humidity is not None:
        logging.info(
            f"Avg Temp: {avg_temperature:.1f} C    Avg Humidity: {avg_humidity:.1f}% "
        )
    else:
        logging.warning("Failed to get average readings.")

    time.sleep(2.0)
