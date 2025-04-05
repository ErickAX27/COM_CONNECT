import os
import sys
from datetime import timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import serial
import time
import requests
from CLASS.PIR import MovimientoPIR
from CLASS.PESO import Peso
from CLASS.LUZ import Luz
from CLASS.DHT import DHT
from CLASS.CERRADURA import Cerradura
from MongoSync import MongoSync
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()


class Main:
    def __init__(self):
            # Create base directory path that's absolute
            self.base_dir = os.path.dirname(os.path.abspath(__file__))

            # Debug: Print base directory and .env path
            print(f"Directorio base: {self.base_dir}")
            print(f"Ruta del .env: {os.path.join(self.base_dir, '.env')}")

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
            self.device_id = os.getenv("DEVICE_ID", "0")  # Default to "0" if not found
            print(f"Valor inicial de DEVICE_ID: {self.device_id}")

            self.device_name = os.getenv("DEVICE_NAME", "NEW_DEVICE")
            self.api_endpoint = os.getenv("API_ENDPOINT")
            self.area_id = os.getenv("AREA_ID", "1")  # Default to "1" if not found
            self.reading_time = int(os.getenv("READING_TIME", "60000"))  # milliseconds
            self.response_time = int(os.getenv("RESPONSE_TIME", "300000"))  # milliseconds
            self.password = os.getenv("DEVICE_PASSWORD", "12345678")
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

    def cargar_rfids_autorizados(self):
        """Carga los RFIDs autorizados desde la API o MongoDB"""
        self.rfids_autorizados = []

        # Primero intentar obtener de MongoDB
        rfid_documents = self.mongo_rfid.consultar()

        if rfid_documents:
            for doc in rfid_documents:
                if "rfid_code" in doc:
                    self.rfids_autorizados.append(doc["rfid_code"])

            print(f"Cargados {len(self.rfids_autorizados)} RFIDs autorizados de MongoDB")
        else:
            print("No se encontraron RFIDs autorizados en MongoDB")

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

                # Create registration payload using environment variables
                payload = {
                    'name': os.getenv("DEVICE_NAME", "NEW_DEVICE"),
                    'password': os.getenv("DEVICE_PASSWORD", "12345678"),
                    'area_id': '1',
                    'reading_time': os.getenv("READING_TIME", "60000"),
                    'response_time': os.getenv("RESPONSE_TIME", "300000")
                }

                # Register device with API
                register_response = requests.post(self.api_endpoint, json=payload)
                register_response.raise_for_status()

                # Update environment variable and .env file
                os.environ["DEVICE_ID"] = self.device_id
                self.update_env_file("DEVICE_ID", self.device_id)

                # Reload environment variables to ensure they're updated
                load_dotenv(override=True)
                self.device_id = os.getenv("DEVICE_ID")  # Update instance variable

                print(f"Device registered with ID: {self.device_id}")
                return True

            except requests.exceptions.RequestException as e:
                print(f"Error registering device: {e}")
                return False
        return True

    def update_env_file(self, key, value):
        """Update the .env file with the new key-value pair, handling different formats"""
        env_file = os.path.join(self.base_dir, ".env")

        # Print path for debugging
        print(f"Actualizando archivo .env en: {env_file}")

        updated = False
        new_lines = []

        # Read existing content
        try:
            with open(env_file, "r") as file:
                lines = file.readlines()
        except FileNotFoundError:
            lines = []

        # Process each line
        for line in lines:
            line_stripped = line.strip()

            # Skip comments and empty lines
            if line_stripped.startswith("#") or not line_stripped:
                new_lines.append(line)
                continue

            # Split into key and value
            if '=' in line_stripped:
                current_key, _, current_value = line_stripped.partition('=')
                current_key = current_key.strip()

                if current_key == key:
                    # Replace the existing key
                    new_line = f"{key}={value}\n"
                    new_lines.append(new_line)
                    updated = True
                else:
                    # Keep the original line
                    new_lines.append(line)
            else:
                # Keep lines without '=' intact
                new_lines.append(line)

        # Add new key-value pair if not updated
        if not updated:
            new_lines.append(f"{key}={value}\n")

        # Write back to file
        with open(env_file, "w") as file:
            file.writelines(new_lines)

        # Print confirmation
        print(f"Archivo .env actualizado. Nueva entrada: {key}={value}")
        print("Contenido actualizado del .env:")
        with open(env_file, "r") as file:
            print(file.read())

    def actualizar_variables_desde_api(self):
        """Update variables from API using device ID"""
        if not self.api_endpoint:
            print("API_ENDPOINT no configurado")
            return False

        # Ensure there is no double slash in the URL
        url = f"{self.api_endpoint.rstrip('/')}/{self.device_id}"

        try:
            # Make the API request
            response = requests.get(url)
            response.raise_for_status()

            # Parse the JSON response
            data = response.json()

            # Check if data is a list (multiple devices)
            if isinstance(data, list):
                # Find our device in the list
                for device in data:
                    if str(device.get('id', '')) == str(self.device_id):
                        data = device
                        break
                else:
                    print(f"Device ID {self.device_id} not found in API response")
                    return False

            # Now data should be a dictionary
            if data.get('updated_at') != self.ultima_actualizacion:
                # Update variables
                self.device_name = data.get('name', self.device_name)
                self.password = data.get('password', self.password)
                self.area_id = data.get('area_id', self.area_id)
                self.reading_time = self.time_to_seconds(data.get('reading_time', '00:00:00'))
                self.response_time = self.time_to_seconds(data.get('response_time', '00:00:00'))
                self.ultima_actualizacion = data.get('updated_at', self.ultima_actualizacion)

                # Save updated variables to JSON
                self.update_env_file("DEVICE_NAME", self.device_name)
                self.update_env_file("DEVICE_PASSWORD", self.password)
                self.update_env_file("AREA_ID", self.area_id)
                self.update_env_file("READING_TIME", str(self.reading_time))
                self.update_env_file("RESPONSE_TIME", str(self.response_time))

                print(
                    f"Variables actualizadas: nombre={self.device_name}, contraseña={self.password}, area_id={self.area_id}, lectura={self.reading_time}, respuesta={self.response_time}")
                return True
            else:
                print("No hay actualizaciones nuevas")
                return False

        except requests.exceptions.RequestException as e:
            print(f"Error al realizar la solicitud a la API: {e}")
            return False
        except (KeyError, ValueError, TypeError) as e:
            print(f"Error al procesar la respuesta de la API: {e}")
            print(f"Tipo de respuesta: {type(data).__name__}, Contenido: {data}")
            return False

    def time_to_seconds(self, time_str):
        """Convert time string to seconds"""
        h, m, s = map(int, time_str.split(':'))
        return int(timedelta(hours=h, minutes=m, seconds=s).total_seconds())

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

    def crear_y_guardar_sensor(self, tipo_sensor, id_sensor, valores, port):
        try:
            if tipo_sensor == "MOV":
                sensor = MovimientoPIR(int(valores[0]), self.area_id)
                self.mongo_pir.guardar_datos(sensor.guardar())

            elif tipo_sensor == "LUZ":
                try:
                    valor_limpio = valores[0].strip().split('\r')[0]
                    sensor = Luz(int(valor_limpio), self.area_id)
                    self.mongo_light.guardar_datos(sensor.guardar())
                except ValueError:
                    logging.warning(f"Valor no válido para sensor de Luz ignorado: {valores[0]}")
                    return

            elif tipo_sensor == "DHT":
                try:
                    humedad = float(valores[0])
                    temperatura = float(valores[1])
                    sensor = DHT(temperatura, humedad, self.area_id)
                    self.mongo_temp.guardar_datos(sensor.guardar())
                except (ValueError, IndexError):
                    logging.warning(f"Valores no válidos para sensor DHT ignorados: {valores}")
                    return

            elif tipo_sensor == "PPADACC":
                codigo = valores[0]
                if codigo == self.password:
                    if port:
                        port.write("ACCESS_GARANTEED\n".encode())
                    print("ACCESS_GRANTED")
                    cerradura = Cerradura(self.area_id, "ACCESO", "PASSWORD")
                    self.mongo_cerradura.guardar_datos(cerradura.serializar())
                    self.mongo_cerradura.subir_a_mongo()
                else:
                    if port:
                        port.write("ACCESS_DENIED\n".encode())
                    print("ACCESS_DENIED")

            elif tipo_sensor == "PADPSO":
                try:
                    if len(valores) >= 2:
                        codigo = valores[0]
                        peso_str = valores[1].strip().split('\r')[0]
                        peso_valor = float(peso_str)
                        if len(valores) == 3 and valores[2] == "ADD":
                            payload = {
                                'exit_code': codigo,
                                'stock_weight': peso_valor
                            }
                            api_endpoint_stock = os.getenv("API_ENDPOINT_STOCK")
                            try:
                                response = requests.put(api_endpoint_stock, json=payload)
                                response.raise_for_status()
                                print(f"Datos enviados a la API: {payload}")
                            except requests.exceptions.RequestException as e:
                                logging.warning(f"Error al enviar datos a la API: {e}")
                        else:
                            peso = Peso(codigo, peso_valor, self.device_name, self.area_id)
                            self.mongo_peso.guardar_datos(peso.guardar())
                            self.mongo_peso.subir_a_mongo()
                    else:
                        logging.warning(f"Formato inválido para sensor PADPSO: {valores}")
                except (ValueError, IndexError):
                    logging.warning(f"Valores no válidos para sensor PADPSO ignorados: {valores}")
                    return

            elif tipo_sensor == "IDCRD":
                rfid_code = valores[0].strip()
                if rfid_code in self.rfids_autorizados:
                    if port:
                        port.write("ACCESS_GARANTEED\n".encode())
                    print(f"ACCESS_GRANTED - RFID: {rfid_code}")
                    cerradura = Cerradura(id_sensor, "ACCESO", "RFID")
                    self.mongo_cerradura.guardar_datos(cerradura.serializar())
                    self.mongo_cerradura.subir_a_mongo()
                else:
                    if port:
                        port.write("ACCESS_DENIED\n".encode())
                    print(f"ACCESS_DENIED - RFID no autorizado: {rfid_code}")
            else:
                logging.info(f"Tipo de sensor no reconocido, ignorando: {tipo_sensor}")

        except Exception as e:
            logging.warning(f"Error al procesar mensaje: {e}")
            return

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
        if not self.register_device():
            print("No se pudo registrar el dispositivo. Usando configuración predeterminada.")

        self.actualizar_variables_desde_api()
        self.cargar_rfids_autorizados()

        try:
            available_ports = []
            for i in range(10):
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
                ser = available_ports[0]

            time.sleep(2)

            while True:
                current_time_ms = time.time() * 1000

                if time.time() - self.last_api_check >= self.check_interval:
                    self.actualizar_variables_desde_api()
                    self.cargar_rfids_autorizados()
                    self.last_api_check = time.time()

                if current_time_ms - self.last_reading_time >= self.reading_time:
                    self.mongo_temp.subir_a_mongo()
                    self.mongo_light.subir_a_mongo()
                    self.mongo_pir.subir_a_mongo()
                    self.mongo_peso.subir_a_mongo()
                    self.mongo_cerradura.subir_a_mongo()
                    self.last_reading_time = current_time_ms

                if current_time_ms - self.last_response_time >= self.response_time:
                    self.intentar_subir_pendientes()
                    self.last_response_time = current_time_ms

                for port in available_ports:
                    if port.in_waiting > 0:
                        linea = port.readline().decode('latin-1').strip()
                        if linea:
                            print(f"Datos recibidos: {linea}")
                            tipo_sensor, id_sensor, valores = self.procesar_dato(linea)
                            if tipo_sensor:
                                self.crear_y_guardar_sensor(tipo_sensor, id_sensor, valores, port)

                time.sleep(0.1)

        except serial.SerialException as e:
            print(f"Error con el puerto serial: {e}")
        except KeyboardInterrupt:
            print("Terminando el programa...")
        finally:
            for port in available_ports if 'available_ports' in locals() else []:
                if port.is_open:
                    port.close()

if __name__ == "__main__":
    app = Main()
    app.run()
