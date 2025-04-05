from datetime import datetime
class Peso:

    def __init__(self,codigo, peso,zona, area_id):
        self.area_id = area_id
        self.codigo = codigo
        self.peso = peso
        self.zona = zona


    def serializar(self):
        return {
            "area_id": self.area_id,
            "$date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "area_name": self.zona,
            "exit_code": self.codigo,
            "weight_kg": self.peso,
            "weight_status": False,
        }

    def guardar(self):
        datos = self.serializar()
        return datos