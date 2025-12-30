# backend/app/db/base.py
"""
Database Base Class - FIXED
Path: backend/app/db/base.py
"""
from sqlalchemy.ext.declarative import declarative_base

# Base class for all SQLAlchemy models
Base = declarative_base()
