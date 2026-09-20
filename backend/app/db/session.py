from sqlalchemy.orm import DeclarativeBase, Session,sessionmaker
from sqlalchemy import create_engine
from app.core.config import settings

class Base(DeclarativeBase):
    pass


engine = create_engine(settings.database_url)

SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()