# backend/app/db/base.py
"""
Database Base Class - FIXED to prevent circular imports
Path: backend/app/db/base.py

CRITICAL: This file should ONLY contain the Base class definition.
DO NOT import any models here - that creates circular dependencies.
Models should import Base from here, not the other way around.
"""
from sqlalchemy.ext.declarative import declarative_base

# Base class for all SQLAlchemy models
Base = declarative_base()

# DO NOT IMPORT MODELS HERE!
# Models will import this Base class
# If you need to import models, do it in:
# - app/models/__init__.py (for model registration)
# - app/db/init_db.py (for table creation)
# - Individual files that need specific models