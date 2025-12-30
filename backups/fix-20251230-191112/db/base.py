"""
Database Base Class
"""
from sqlalchemy.ext.declarative import declarative_base

# Base class for all models
Base = declarative_base()

from app.models.user import User
from app.models.model import Model
from app.models.diagram import Diagram