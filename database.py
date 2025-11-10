from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models import Base
import os
from dotenv import load_dotenv

load_dotenv()

# Database URL from env or default to SQLite for dev
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./spinthewheel.db")

# For PostgreSQL, use: postgresql://user:password@localhost/dbname
# For SQLite (dev), use: sqlite:///./spinthewheel.db

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_db_and_tables():
    Base.metadata.create_all(bind=engine)
