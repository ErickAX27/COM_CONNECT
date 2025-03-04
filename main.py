import serial
import time
from CLASS.PIR import MovimientoPIR
from CLASS.PESO import Peso
from CLASS.LUZ import Luz

def procesar_dato(dato):
    tipo_sensor = dato[:3]
    id_sensor = dato[3:5]
    valor = dato.split(":")[1]
    return tipo_sensor, id_sensor, valor

def crear_objeto_sensor(tipo_sensor, id_sensor, valor):
    if tipo_sensor == "MOV":
        return MovimientoPIR(id_sensor, valor, time.strftime("%Y-%m-%d %H:%M:%S"), "Zona A", False)
    elif tipo_sensor == "PSO":
        return Peso(id_sensor, valor, time.strftime("%Y-%m-%d %H:%M:%S"), "Zona A", False)
    elif tipo_sensor == "LUZ":
        return Luz(id_sensor, valor, time.strftime("%Y-%m-%d %H:%M:%S"), "Zona A", False)
    else:
        raise ValueError("Tipo de sensor desconocido")

def main():
    try:
        ser = serial.Serial('COM5', 9600, timeout=1)
        time.sleep(2)
        while True:
            if ser.in_waiting > 0:
                linea = ser.readline().decode('utf-8').strip()
                if linea:
                    tipo_sensor, id_sensor, valor = procesar_dato(linea)
                    sensor = crear_objeto_sensor(tipo_sensor, id_sensor, valor)
                    print(sensor.serializar())
    except serial.SerialException as e:
        print(f"Error al abrir el puerto serial: {e}")
    except KeyboardInterrupt:
        print("Terminando el programa...")
    finally:
        if ser.is_open:
            ser.close()

if __name__ == "__main__":
    main()