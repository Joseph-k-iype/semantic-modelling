"""
Application configuration using Pydantic Settings
"""

from typing import List, Optional
from functools import lru_cache

from pydantic import Field, validator, PostgresDsn
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """
    
    # Application
    PROJECT_NAME: str = "Enterprise Modeling Platform"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=False, env="DEBUG")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    # API
    API_V1_STR: str = "/api/v1"
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    
    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:5173",
        ],
        env="CORS_ORIGINS",
    )
    
    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    # Database - PostgreSQL
    POSTGRES_USER: str = Field(default="modeling", env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field(default="modeling_dev", env="POSTGRES_PASSWORD")
    POSTGRES_HOST: str = Field(default="localhost", env="POSTGRES_HOST")
    POSTGRES_PORT: int = Field(default=5432, env="POSTGRES_PORT")
    POSTGRES_DB: str = Field(default="modeling_platform", env="POSTGRES_DB")
    DATABASE_URL: Optional[str] = Field(default=None, env="DATABASE_URL")
    
    @validator("DATABASE_URL", pre=True)
    def assemble_database_url(cls, v, values):
        if v:
            return v
        
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_HOST"),
            port=values.get("POSTGRES_PORT"),
            path=f"/{values.get('POSTGRES_DB')}",
        )
    
    # Database pool settings
    DB_POOL_SIZE: int = Field(default=20, env="DB_POOL_SIZE")
    DB_MAX_OVERFLOW: int = Field(default=10, env="DB_MAX_OVERFLOW")
    DB_POOL_TIMEOUT: int = Field(default=30, env="DB_POOL_TIMEOUT")
    DB_POOL_RECYCLE: int = Field(default=3600, env="DB_POOL_RECYCLE")
    
    # FalkorDB - Graph Database
    FALKORDB_HOST: str = Field(default="localhost", env="FALKORDB_HOST")
    FALKORDB_PORT: int = Field(default=6379, env="FALKORDB_PORT")
    FALKORDB_GRAPH: str = Field(default="modeling_graph", env="FALKORDB_GRAPH")
    FALKORDB_PASSWORD: Optional[str] = Field(default=None, env="FALKORDB_PASSWORD")
    
    # Redis - Caching & Real-time
    REDIS_HOST: str = Field(default="localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(default=6380, env="REDIS_PORT")
    REDIS_DB: int = Field(default=0, env="REDIS_DB")
    REDIS_PASSWORD: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    REDIS_MAX_CONNECTIONS: int = Field(default=50, env="REDIS_MAX_CONNECTIONS")
    
    # Authentication & Security
    SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        env="SECRET_KEY",
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    
    # Password hashing
    PWD_CONTEXT_SCHEMES: List[str] = ["bcrypt"]
    PWD_CONTEXT_DEPRECATED: str = "auto"
    
    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = Field(default=30, env="WS_HEARTBEAT_INTERVAL")
    WS_MAX_CONNECTIONS_PER_USER: int = Field(default=10, env="WS_MAX_CONNECTIONS_PER_USER")
    
    # Collaboration
    COLLABORATION_LOCK_TIMEOUT: int = Field(default=300, env="COLLABORATION_LOCK_TIMEOUT")  # 5 minutes
    COLLABORATION_PRESENCE_TIMEOUT: int = Field(default=60, env="COLLABORATION_PRESENCE_TIMEOUT")  # 1 minute
    
    # Validation
    VALIDATION_MAX_NODES: int = Field(default=10000, env="VALIDATION_MAX_NODES")
    VALIDATION_MAX_EDGES: int = Field(default=20000, env="VALIDATION_MAX_EDGES")
    VALIDATION_TIMEOUT: int = Field(default=30, env="VALIDATION_TIMEOUT")  # seconds
    
    # Layout Engine
    LAYOUT_COMPUTATION_TIMEOUT: int = Field(default=60, env="LAYOUT_COMPUTATION_TIMEOUT")  # seconds
    LAYOUT_MAX_ITERATIONS: int = Field(default=1000, env="LAYOUT_MAX_ITERATIONS")
    
    # Export
    EXPORT_MAX_FILE_SIZE: int = Field(default=100, env="EXPORT_MAX_FILE_SIZE")  # MB
    EXPORT_TIMEOUT: int = Field(default=120, env="EXPORT_TIMEOUT")  # seconds
    
    # File Upload
    MAX_UPLOAD_SIZE: int = Field(default=50, env="MAX_UPLOAD_SIZE")  # MB
    ALLOWED_UPLOAD_EXTENSIONS: List[str] = [
        ".json",
        ".xml",
        ".xmi",
        ".sql",
        ".cypher",
    ]
    
    # Versioning
    MAX_VERSIONS_PER_MODEL: int = Field(default=100, env="MAX_VERSIONS_PER_MODEL")
    VERSION_RETENTION_DAYS: int = Field(default=90, env="VERSION_RETENTION_DAYS")
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    RATE_LIMIT_PER_HOUR: int = Field(default=1000, env="RATE_LIMIT_PER_HOUR")
    
    # Audit & Logging
    AUDIT_LOG_RETENTION_DAYS: int = Field(default=365, env="AUDIT_LOG_RETENTION_DAYS")
    ENABLE_QUERY_LOGGING: bool = Field(default=False, env="ENABLE_QUERY_LOGGING")
    
    # Performance
    MAX_PAGE_SIZE: int = Field(default=100, env="MAX_PAGE_SIZE")
    DEFAULT_PAGE_SIZE: int = Field(default=20, env="DEFAULT_PAGE_SIZE")
    
    # Caching
    CACHE_TTL_SHORT: int = 300  # 5 minutes
    CACHE_TTL_MEDIUM: int = 3600  # 1 hour
    CACHE_TTL_LONG: int = 86400  # 24 hours
    
    # Background Tasks
    CLEANUP_INTERVAL_HOURS: int = Field(default=24, env="CLEANUP_INTERVAL_HOURS")
    
    # Feature Flags
    ENABLE_EXPERIMENTAL_FEATURES: bool = Field(default=False, env="ENABLE_EXPERIMENTAL_FEATURES")
    ENABLE_TELEMETRY: bool = Field(default=False, env="ENABLE_TELEMETRY")
    
    # First Admin User
    FIRST_ADMIN_EMAIL: str = Field(default="admin@example.com", env="FIRST_ADMIN_EMAIL")
    FIRST_ADMIN_PASSWORD: str = Field(default="change-this-password", env="FIRST_ADMIN_PASSWORD")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        
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


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance
    """
    return Settings()


# Global settings instance
settings = get_settings()