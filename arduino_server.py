import serial
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import time

# Initialize the serial port to which Arduino is connected
ser = serial.Serial("COM1", 9600, timeout=1)

# Global variables to store the latest data from both sensors and their accumulated power
latest_data = {
    "sensor_1": {
        "voltage": "N/A",
        "current": "N/A",
        "power": 0.0,
        "accumulated_power": 0.0,
    },
    "sensor_2": {
        "voltage": "N/A",
        "current": "N/A",
        "power": 0.0,
        "accumulated_power": 0.0,
    },
}


# Function to accumulate power for both sensors
def accumulate_power():
    global latest_data
    try:
        power_1 = float(latest_data["sensor_1"]["power"])
        power_2 = float(latest_data["sensor_2"]["power"])

        latest_data["sensor_1"]["accumulated_power"] += (
            power_1 / 1000
        )  # Convert mW to Joules
        latest_data["sensor_2"]["accumulated_power"] += (
            power_2 / 1000
        )  # Convert mW to Joules
    except (ValueError, TypeError):
        pass


# Define a class to handle HTTP requests
class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()

            # Serve the HTML file from the file system
            with open("index.html", "r") as file:
                self.wfile.write(file.read().encode())

        elif self.path == "/data":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(latest_data).encode())


# Function to read from the serial port and update the latest data for both sensors
def read_serial_data():
    global latest_data
    while True:
        try:
            if ser.in_waiting > 0:
                line = ser.readline().decode("utf-8").strip()
                try:
                    new_data = json.loads(line)  # Load incoming JSON data

                    # Update sensor 1 data, preserving accumulated power
                    if "sensor_1" in new_data:
                        latest_data["sensor_1"]["voltage"] = new_data["sensor_1"].get(
                            "voltage", latest_data["sensor_1"]["voltage"]
                        )
                        latest_data["sensor_1"]["current"] = new_data["sensor_1"].get(
                            "current", latest_data["sensor_1"]["current"]
                        )
                        latest_data["sensor_1"]["power"] = new_data["sensor_1"].get(
                            "power", latest_data["sensor_1"]["power"]
                        )

                    # Update sensor 2 data, preserving accumulated power
                    if "sensor_2" in new_data:
                        latest_data["sensor_2"]["voltage"] = new_data["sensor_2"].get(
                            "voltage", latest_data["sensor_2"]["voltage"]
                        )
                        latest_data["sensor_2"]["current"] = new_data["sensor_2"].get(
                            "current", latest_data["sensor_2"]["current"]
                        )
                        latest_data["sensor_2"]["power"] = new_data["sensor_2"].get(
                            "power", latest_data["sensor_2"]["power"]
                        )

                    print(f"Received data: {latest_data}")
                    accumulate_power()

                except json.JSONDecodeError:
                    print(f"Received non-JSON data: {line}")
            time.sleep(0.1)
        except Exception as e:
            print(f"Error reading serial data: {e}")
            time.sleep(1)


# Set up the server
def run_server(server_class=HTTPServer, handler_class=RequestHandler, port=8000):
    server_address = ("", port)
    httpd = server_class(server_address, handler_class)
    print(f"Starting server on port {port}")
    httpd.serve_forever()


# Main function remains the same as before
if __name__ == "__main__":
    # Start a background thread to read serial data from Arduino
    serial_thread = threading.Thread(target=read_serial_data, daemon=True)
    serial_thread.start()

    # Run the HTTP server on the main thread
    run_server()
