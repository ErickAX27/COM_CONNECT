import json
import threading
import time
from pymongo import MongoClient, errors
import logging

logging.basicConfig(level=logging.WARNING)

class MongoSync:
    def __init__(self, nombre_coleccion: str, archivo_json: str, respaldo_json: str):
        self.nombre_coleccion = nombre_coleccion
        self.archivo_json = archivo_json
        self.respaldo_json = respaldo_json
        self.mongo_uri = "mongodb+srv://lexus:amnesia00@cluster0.rydnf.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
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

    def enviar_datos(self, lista_datos: list):
        if not isinstance(lista_datos, list):
            raise ValueError("El parámetro debe ser una lista de objetos JSON.")
        self.guardar_en_respaldo(lista_datos)
        self.guardar_en_local(lista_datos)
        lista_datos = self.limpiar_datos(lista_datos)

        if self.esta_conectado():
            try:
                self.coleccion.insert_many(lista_datos)
            except errors.PyMongoError:
                pass

    def guardar_en_local(self, lista_datos: list):
        try:
            with open(self.archivo_json, "a") as archivo:
                for dato in lista_datos:
                    json.dump(dato, archivo)
                    archivo.write("\n")
        except IOError:
            pass

    def guardar_en_respaldo(self, lista_datos: list):
        try:
            with open(self.respaldo_json, "a") as archivo:
                for dato in lista_datos:
                    json.dump(dato, archivo)
                    archivo.write("\n")
        except IOError:
            pass
