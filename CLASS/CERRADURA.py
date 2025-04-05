from datetime import datetime
class Cerradura:
    def __init__(self, area_id,evento,origen):
        self.area_id = area_id
        self.evento = evento
        self.origen = origen


    def serializar(self):
        return {
            "area_id": self.area_id,
            "event_type": self.evento,
            "$date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "origin":self.origen,
        }

