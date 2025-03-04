class Peso:
    def __init__(self,id_sensor, peso, fecha_registro, ubicacion, alerta):
        self.id_sensor = id_sensor
        self.peso = peso
        self.fecha_registro = fecha_registro
        self.ubicacion = ubicacion
        self.alerta = alerta

    def serializar(self):
            return {
                "tipo_sensor": "peso",
                "id_sensor": self.id_sensor,
                "peso": self.peso,
                "fecha_registro": self.fecha_registro,
                "ubicacion": self.ubicacion,
                "alerta": self.alerta
            }

