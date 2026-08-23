from database import engine
from database import Base
import models

Base.metadata.create_all(bind=engine)
print("Таблицы успешно созданы ✅")