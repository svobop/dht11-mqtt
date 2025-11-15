import os
import time
import board
import adafruit_dht
import logging
import paho.mqtt.client as mqtt
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration ---
# Read credentials from environment variables
MQTT_BROKER = os.environ.get('MQTT_BROKER')
MQTT_PORT = int(os.environ.get('MQTT_PORT', 1883))
MQTT_USER = os.environ.get('MQTT_USER')
MQTT_PASS = os.environ.get('MQTT_PASSWORD')
SENSOR_TOPIC = os.environ.get('MQTT_TOPIC', "raspberrypi/dht11")
SLEEP_INTERVAL = int(os.environ.get('SLEEP_INTERVAL', 60))

# Check that all required variables are set
if not all([MQTT_BROKER, MQTT_USER, MQTT_PASS]):
    raise EnvironmentError("Error: MQTT_BROKER, MQTT_USER, and MQTT_PASSWORD environment variables must be set.")

# --- Sensor Setup ---
# Initialize your DHT11 sensor (adjust for your library)
# Example for adafruit_dht:
dhtDevice = adafruit_dht.DHT11(board.D4) # Assumes connected to GPIO 4


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

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected with result code {reason_code}")
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("$SYS/#")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))


if __name__ == "__main__":

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, 1883, 60)
    client.loop_start()

    logging.info("Starting sensor loop...")
    while True:
        temperature, humidity = get_average_reading()

        if temperature is not None and humidity is not None:
            logging.info(
                f"Avg Temp: {temperature:.1f} C    Avg Humidity: {humidity:.1f}% "
            )

            payload = json.dumps({"temperature": temperature, "humidity": humidity})
            client.publish("raspberrypi/dht11", payload)
        else:
            logging.warning("Failed to get average readings.")

        time.sleep(SLEEP_INTERVAL)

    # Stop the MQTT loop
    client.loop_stop()
    print("Exiting.")
