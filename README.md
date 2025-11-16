# DHT11 to MQTT with Home Assistant Discovery

This project publishes temperature and humidity readings from a DHT11 sensor to an MQTT broker, with automatic discovery in Home Assistant.

## Prerequisites

*   Raspberry Pi (or similar)
*   DHT11 sensor
*   Home Assistant
*   uv

## Installation

1.  **Install MQTT integration in Home Assistant**
    
    Create new user for the integration, don't use the root. Automatic discovery should be enabled by default.

2.  **Configure Environment Variables:**

    Set the following environment variables:

    *   `MQTT_BROKER`:  IP address or hostname of your MQTT broker (Home Assistant).
    *   `MQTT_PORT`: Port number of your MQTT broker (default: 1883).
    *   `MQTT_USER`: MQTT username.
    *   `MQTT_PASSWORD`: MQTT password.
    *   `DEVICE_NAME`: A friendly name for your device (e.g., "Living Room Sensor").
    *   `DEVICE_ID`: This needs to be unique a preferably short (e.g, "01rp")
    *   `SLEEP_INTERVAL`:  Time in seconds between sensor readings (default: 60).

    You can set these in the `dht11-mqtt.service` file or directly in your shell and run with `uv run main.py`

3.  **Create the Service File:**

    Copy the provided `dht11-mqtt.service` file to `/etc/systemd/system/`.  Modify the `User`, `WorkingDirectory`, `ExecStart`, and `Environment` variables to match your setup.  **Important:**  Ensure the paths in `WorkingDirectory` and `ExecStart` are correct.  Also, fill in the `MQTT_USER` and `MQTT_PASSWORD` in the `Environment` section.

4.  **Enable and Start the Service:**

    ```bash
    sudo systemctl daemon-reload
    sudo systemctl enable dht11-mqtt.service
    sudo systemctl start dht11-mqtt.service
    ```

## Home Assistant

No other configuration should be necessary. Entity should appear immediately after starting the service. 

## Troubleshooting

*   **Check Logs:**  Use `journalctl -f -u dht11-mqtt.service` to view the service logs for errors.
