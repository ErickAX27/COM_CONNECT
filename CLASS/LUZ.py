from MongoSync import MongoSync
class Luz:
    def __init__(self, id_sensor, nivel_luz, fecha_registro, ubicacion, alerta):
        self.id_sensor = id_sensor
        self.nivel_luz = nivel_luz
        self.fecha_registro = fecha_registro
        self.ubicacion = ubicacion
        self.alerta = alerta
        self.mongo_sync = MongoSync("LightSensor", "luz.json","local_luz.json")

    def serializar(self):
            return {
                "tipo_sensor": "lux",
                "id_sensor": self.id_sensor,
                "nivel_luz": self.nivel_luz,
                "fecha_registro": self.fecha_registro,
                "ubicacion": self.ubicacion,
                "alerta": self.alerta
            }

    def guardar(self):
        datos = [self.serializar()]
        self.mongo_sync.enviar_datos(datos)