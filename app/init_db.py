from sqlalchemy import create_engine
from .database import SQLALCHEMY_DATABASE_URL
from .models import Base

def init_db():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    print("База данных успешно инициализирована")

if __name__ == "__main__":
    init_db() 