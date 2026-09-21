"""
Configuración de base de datos SQLite con SQLAlchemy 2.0.
"""
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

BASE_DIR = Path(__file__).parent.parent
DB_PATH  = BASE_DIR / "yt_outlier_lab.db"

# Eliminar DB al iniciar si está corrupta (solo desarrollo)
# if DB_PATH.exists():
#     DB_PATH.unlink()

engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False},
    echo=False,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_session():
    return SessionLocal()


def init_db():
    # Importar TODOS los modelos antes de crear las tablas
    from core.models import (
        Channel, Video, VideoSnapshot,
        TopicCluster, IdeaNote, QuotaLog
    )
    # Esto crea TODAS las tablas según los modelos actuales
    Base.metadata.create_all(bind=engine)
    print("✅ Base de datos inicializada correctamente.")
    print(f"📁 Ubicación: {DB_PATH}")