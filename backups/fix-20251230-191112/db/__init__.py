# backend/app/db/__init__.py
"""
Database package initialization - FIXED
Path: backend/app/db/__init__.py

This module exports database utilities.
Model imports are handled in app/models/__init__.py
"""
from app.db.base import Base
from app.db.session import (
    get_db,
    init_db,
    close_db,
    engine,
    AsyncSessionLocal,
    SessionLocal,
)

__all__ = [
    "Base",
    "get_db",
    "init_db",
    "close_db",
    "engine",
    "AsyncSessionLocal",
    "SessionLocal",
]