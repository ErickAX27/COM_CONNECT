import time
class Rfid:
    def __init__(self, rfid_code, name, position, area):
        self.rfid_code = rfid_code
        self.name = name
        self.position = position
        self.area = area
        self.event_date = time.strftime("%Y-%m-%d %H:%M:%S")

    def serializar(self):
        return {
            "rfid_code": self.rfid_code,
            "name": self.name,
            "position": self.position,
            "area": self.area,
            "event_date": self.event_date
        }

    def guardar(self):
        datos = self.serializar()
        return datos