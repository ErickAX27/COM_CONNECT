import serial
import time
from CLASS.PIR import MovimientoPIR
# from CLASS.PESO import Peso
from CLASS.LUZ import Luz
from CLASS.DHT import DHT

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

def main():
    try:
        ser = serial.Serial('COM5', 9600, timeout=1)
        time.sleep(2)
        while True:
            if ser.in_waiting > 0:
                linea = ser.readline().decode('latin-1').strip()
                if linea:
                    tipo_sensor, id_sensor, valor = procesar_dato(linea)
                    sensor = crear_objeto_sensor(tipo_sensor, id_sensor, valor)
                    if sensor is not None:
                        print(sensor.guardar())
    except serial.SerialException as e:
        print(f"Error al abrir el puerto serial: {e}")
    except KeyboardInterrupt:
        print("Terminando el programa...")
    finally:
        if ser.is_open:
            ser.close()

if __name__ == "__main__":
    main()