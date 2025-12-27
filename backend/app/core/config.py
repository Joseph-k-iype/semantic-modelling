# backend/app/core/config.py
"""
Application configuration settings
SINGLE SOURCE OF TRUTH for all configuration
"""
from typing import List, Optional, Any
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Application settings"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )
    
    # Project Info
    PROJECT_NAME: str = "Enterprise Modeling Platform"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=True)
    
    # API
    API_V1_STR: str = "/api/v1"
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)
    
    # CORS - Fixed to handle empty strings properly
    CORS_ORIGINS: str = Field(
        default="http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000"
    )
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def validate_cors_origins(cls, v: Any) -> str:
        """Validate and normalize CORS origins"""
        if v is None or v == "":
            return "http://localhost:5173,http://localhost:3000"
        if isinstance(v, str):
            return v
        if isinstance(v, list):
            return ",".join(v)
        return str(v)
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list"""
        if not self.CORS_ORIGINS:
            return ["http://localhost:5173", "http://localhost:3000"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
    
    # Database - PostgreSQL
    POSTGRES_USER: str = Field(default="postgres")
    POSTGRES_PASSWORD: str = Field(default="postgres")
    POSTGRES_HOST: str = Field(default="postgres")
    POSTGRES_PORT: int = Field(default=5432)
    POSTGRES_DB: str = Field(default="modeling_platform")
    
    # Database pool settings
    DB_POOL_SIZE: int = Field(default=20)
    DB_MAX_OVERFLOW: int = Field(default=10)
    DB_POOL_TIMEOUT: int = Field(default=30)
    DB_POOL_RECYCLE: int = Field(default=3600)
    
    @property
    def DATABASE_URL(self) -> str:
        """Construct database URL"""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    @property
    def ASYNC_DATABASE_URL(self) -> str:
        """Construct async database URL"""
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # Redis
    REDIS_HOST: str = Field(default="redis")
    REDIS_PORT: int = Field(default=6379)
    REDIS_DB: int = Field(default=0)
    REDIS_PASSWORD: Optional[str] = Field(default=None)
    REDIS_MAX_CONNECTIONS: int = Field(default=50)
    
    @property
    def REDIS_URL(self) -> str:
        """Construct Redis URL"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # FalkorDB (Graph Database)
    FALKORDB_HOST: str = Field(default="falkordb")
    FALKORDB_PORT: int = Field(default=6379)
    FALKORDB_GRAPH_NAME: str = Field(default="modeling_graph")
    FALKORDB_PASSWORD: Optional[str] = Field(default=None)
    
    @property
    def FALKORDB_URL(self) -> str:
        """Construct FalkorDB URL"""
        if self.FALKORDB_PASSWORD:
            return f"redis://:{self.FALKORDB_PASSWORD}@{self.FALKORDB_HOST}:{self.FALKORDB_PORT}"
        return f"redis://{self.FALKORDB_HOST}:{self.FALKORDB_PORT}"
    
    # Security
    SECRET_KEY: str = Field(
        default="your-secret-key-change-this-in-production-min-32-chars-long"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)
    
    # Password hashing
    PWD_CONTEXT_SCHEMES: List[str] = ["bcrypt"]
    PWD_CONTEXT_DEPRECATED: str = "auto"
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # File uploads
    MAX_UPLOAD_SIZE: int = Field(default=10485760)  # 10MB
    ALLOWED_UPLOAD_EXTENSIONS: List[str] = [".json", ".xml", ".xmi", ".sql", ".cypher"]
    
    # Audit & Monitoring
    AUDIT_LOG_RETENTION_DAYS: int = Field(default=365)
    ENABLE_QUERY_LOGGING: bool = Field(default=False)
    
    # Performance
    MAX_PAGE_SIZE: int = Field(default=100)
    DEFAULT_PAGE_SIZE: int = Field(default=20)
    
    # Caching
    CACHE_TTL_SHORT: int = 300  # 5 minutes
    CACHE_TTL_MEDIUM: int = 3600  # 1 hour
    CACHE_TTL_LONG: int = 86400  # 24 hours
    
    # Background Tasks
    CLEANUP_INTERVAL_HOURS: int = Field(default=24)
    
    # Feature Flags
    ENABLE_EXPERIMENTAL_FEATURES: bool = Field(default=False)
    ENABLE_TELEMETRY: bool = Field(default=False)
    
    # First Admin User
    FIRST_ADMIN_EMAIL: str = Field(default="admin@example.com")
    FIRST_ADMIN_PASSWORD: str = Field(default="change-this-password")
    
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


# Global settings instance - SINGLE INSTANCE
settings = Settings()