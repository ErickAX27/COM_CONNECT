import os
from MongoSync import MongoSync
from dotenv import load_dotenv
from CLASS.CERRADURA import Cerradura
load_dotenv()
print(os.getenv("MONGO_STRING"))
mongo_temp = MongoSync("LockEvents", "lck.json", "local_lck.json")
cerradura = Cerradura(1, "ACCESO", "PASSWORD")
mongo_temp.guardar_datos(cerradura.serializar())
print(mongo_temp.consultar())
mongo_temp.subir_a_mongo()
print(mongo_temp.consultar())

