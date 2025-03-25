from MongoSync import MongoSync
import time
class Luz:
    def __init__(self, valor):
        if valor == 1:
            self.status = "off"
            self.alert_triggered = False
            self.alert_message = "The light is off in the storage area"
        else:
            self.status = "on"
            self.alert_triggered = True
            self.alert_message = "The light is on in the storage area"
        self.event_date = time.strftime("%Y-%m-%d %H:%M:%S")

    def serializar(self):
            return {
                "status": self.status,
                "event_date": self.event_date,
                "alert_triggered": self.alert_triggered,
                "alert_message": self.alert_message
            }

    def guardar(self):
        datos = self.serializar()
        return datos
