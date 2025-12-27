# backend/app/models/base.py
"""
Import Base from db.base for convenience
This allows models to import from app.models.base
"""
from app.db.base import Base

__all__ = ['Base']