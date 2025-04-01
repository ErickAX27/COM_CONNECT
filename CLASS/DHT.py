import time
class DHT:
    def __init__(self,Temperatura,Humedad):
        self.temperature_c = Temperatura
        self.humidity_percent = Humedad
        if self.temperature_c < 0 or self.temperature_c > 60:
            self.alert_triggered = True
            self.alert_message = "Temperature outside the permitted range"
        else:
            self.alert_triggered = False
            self.alert_message = "Temperature within the permitted range"
        if self.humidity_percent > 45:
            self.alert_triggered = True
            self.alert_message = "Humidity outside the permitted range"
        self.event_date = time.strftime("%Y-%m-%d %H:%M:%S")

    def serializar(self):
        return {
            "temperature_c": self.temperature_c,
            "humidity_percent": self.humidity_percent,
            "event_date": self.event_date,
            "alert_triggered": self.alert_triggered,
            "alert_message": self.alert_message
        }

    def guardar(self):
        datos = self.serializar()
        return datos
