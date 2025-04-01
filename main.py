import os
import serial
import time
import json
import requests
from datetime import datetime
from CLASS.PIR import MovimientoPIR
from CLASS.PESO import Peso
from CLASS.LUZ import Luz
from CLASS.DHT import DHT
from CLASS.CERRADURA import Cerradura
from CLASS.RFID import Rfid
from MongoSync import MongoSync
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Main:
    def __init__(self):
        # Create base directory path that's absolute
        self.base_dir = os.path.dirname(os.path.abspath(__file__))

        # Create directories if they don't exist
        self.jsons_dir = os.path.join(self.base_dir, "JSONs")
        self.local_dir = os.path.join(self.jsons_dir, "Local")

        # Create directories if they don't exist
        if not os.path.exists(self.jsons_dir):
            os.makedirs(self.jsons_dir)
            print(f"Created directory: {self.jsons_dir}")

        if not os.path.exists(self.local_dir):
            os.makedirs(self.local_dir)
            print(f"Created directory: {self.local_dir}")

        # Initialize device attributes
        self.device_id = os.getenv("DEVICE_ID", "0")
        self.device_name = "NEW_DEVICE"
        self.api_endpoint = os.getenv("API_ENDPOINT")
        self.reading_time = 6000  # milliseconds
        self.response_time = 40000  # milliseconds
        self.password = 123
        self.ultima_actualizacion = time.strftime("%Y-%m-%d %H:%M:%S")

        # Initialize MongoDB connectors with absolute paths
        self.mongo_temp = MongoSync(
            "TemperatureHumiditySensor",
            os.path.join(self.jsons_dir, "DHT.json"),
            os.path.join(self.local_dir, "local_DHT.json")
        )
        self.mongo_light = MongoSync(
            "LightSensor",
            os.path.join(self.jsons_dir, "luz.json"),
            os.path.join(self.local_dir, "local_luz.json")
        )
        self.mongo_pir = MongoSync(
            "PirSensor",
            os.path.join(self.jsons_dir, "pir.json"),
            os.path.join(self.local_dir, "local_pir.json")
        )
        self.mongo_peso = MongoSync(
            "WeightSensor",
            os.path.join(self.jsons_dir, "peso.json"),
            os.path.join(self.local_dir, "local_peso.json")
        )
        self.mongo_cerradura = MongoSync(
            "LockSensor",
            os.path.join(self.jsons_dir, "cerradura.json"),
            os.path.join(self.local_dir, "local_cerradura.json")
        )
        self.mongo_rfid = MongoSync(
            "RfidSensor",
            os.path.join(self.jsons_dir, "rfid.json"),
            os.path.join(self.local_dir, "local_rfid.json")
        )

        # Initialize timers
        self.last_reading_time = time.time() * 1000  # Convert to milliseconds
        self.last_response_time = time.time() * 1000  # Convert to milliseconds
        self.last_api_check = 0
        self.check_interval = 300  # Check API every 300 seconds

    def register_device(self):
        """Register new device with the API if device_id is 0"""
        if self.device_id == "0":
            try:
                # Get all devices to find highest ID
                response = requests.get(self.api_endpoint)
                response.raise_for_status()
                devices = response.json()

                # Find the highest device ID
                highest_id = 0
                for device in devices:
                    try:
                        device_id = int(device.get('id', 0))
                        highest_id = max(highest_id, device_id)
                    except (ValueError, TypeError):
                        pass

                # Set new device ID
                new_id = highest_id + 1
                self.device_id = str(new_id)

                # Create registration payload
                payload = {
                    'name': 'NEW_DEVICE',
                    'password': '12345678',
                    'reading_time': '3600000',
                    'response_time': '18000000'
                }

                # Register device with API
                register_response = requests.post(self.api_endpoint, json=payload)
                register_response.raise_for_status()

                # Update environment variable
                os.environ["DEVICE_ID"] = self.device_id
                print(f"Device registered with ID: {self.device_id}")
                return True

            except requests.exceptions.RequestException as e:
                print(f"Error registering device: {e}")
                return False
        return True

    def actualizar_variables_desde_api(self):
        """Update variables from API using device ID"""
        if not self.api_endpoint:
            print("API_ENDPOINT no configurado")
            return False

        url = f"{self.api_endpoint}/{self.device_id}"

        try:
            # Make the API request
            response = requests.get(url)
            response.raise_for_status()

            # Parse the JSON response
            data = response.json()

            # Check if updated_at is different from ultima_actualizacion
            if data.get('updated_at') != self.ultima_actualizacion:
                # Update variables
                self.reading_time = int(data.get('reading_time', self.reading_time))
                self.response_time = int(data.get('response_time', self.response_time))
                self.password = data.get('password', self.password)
                self.ultima_actualizacion = data.get('updated_at', self.ultima_actualizacion)
                print(f"Variables actualizadas: lectura={self.reading_time}, respuesta={self.response_time}")
                return True
            else:
                print("No hay actualizaciones nuevas")
                return False

        except requests.exceptions.RequestException as e:
            print(f"Error al realizar la solicitud a la API: {e}")
            return False
        except (KeyError, ValueError) as e:
            print(f"Error al procesar la respuesta de la API: {e}")
            return False

    def procesar_dato(self, dato):
        """Parse incoming sensor data string"""
        if dato.startswith("DHT"):
            tipo_sensor = "DHT"
            id_sensor = "00"
            partes = dato.split(":")
            if len(partes) >= 3:
                valores = [partes[1], partes[2]]  # Temperature, Humidity
            else:
                valores = ["0", "0"]  # Default values if parsing fails
            return tipo_sensor, id_sensor, valores
        elif dato.startswith("LUZ"):
            tipo_sensor = "LUZ"
            id_sensor = "00"
            valores = [dato[4:]]
            return tipo_sensor, id_sensor, valores
        elif dato.startswith("MOV"):
            tipo_sensor = "MOV"
            id_sensor = "00"
            valores = [dato[4:]]
            return tipo_sensor, id_sensor, valores
        elif dato.startswith("PPADACC"):
            tipo_sensor = "PPADACC"
            id_sensor = "00"
            valores = [dato[8:]]
            return tipo_sensor, id_sensor, valores
        elif dato.startswith("PADPSO"):
            tipo_sensor = "PADPSO"
            partes = dato.split(":")
            id_sensor = "00"
            if len(partes) >= 3:
                valores = [partes[1], partes[2]]
            else:
                valores = ["0", "0"]
            return tipo_sensor, id_sensor, valores
        elif dato.startswith("IDCRD"):
            tipo_sensor = "IDCRD"
            id_sensor = "00"
            valores = [dato[6:]]
            return tipo_sensor, id_sensor, valores
        return None, None, None

    def crear_y_guardar_sensor(self, tipo_sensor, id_sensor, valores, ser=None):
        """Create sensor object and save data based on sensor type"""
        if tipo_sensor == "MOV":
            sensor = MovimientoPIR(int(valores[0]))
            self.mongo_pir.guardar_datos(sensor.guardar())

        elif tipo_sensor == "LUZ":
            sensor = Luz(int(valores[0]))
            self.mongo_light.guardar_datos(sensor.guardar())

        elif tipo_sensor == "DHT":
            humedad = float(valores[0])
            temperatura = float(valores[1])
            sensor = DHT(temperatura, humedad)
            self.mongo_temp.guardar_datos(sensor.guardar())



        elif tipo_sensor == "PPADACC":

            codigo = valores[0]

            try:

                # Convert the received code to integer for comparison

                if int(codigo) == self.password:

                    if ser:
                        ser.write("ACCESS_GRANTED\n".encode())

                    print("ACCESS_GRANTED")

                    # Create lock event

                    cerradura = Cerradura(id_sensor, "ACCESO", "PASSWORD")
                    self.mongo_cerradura.guardar_datos(Cerradura.serializar())

                    self.mongo_cerradura.guardar_datos(cerradura.serializar())

                    # Try to send immediately

                    self.mongo_cerradura.subir_a_mongo()

                else:

                    if ser:
                        ser.write("ACCESS_DENIED\n".encode())

                    print("ACCESS_DENIED")

            except ValueError:

                if ser:
                    ser.write("ACCESS_DENIED\n".encode())

                print("ACCESS_DENIED - Invalid code format")

        elif tipo_sensor == "PADPSO":
            if len(valores) >= 2:
                codigo = valores[0]
                peso_valor = float(valores[1])
                peso = Peso(codigo, peso_valor, self.device_name)
                self.mongo_peso.guardar_datos(peso.serializar())
                # Try to send immediately
                self.mongo_peso.subir_a_mongo()

        elif tipo_sensor == "IDCRD":
            rfid_code = valores[0].strip()
            rfid = Rfid(rfid_code, "Unknown", "Entry", self.device_name)
            self.mongo_rfid.guardar_datos(rfid.guardar())
            # Try to send immediately
            self.mongo_rfid.subir_a_mongo()

    def intentar_subir_pendientes(self):
        """Try to upload pending data to MongoDB"""
        print("Intentando subir datos pendientes a MongoDB...")
        self.mongo_temp.subir_a_mongo()
        self.mongo_light.subir_a_mongo()
        self.mongo_pir.subir_a_mongo()
        self.mongo_peso.subir_a_mongo()
        self.mongo_cerradura.subir_a_mongo()
        self.mongo_rfid.subir_a_mongo()

    def run(self):
        """Main execution loop"""
        # Register device if needed
        if not self.register_device():
            print("No se pudo registrar el dispositivo. Usando configuración predeterminada.")

        # Update variables from API
        self.actualizar_variables_desde_api()

        try:
            # Try to open all available COM ports
            available_ports = []
            for i in range(10):  # Check COM1 to COM10
                port = f'COM{i + 1}'
                try:
                    ser = serial.Serial(port, 9600, timeout=1)
                    available_ports.append(ser)
                    print(f"Puerto {port} abierto correctamente")
                except serial.SerialException:
                    pass

            if not available_ports:
                print("No se pudo abrir ningún puerto COM.")
                ser = None
            else:
                ser = available_ports[0]  # Use the first available port as default

            time.sleep(2)  # Allow serial connections to stabilize

            while True:
                current_time_ms = time.time() * 1000  # Current time in milliseconds

                # Check API for updates
                if time.time() - self.last_api_check >= self.check_interval:
                    self.actualizar_variables_desde_api()
                    self.last_api_check = time.time()

                # Check if it's time to upload data
                if current_time_ms - self.last_response_time >= self.response_time:
                    self.intentar_subir_pendientes()
                    self.last_response_time = current_time_ms

                # Process serial data from all ports
                for port in available_ports:
                    if port.in_waiting > 0:
                        linea = port.readline().decode('latin-1').strip()
                        if linea:
                            print(f"Datos recibidos: {linea}")
                            tipo_sensor, id_sensor, valores = self.procesar_dato(linea)
                            if tipo_sensor:
                                self.crear_y_guardar_sensor(tipo_sensor, id_sensor, valores, port)

                # Small delay to prevent CPU overuse
                time.sleep(0.1)

        except serial.SerialException as e:
            print(f"Error con el puerto serial: {e}")
        except KeyboardInterrupt:
            print("Terminando el programa...")
        finally:
            # Close all open ports
            for port in available_ports if 'available_ports' in locals() else []:
                if port.is_open:
                    port.close()


if __name__ == "__main__":
    app = Main()
    app.run()