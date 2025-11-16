import os
import time
import board
import adafruit_dht
import logging
import paho.mqtt.client as mqtt
import json

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

# --- Configuration ---
# Read credentials from environment variables
MQTT_BROKER = os.environ.get('MQTT_BROKER')
MQTT_PORT = int(os.environ.get('MQTT_PORT', 1883))
MQTT_USER = os.environ.get('MQTT_USER')
MQTT_PASS = os.environ.get('MQTT_PASSWORD')
SLEEP_INTERVAL = int(os.environ.get('SLEEP_INTERVAL', 60))
DEVICE_NAME = os.environ.get('DEVICE_NAME', "RaspberryPi DHT11")
DEVICE_ID = DEVICE_NAME.replace(" ", "_").lower()  # Create a unique device ID
SENSOR_TOPIC = os.environ.get('MQTT_TOPIC', f"homeassistant/sensor/{DEVICE_ID}")

# Check that all required variables are set
if not all([MQTT_BROKER, MQTT_USER, MQTT_PASS]):
    raise EnvironmentError("Error: MQTT_BROKER, MQTT_USER, and MQTT_PASSWORD environment variables must be set.")

# --- Sensor Setup ---
# Initialize your DHT11 sensor (adjust for your library)
# Example for adafruit_dht:
dhtDevice = adafruit_dht.DHT11(board.D4)  # Assumes connected to GPIO 4


def get_average_reading(num_readings=30):
    """
    Gets an average temperature and humidity reading from the DHT sensor.

    Args:
        num_readings (int): The number of readings to take for averaging.  Defaults to 30.

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
            time.sleep(1.0)  # Short delay between readings
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
        # round to half degree for temps
        avg_temperature = round(round(sum(temperatures) / len(temperatures) * 2) / 2, 1)
        avg_humidity = round(sum(humidities) / len(humidities))
        return avg_temperature, avg_humidity
    else:
        return None, None


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, reason_code, properties):
    logging.info(f"Connected with result code {reason_code}")
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("$SYS/#")


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    logging.info(msg.topic + " " + str(msg.payload))


def config_home_assistant(client):
    """Publishes MQTT discovery messages for Home Assistant."""

    device_config = {
        "identifiers": [DEVICE_ID],
        "name": DEVICE_NAME,
        "manufacturer": "Generic",
        "model": "DHT11 Sensor",
    }

    # Temperature sensor configuration
    temp_config = {
        "device": device_config,
        "name": f"{DEVICE_NAME} Temperature",
        "unique_id": f"{DEVICE_ID}_001_temperature",
        "state_topic": f"{SENSOR_TOPIC}/state",
        "value_template": "{{ value_json.temperature }}",
        "unit_of_measurement": "°C",
        "device_class": "temperature",
        "availability_topic": "telemetry/sensor/availability",
        "payload_available": "online",
        "payload_not_available": "offline",
    }
    temp_config_topic = f"{SENSOR_TOPIC}_t/config"

    # Humidity sensor configuration
    humidity_config = {
        "device": device_config,
        "name": f"{DEVICE_NAME} Humidity",
        "unique_id": f"{DEVICE_ID}_001_humidity",
        "state_topic": f"{SENSOR_TOPIC}/state",
        "value_template": "{{ value_json.humidity }}",
        "unit_of_measurement": "%",
        "device_class": "humidity",
        "availability_topic": "telemetry/sensor/availability",
        "payload_available": "online",
        "payload_not_available": "offline",
    }
    humidity_config_topic = f"{SENSOR_TOPIC}_h/config"

    client.publish(temp_config_topic, json.dumps(temp_config), retain=True)
    client.publish(humidity_config_topic, json.dumps(humidity_config), retain=True)
    logging.info("Published Home Assistant MQTT discovery messages.")


if __name__ == "__main__":

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)

    # Configure Home Assistant
    config_home_assistant(client)

    logging.info("Starting sensor loop...")
    client.loop_start()
    while True:
        temperature, humidity = get_average_reading()

        if temperature is not None and humidity is not None:
            logging.info(
                f"Avg Temp: {temperature} C    Avg Humidity: {humidity}% "
            )

            payload = json.dumps({"temperature": temperature, "humidity": humidity})
            client.publish(f"{SENSOR_TOPIC}/state", payload)
        else:
            logging.warning("Failed to get average readings.")

        time.sleep(SLEEP_INTERVAL)

    # Stop the MQTT loop
    client.loop_stop()
    print("Exiting.")
