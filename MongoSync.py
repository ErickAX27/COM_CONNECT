import json
import threading
import time
from pymongo import MongoClient, errors
import logging
import os
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.WARNING)

class MongoSync:
    def __init__(self, nombre_coleccion: str, archivo_json: str, respaldo_json: str):
        self.nombre_coleccion = nombre_coleccion
        self.archivo_json = archivo_json
        self.respaldo_json = respaldo_json
        self.mongo_uri = os.getenv("MONGO_STRING")
        self.cliente = None
        self.base_datos = None
        self.coleccion = None
        self.modo_sin_conexion = True
        self.intento_reconexion = False
        threading.Thread(target=self.intentar_reconexion, daemon=True).start()

    def conectar_a_mongo(self):
        if self.esta_conectado():
            return
        try:
            self.cliente = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=2)
            self.base_datos = self.cliente["python"]
            self.coleccion = self.base_datos[self.nombre_coleccion]
            self.cliente.server_info()
            self.modo_sin_conexion = False
            logging.info("Conexión a MongoDB establecida correctamente.")
        except (errors.ServerSelectionTimeoutError, errors.ConfigurationError):
            self.cliente = None
            self.coleccion = None
            self.modo_sin_conexion = True

    def intentar_reconexion(self):
        while True:
            if self.modo_sin_conexion and not self.intento_reconexion:
                self.intento_reconexion = True
                logging.info("Intentando reconectar a MongoDB en segundo plano...")
                self.conectar_a_mongo()
                self.intento_reconexion = False
            time.sleep(30)

    def esta_conectado(self):
        return self.cliente is not None and self.coleccion is not None

    def limpiar_datos(self, datos):
        for dato in datos:
            if "_id" in dato:
                del dato["_id"]
        return datos

    def enviar_datos(self, dato: dict):
        if not isinstance(dato, dict):
            raise ValueError("El parámetro debe ser un objeto JSON.")
        self.guardar_en_respaldo(dato)
        self.guardar_en_local(dato)
        dato = self.limpiar_datos([dato])[0]

        if self.esta_conectado():
            try:
                self.coleccion.insert_one(dato)
            except errors.PyMongoError:
                pass

    def guardar_en_local(self, dato: dict):
        self._guardar_dato(self.archivo_json, dato)

    def guardar_en_respaldo(self, dato: dict):
        self._guardar_dato(self.respaldo_json, dato)

    def _guardar_dato(self, archivo_path: str, dato: dict):
        datos = []
        if os.path.exists(archivo_path):
            with open(archivo_path, "r") as archivo:
                try:
                    datos = json.load(archivo)
                except json.JSONDecodeError:
                    pass
        datos.append(dato)
        with open(archivo_path, "w") as archivo:
            json.dump(datos, archivo, indent=4)