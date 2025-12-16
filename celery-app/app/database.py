# app/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from contextlib import contextmanager

DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://celery_user:celery_pass@localhost:5432/celery_db'
)

engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_context():
    """Context manager para usar en tareas de Celery"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Crear todas las tablas"""
    Base.metadata.create_all(bind=engine)
