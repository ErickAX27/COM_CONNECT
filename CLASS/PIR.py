import time
from MongoSync import MongoSync
class MovimientoPIR:
    def __init__(self,valor):
        if valor == 1:
            self.motion_detected = True
            self.alert_triggered = True
            self.alert_message = "Movement detected in the storage area"
        else:
            self.motion_detected = False
            self.alert_triggered = False
            self.alert_message = "No movement detected in the storage area"
        self.event_date = time.strftime("%Y-%m-%d %H:%M:%S")

    def serializar(self):
        return {
            "motion_detected": self.motion_detected,
            "alert_triggered": self.alert_triggered,
            "alert_message": self.alert_message,
            "event_date": self.event_date
        }

    def guardar(self):
        datos = self.serializar()
        return datos