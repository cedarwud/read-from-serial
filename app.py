import serial
import requests
import time
import json  # Import the json module to handle JSON data

# Constants for API URLs and credentials
# LOGIN_URL = "https://edu.nthu-smart-farming.kits.tw/api/api/account/login"
# DATA_POST_URL = "https://edu.nthu-smart-farming.kits.tw/api/api/iot_data/lab501"
# DATA_POST_CUSTOM = "https://gauge-charts.onrender.com/api/data"
# EMAIL = "2024-competition-team9"
# PASSWORD = "38885800"
DATA_POST_CUSTOM = "http://localhost:3000/api/data"

# Arduino Serial Port Configuration (change according to your port)
SERIAL_PORT = "COM6"  # Adjust for your system, on Linux it might be '/dev/ttyUSB0'
BAUD_RATE = 9600

# Initialize accumulated power for both sensors
accumulated_power_1 = 0.0
accumulated_power_2 = 0.0


# Login and get token
# def get_token():
#     credentials = {"email": EMAIL, "password": PASSWORD}
#     response = requests.post(LOGIN_URL, json=credentials)
#     if response.status_code == 200:
#         return response.json()["token"]
#     else:
#         print("Failed to log in.")
#         return None


# Function to send the data to API
def send_data(token, sensor_data_1, sensor_data_2, acc_power_1, acc_power_2):
    # headers = {"Authorization": f"Bearer {token}"}
    data = {
        "data": [
            {
                "type": "BATTERY_VOLTAGE",
                "value": sensor_data_1["voltage"],
                "channel": 0,
            },
            {
                "type": "ELECTRIC_CURRENT",
                "value": sensor_data_1["current"],
                "channel": 0,
            },
            {
                "type": "ELECTRICAL_CONSUMPTION",
                "value": sensor_data_1["power"],
                "channel": 0,
            },
            {"type": "ELECTRICAL_CONSUMPTION", "value": acc_power_1, "channel": 2},
            {
                "type": "BATTERY_VOLTAGE",
                "value": sensor_data_2["voltage"],
                "channel": 1,
            },
            {
                "type": "ELECTRIC_CURRENT",
                "value": sensor_data_2["current"],
                "channel": 1,
            },
            {
                "type": "ELECTRICAL_CONSUMPTION",
                "value": sensor_data_2["power"],
                "channel": 1,
            },
            {"type": "ELECTRICAL_CONSUMPTION", "value": acc_power_2, "channel": 3},
            {
                "type": "ELECTRICAL_CONSUMPTION",
                "value": acc_power_1 + acc_power_2,
                "channel": 4,
            },
            {
                "type": "ELECTRICAL_CONSUMPTION",
                "value": sensor_data_1["power"] + sensor_data_2["power"],
                "channel": 5,
            },
        ]
    }
    try:
        # requests.post(DATA_POST_URL, headers=headers, json=data)
        requests.post(DATA_POST_CUSTOM, json=data)
    except requests.RequestException as e:
        print(f"Failed to send data: {e}")


# Open serial port to communicate with Arduino
def read_from_serial(ser):
    try:
        if ser.in_waiting > 0:  # Only read if there is data in the buffer
            line = ser.readline().decode("utf-8").strip()  # Read and decode serial data
            return json.loads(line)  # Convert JSON string to dictionary
    except json.JSONDecodeError:
        print(f"Received malformed JSON.")
        return None
    except Exception as e:
        print(f"Error reading from serial: {e}")
        return None
    return None  # Return None if no data is available


def main():
    global accumulated_power_1, accumulated_power_2  # Access global variables
    # token = get_token()
    # if not token:
    #     return

    # Open serial port to Arduino
    with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1) as ser:
        start_time = time.time()
        while True:
            # Read data from serial (JSON format)
            sensor_data = read_from_serial(ser)
            if sensor_data:
                try:
                    # Extract values from the JSON dictionary
                    sensor_data_1 = sensor_data.get("sensor_1")
                    voltage_1 = float(sensor_data_1.get("voltage", 0))
                    current_1 = float(sensor_data_1.get("current", 0))
                    power_1 = float(sensor_data_1.get("power", 0))
                    sensor_data_2 = sensor_data.get("sensor_2")
                    voltage_2 = float(sensor_data_2.get("voltage", 0))
                    current_2 = float(sensor_data_2.get("current", 0))
                    power_2 = float(sensor_data_2.get("power", 0))

                    print(
                        f"Voltage_1: {voltage_1}V, Current_1: {current_1}mA, Power_1: {power_1}mW, Voltage_2: {voltage_2}V, Current_2: {current_2}mA, Power_2: {power_2}mW"
                    )

                    # Update accumulated power (assuming power is in mW and time interval is 1 second)
                    current_time = time.time()
                    time_interval = current_time - start_time
                    accumulated_power_1 += (
                        power_1 / 1000
                    ) * time_interval  # Convert to Watt-seconds (Joules)
                    accumulated_power_2 += (
                        power_2 / 1000
                    ) * time_interval  # Convert to Watt-seconds (Joules)
                    start_time = current_time

                    # Send the sensor data to the API, including accumulated power
                    send_data(
                        # token,
                        sensor_data_1,
                        sensor_data_2,
                        accumulated_power_1,
                        accumulated_power_2,
                    )
                except (ValueError, TypeError) as e:
                    print(f"Error parsing sensor data: {e}")

            # Adjust sleep time if needed for real-time performance
            time.sleep(0.1)


if __name__ == "__main__":
    main()
