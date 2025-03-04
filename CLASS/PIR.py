class MovimientoPIR:
    def __init__(self,id_sensor, estado, fecha_evento, ubicacion, alerta):
        self.id_sensor = id_sensor
        self.estado = estado
        self.fecha_evento = fecha_evento
        self.ubicacion = ubicacion
        self.alerta = alerta

    def serializar(self):
            return {
                "tipo_sensor": "pir",
                "id_sensor": self.id_sensor,
                "estado": self.estado,
                "fecha_evento": self.fecha_evento,
                "ubicacion": self.ubicacion,
                "alerta": self.alerta
            }