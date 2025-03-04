class Rfid:
    def __init__(self, id_sensor,tarjeta_id,usuario_id,nombre_usuario,fecha_registro,evento,ubicacion):
        self.id_sensor = id_sensor
        self.tarjeta_id = tarjeta_id
        self.usuario_id = usuario_id
        self.fecha_registro = fecha_registro
        self.evento = evento
        self.ubicacion = ubicacion

    def serializar(self):
            return {
                "tipo_sensor": "rfid",
                "id_sensor": self.id_sensor,
                "tarjeta_id": self.tarjeta_id,
                "usuario_id": self.usuario_id,
                "fecha_registro": self.fecha_registro,
                "evento": self.evento,
                "ubicacion": self.ubicacion
            }