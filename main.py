import os

import serial
import time
import requests
from CLASS.PIR import MovimientoPIR
# from CLASS.PESO import Peso
from CLASS.LUZ import Luz
from CLASS.DHT import DHT
from MongoSync import MongoSync

device_id = 1
lectura = 0
respuesta = 0
ultima_actualizacion = time.strftime("%Y-%m-%d %H:%M:%S")
pin_pad = "12345678"


def actualizar_variables_desde_api(url):
    global lectura, respuesta, pin_pad, ultima_actualizacion

    try:
        # Make the API request
        response = requests.get(url)
        response.raise_for_status()  # Raise exception for HTTP errors

        # Parse the JSON response
        data = response.json()

        # Check if updated_at is different from ultima_actualizacion
        if data['updated_at'] != ultima_actualizacion:
            # Update variables only if the timestamp is different
            lectura = data['read']
            respuesta = data['response']
            pin_pad = data['password']
            ultima_actualizacion = data['updated_at']
            print(f"Variables actualizadas: lectura={lectura}, respuesta={respuesta}, pin_pad={pin_pad}")
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


def procesar_dato(dato):
    tipo_sensor = dato[:3]
    id_sensor = dato[3:5]
    valores = dato.split(":")[1:]
    return tipo_sensor, id_sensor, valores


def crear_objeto_sensor(tipo_sensor, id_sensor, valores):
    if tipo_sensor == "MOV":
        return MovimientoPIR(int(valores[0]))
    elif tipo_sensor == "LUZ":
        return Luz(int(valores[0]))
    elif tipo_sensor == "DHT":
        humedad = float(valores[0])
        temperatura = float(valores[1])
        return DHT(temperatura, humedad)
    else:
        return None


def main(self):
    self.mongo_temp = MongoSync("TemperatureHumiditySensor", "DHT.json", "local_DHT.json")
    self.mongo_light = MongoSync("LightSensor", "luz.json", "local_luz.json")
    self.mongo_pir = MongoSync("PirSensor", "pir.json", "local_pir.json")
    api_url = os.getenv("API_ENDPOINT") # Replace with your actual API endpoint

    try:
        ser = serial.Serial('COM4', 9600, timeout=1)
        time.sleep(2)
        last_api_check = 0
        check_interval = 60  # Check API every 60 seconds

        while True:
            # Check if it's time to query the API
            current_time = time.time()
            if current_time - last_api_check >= check_interval:
                actualizar_variables_desde_api(api_url)
                last_api_check = current_time

            # Process serial data
            if ser.in_waiting > 0:
                linea = ser.readline().decode('latin-1').strip()
                if linea:
                    tipo_sensor, id_sensor, valor = procesar_dato(linea)
                    sensor = crear_objeto_sensor(tipo_sensor, id_sensor, valor)
                    if sensor is not None:
                        print(sensor.guardar())

            # Small delay to prevent CPU overuse
            time.sleep(0.1)

    except serial.SerialException as e:
        print(f"Error al abrir el puerto serial: {e}")
    except KeyboardInterrupt:
        print("Terminando el programa...")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()


if __name__ == "__main__":
    main()