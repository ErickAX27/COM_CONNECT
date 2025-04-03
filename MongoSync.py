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
        self.archivo_json = archivo_json  # Archivo para pendientes
        self.respaldo_json = respaldo_json  # Archivo para respaldo permanente
        self.mongo_uri = os.getenv("MONGO_STRING")
        self.cliente = None
        self.base_datos = None
        self.coleccion = None
        self.modo_sin_conexion = True
        self.intento_reconexion = False

        # Intentar conectar de inmediato al crearse la instancia.
        self.conectar_a_mongo()

        # Iniciar un hilo en segundo plano que intente reconectar cada 30 segundos
        threading.Thread(target=self.intentar_reconexion, daemon=True).start()

    def conectar_a_mongo(self):
        if self.esta_conectado():
            return
        try:
            self.cliente = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=2000)
            self.base_datos = self.cliente["GateeDB"]
            self.coleccion = self.base_datos[self.nombre_coleccion]
            # Forzar la conexión con server_info()
            self.cliente.server_info()
            self.modo_sin_conexion = False
            logging.info("Conexión a MongoDB establecida correctamente.")
        except (errors.ServerSelectionTimeoutError, errors.ConfigurationError) as e:
            self.cliente = None
            self.coleccion = None
            self.modo_sin_conexion = True
            logging.warning("No se pudo conectar a MongoDB. Modo offline activado: " + str(e))

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

    def guardar_datos(self, dato: dict):
        """Guarda los datos localmente en el archivo de pendientes y en el respaldo"""
        if not isinstance(dato, dict):
            raise ValueError("El parámetro debe ser un objeto JSON.")

        # Guardar en archivo de pendientes
        self._guardar_dato(self.archivo_json, dato)
        # Guardar en respaldo permanente
        self._guardar_dato(self.respaldo_json, dato)

    def subir_a_mongo(self):
        """Intenta subir los datos pendientes a MongoDB"""
        # Intentar reconectar justo antes de subir si no está conectado
        if not self.esta_conectado():
            logging.info("Intentando conectar a MongoDB antes de subir datos.")
            self.conectar_a_mongo()

        if not self.esta_conectado():
            logging.warning("No hay conexión a MongoDB. Los datos se subirán cuando se restablezca la conexión.")
            return False

        # Leer datos pendientes
        pendientes = []
        if os.path.exists(self.archivo_json):
            with open(self.archivo_json, "r") as archivo:
                try:
                    pendientes = json.load(archivo)
                except json.JSONDecodeError:
                    pendientes = []

        if not pendientes:
            return True  # No hay datos pendientes

        # Limpiar datos (eliminando _id para poder serializarlos)
        pendientes = self.limpiar_datos(pendientes)

        # Intentar subir cada documento a MongoDB
        subidos_exitosamente = []
        try:
            for i, dato in enumerate(pendientes):
                self.coleccion.insert_one(dato)
                subidos_exitosamente.append(i)

            # Si se subieron todos, limpiar el archivo de pendientes
            if len(subidos_exitosamente) == len(pendientes):
                with open(self.archivo_json, "w") as archivo:
                    json.dump([], archivo)
            else:
                # Preservar los que no se pudieron subir
                pendientes_restantes = [p for i, p in enumerate(pendientes) if i not in subidos_exitosamente]
                with open(self.archivo_json, "w") as archivo:
                    json.dump(pendientes_restantes, archivo, indent=4)

            return True
        except errors.PyMongoError as e:
            logging.error(f"Error al subir datos a MongoDB: {e}")
            return False

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

    def consultar(self):
        if not self.esta_conectado():
            logging.warning("No hay conexión a MongoDB. No se pueden obtener documentos.")
            return []

        try:
            # Obtener todos los documentos de la colección
            documentos = list(self.coleccion.find({}))

            # Convertir ObjectId a string para lograr una serialización JSON correcta
            for documento in documentos:
                if "_id" in documento:
                    documento["_id"] = str(documento["_id"])

            logging.info(f"Se obtuvieron {len(documentos)} documentos de la colección {self.nombre_coleccion}.")
            return documentos

        except errors.PyMongoError as e:
            logging.error(f"Error al consultar documentos de MongoDB: {e}")
            return []