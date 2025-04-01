from datetime import datetime
class Cerradura:
    def __init__(self, id_sensor,evento,origen):
        self.id_sensor = id_sensor
        self.evento = evento
        self.origen = origen


    def serializar(self):
        return {
            "sensor_id": self.id_sensor,
            "event_type": self.evento,
            "event_date": {
                "$date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000Z")
            },
            "origin":self.origen,
        }

