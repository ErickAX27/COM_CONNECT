class DHT:
    def __init__(self, id_sensor, temperatura, humedad, fecha_registro, ubicacion, alerta):
        self.id_sensor = id_sensor
        self.temperatura = temperatura
        self.humedad = humedad
        self.fecha_registro = fecha_registro
        self.ubicacion = ubicacion
        self.alerta = alerta

    def serializar(self):
            return {
                "tipo_sensor": "temperatura_humedad",
                "id_sensor": self.id_sensor,
                "temperatura": self.temperatura,
                "humedad": self.humedad,
                "fecha_registro": self.fecha_registro,
                "ubicacion": self.ubicacion,
                "alerta": self.alerta
            }