from datetime import datetime
class Peso:

    def __init__(self,codigo, peso,zona, area_id, protocolo):
        self.area_id = area_id
        self.codigo = codigo
        self.peso = peso
        self.zona = zona
        if protocolo == "ADD": self.status = 1
        else : self.status = 0


    def serializar(self):
        return {
            "exit_code": self.codigo,
            "weight_kg": self.peso,
            "status": self.status,
            "area_id": self.area_id,
            "event_date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        }

    def guardar(self):
        datos = self.serializar()
        return datos