from datetime import datetime
class Peso:

    def __init__(self,codigo, peso,zona):
        self.codigo = codigo
        self.peso = peso
        self.zona = zona


    def serializar(self):
        return {
            "event_date": {
                "$date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000Z")
            },
            "area_name": self.zona,
            "delivery_id": self.codigo,
            "weight_kg": self.peso
        }

    def guardar(self):
        datos = self.serializar()
        return datos