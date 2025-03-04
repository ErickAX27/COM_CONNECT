class Huella:
    def __init__(self, id_sensor,usuario_id,nombre_usuario,huella_hash,fecha_registro,evento,ubicacion):
        self.id_sensor = id_sensor
        self.usuario_id = usuario_id
        self.nombre_usuario = nombre_usuario
        self.huella_hash = huella_hash
        self.fecha_registro = fecha_registro
        self.evento = evento
        self.ubicacion = ubicacion

    def serializar(self):
            return {
                "tipo_sensor": "huella_digital",
                "id_sensor": self.id_sensor,
                "nombre_usuario": self.nombre_usuario,
                "huella_hash": self.huella_hash,
                "fecha_registro": self.fecha_registro,
                "evento": self.evento,
                "ubicacion": self.ubicacion
            }