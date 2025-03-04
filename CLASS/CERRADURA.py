class Cerradura:
    def __init__(self, id_sensor,usuario_id,estado,fecha_registro,evento,ubicacion):
        self.id_sensor = id_sensor
        self.usuario_id = usuario_id
        self.estado = estado
        self.fecha_registro = fecha_registro
        self.evento = evento
        self.ubicacion = ubicacion

    def serializar(self):
            return {
                "tipo_sensor": "cerradura",
                "id_sensor": self.id_sensor,
                "usuario_id": self.usuario_id,
                "estado": self.estado,
                "fecha_registro": self.fecha_registro,
                "evento": self.evento,
                "ubicacion": self.ubicacion
            }