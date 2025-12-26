"""
Application configuration settings
"""

from typing import List, Optional, Union
from pydantic import field_validator, ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict
import secrets


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
        case_sensitive=True,
        # CRITICAL: This prevents Pydantic from trying to parse lists as JSON
        env_parse_none_str="null",
    )
    
    # Application
    PROJECT_NAME: str = "Enterprise Modeling Platform"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Graph-native enterprise modeling platform"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    LOG_LEVEL: str = "INFO"
    
    # API
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # 7 days
    
    # CORS - Using string type to avoid JSON parsing issues
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://localhost:8000,http://127.0.0.1:3000,http://127.0.0.1:5173,http://127.0.0.1:8000"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """
        Get CORS origins as a list
        
        Returns:
            List of allowed origin URLs
        """
        if isinstance(self.CORS_ORIGINS, str):
            # Handle comma-separated string
            if self.CORS_ORIGINS.startswith("["):
                # It's a JSON array string, parse it
                import json
                return json.loads(self.CORS_ORIGINS)
            else:
                # It's a comma-separated string
                return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
        elif isinstance(self.CORS_ORIGINS, list):
            return self.CORS_ORIGINS
        return []
    
    # Alias for backwards compatibility
    @property
    def BACKEND_CORS_ORIGINS(self) -> List[str]:
        """Alias for cors_origins_list for backwards compatibility"""
        return self.cors_origins_list
    
    # PostgreSQL Database
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "modeling"
    POSTGRES_PASSWORD: str = "modeling_dev"
    POSTGRES_DB: str = "modeling"
    
    # SQLAlchemy Database URI
    SQLALCHEMY_DATABASE_URI: Optional[str] = None
    
    @field_validator("SQLALCHEMY_DATABASE_URI", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info: ValidationInfo) -> str:
        if isinstance(v, str) and v:
            return v
        
        # Build database URL from components
        user = info.data.get("POSTGRES_USER", "modeling")
        password = info.data.get("POSTGRES_PASSWORD", "modeling_dev")
        host = info.data.get("POSTGRES_HOST", "localhost")
        port = info.data.get("POSTGRES_PORT", 5432)
        db = info.data.get("POSTGRES_DB", "modeling")
        
        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"
    
    # Database pool settings
    SQLALCHEMY_ECHO: bool = False
    SQLALCHEMY_POOL_SIZE: int = 20
    SQLALCHEMY_MAX_OVERFLOW: int = 10
    SQLALCHEMY_POOL_TIMEOUT: int = 30
    SQLALCHEMY_POOL_RECYCLE: int = 3600
    
    # FalkorDB - Graph Database
    FALKORDB_HOST: str = "localhost"
    FALKORDB_PORT: int = 6379
    FALKORDB_GRAPH: str = "modeling_graph"
    FALKORDB_PASSWORD: Optional[str] = None
    
    # Redis - Caching & Real-time
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_MAX_CONNECTIONS: int = 50
    
    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 30
    WS_MAX_CONNECTIONS_PER_USER: int = 10
    
    # Collaboration
    COLLABORATION_LOCK_TIMEOUT: int = 300  # 5 minutes
    COLLABORATION_PRESENCE_TIMEOUT: int = 60  # 1 minute
    
    # Validation
    VALIDATION_MAX_NODES: int = 10000
    VALIDATION_MAX_EDGES: int = 20000
    VALIDATION_TIMEOUT: int = 30  # seconds
    
    # Layout Engine
    LAYOUT_COMPUTATION_TIMEOUT: int = 60  # seconds
    LAYOUT_MAX_ITERATIONS: int = 1000
    
    # Export
    EXPORT_MAX_FILE_SIZE: int = 100  # MB
    EXPORT_TIMEOUT: int = 120  # seconds
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 50  # MB
    ALLOWED_UPLOAD_EXTENSIONS: List[str] = [
        ".json",
        ".xml",
        ".xmi",
        ".sql",
        ".cypher",
    ]
    
    # Versioning
    MAX_VERSIONS_PER_MODEL: int = 100
    VERSION_RETENTION_DAYS: int = 90
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # Audit & Logging
    AUDIT_LOG_RETENTION_DAYS: int = 365
    ENABLE_QUERY_LOGGING: bool = False
    
    # Performance
    MAX_PAGE_SIZE: int = 100
    DEFAULT_PAGE_SIZE: int = 20
    
    # Caching
    CACHE_TTL_SHORT: int = 300  # 5 minutes
    CACHE_TTL_MEDIUM: int = 3600  # 1 hour
    CACHE_TTL_LONG: int = 86400  # 24 hours
    
    # Background Tasks
    CLEANUP_INTERVAL_HOURS: int = 24
    
    # Feature Flags
    ENABLE_EXPERIMENTAL_FEATURES: bool = False
    ENABLE_TELEMETRY: bool = False
    
    # First Admin User
    FIRST_ADMIN_EMAIL: str = "admin@example.com"
    FIRST_ADMIN_PASSWORD: str = "change-this-password"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.ENVIRONMENT.lower() in ["development", "dev"]
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.ENVIRONMENT.lower() in ["production", "prod"]
    
    @property
    def is_testing(self) -> bool:
        """Check if running in testing mode"""
        return self.ENVIRONMENT.lower() in ["testing", "test"]


# Global settings instance
settings = Settings()