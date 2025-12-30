# backend/app/core/config.py
"""
Application configuration settings - COMPLETE AND FIXED VERSION
Single source of truth for all configuration
Path: backend/app/core/config.py
"""
from typing import List, Optional, Any
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    # ========================================================================
    # PROJECT INFO
    # ========================================================================
    PROJECT_NAME: str = "Enterprise Modeling Platform"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=True)
    LOG_LEVEL: str = Field(default="INFO")
    
    # ========================================================================
    # API CONFIGURATION
    # ========================================================================
    API_V1_STR: str = "/api/v1"
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)
    ALLOWED_HOSTS: str = Field(default="*")
    
    # ========================================================================
    # CORS CONFIGURATION - FIXED
    # ========================================================================
    CORS_ORIGINS: str = Field(
        default="http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000"
    )
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def validate_cors_origins(cls, v: Any) -> str:
        """Validate and normalize CORS origins"""
        if v is None or v == "":
            return "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000"
        if isinstance(v, str):
            return v
        if isinstance(v, list):
            return ",".join(v)
        return str(v)
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list"""
        if not self.CORS_ORIGINS:
            return [
                "http://localhost:5173",
                "http://localhost:3000",
                "http://127.0.0.1:5173",
                "http://127.0.0.1:3000"
            ]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.ENVIRONMENT.lower() in ["development", "dev", "local"]
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.ENVIRONMENT.lower() in ["production", "prod"]
    
    # ========================================================================
    # DATABASE - POSTGRESQL
    # ========================================================================
    POSTGRES_USER: str = Field(default="modeling")
    POSTGRES_PASSWORD: str = Field(default="modeling_dev")
    POSTGRES_HOST: str = Field(default="postgres")
    POSTGRES_PORT: int = Field(default=5432)
    POSTGRES_DB: str = Field(default="modeling_platform")
    
    # Connection pool settings
    DB_POOL_SIZE: int = Field(default=20)
    DB_MAX_OVERFLOW: int = Field(default=10)
    DB_POOL_TIMEOUT: int = Field(default=30)
    DB_POOL_RECYCLE: int = Field(default=3600)
    
    @property
    def DATABASE_URL(self) -> str:
        """Construct synchronous database URL"""
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
    
    @property
    def ASYNC_DATABASE_URL(self) -> str:
        """Construct asynchronous database URL for async operations"""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
    
    # ========================================================================
    # GRAPH DATABASE - FALKORDB
    # ========================================================================
    FALKORDB_HOST: str = Field(default="falkordb")
    FALKORDB_PORT: int = Field(default=6379)
    FALKORDB_PASSWORD: Optional[str] = Field(default=None)
    FALKORDB_DB: int = Field(default=0)
    FALKORDB_GRAPH_NAME: str = Field(default="modeling_graph")
    
    # Connection settings
    FALKORDB_MAX_CONNECTIONS: int = Field(default=50)
    FALKORDB_SOCKET_TIMEOUT: int = Field(default=30)
    FALKORDB_CONNECTION_TIMEOUT: int = Field(default=10)
    FALKORDB_RETRY_ON_TIMEOUT: bool = Field(default=True)
    
    @property
    def FALKORDB_URL(self) -> str:
        """Construct FalkorDB connection URL"""
        if self.FALKORDB_PASSWORD:
            return f"redis://:{self.FALKORDB_PASSWORD}@{self.FALKORDB_HOST}:{self.FALKORDB_PORT}/{self.FALKORDB_DB}"
        return f"redis://{self.FALKORDB_HOST}:{self.FALKORDB_PORT}/{self.FALKORDB_DB}"
    
    # ========================================================================
    # CACHE - REDIS
    # ========================================================================
    REDIS_HOST: str = Field(default="redis")
    REDIS_PORT: int = Field(default=6379)
    REDIS_PASSWORD: Optional[str] = Field(default=None)
    REDIS_DB: int = Field(default=0)
    
    # Cache settings
    REDIS_MAX_CONNECTIONS: int = Field(default=50)
    REDIS_SOCKET_TIMEOUT: int = Field(default=5)
    REDIS_CONNECTION_TIMEOUT: int = Field(default=5)
    CACHE_TTL: int = Field(default=3600)  # 1 hour default
    
    @property
    def REDIS_URL(self) -> str:
        """Construct Redis connection URL"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # ========================================================================
    # SECURITY - JWT
    # ========================================================================
    SECRET_KEY: str = Field(
        default="your-secret-key-change-this-in-production-make-it-long-and-random"
    )
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60 * 24)  # 24 hours
    REFRESH_TOKEN_EXPIRE_MINUTES: int = Field(default=60 * 24 * 7)  # 7 days
    
    # Password requirements
    PASSWORD_MIN_LENGTH: int = Field(default=8)
    PASSWORD_MAX_LENGTH: int = Field(default=100)
    
    # ========================================================================
    # EMAIL (Optional - for notifications)
    # ========================================================================
    SMTP_HOST: Optional[str] = Field(default=None)
    SMTP_PORT: int = Field(default=587)
    SMTP_USER: Optional[str] = Field(default=None)
    SMTP_PASSWORD: Optional[str] = Field(default=None)
    SMTP_TLS: bool = Field(default=True)
    EMAIL_FROM: Optional[str] = Field(default=None)
    EMAIL_FROM_NAME: Optional[str] = Field(default="Enterprise Modeling Platform")
    
    # ========================================================================
    # FILE STORAGE (Optional - for exports/attachments)
    # ========================================================================
    UPLOAD_DIR: str = Field(default="/tmp/uploads")
    MAX_UPLOAD_SIZE: int = Field(default=10 * 1024 * 1024)  # 10MB
    ALLOWED_UPLOAD_EXTENSIONS: str = Field(
        default=".json,.xml,.sql,.cypher,.png,.jpg,.jpeg,.svg,.pdf"
    )
    
    @property
    def allowed_extensions_list(self) -> List[str]:
        """Get allowed upload extensions as a list"""
        return [ext.strip() for ext in self.ALLOWED_UPLOAD_EXTENSIONS.split(",")]
    
    # ========================================================================
    # WEBSOCKET
    # ========================================================================
    WEBSOCKET_HEARTBEAT_INTERVAL: int = Field(default=30)  # seconds
    WEBSOCKET_TIMEOUT: int = Field(default=60)  # seconds
    
    # ========================================================================
    # COLLABORATION
    # ========================================================================
    PRESENCE_TIMEOUT: int = Field(default=60)  # seconds
    LOCK_TIMEOUT: int = Field(default=300)  # 5 minutes
    
    # ========================================================================
    # RATE LIMITING
    # ========================================================================
    RATE_LIMIT_ENABLED: bool = Field(default=True)
    RATE_LIMIT_REQUESTS: int = Field(default=100)
    RATE_LIMIT_WINDOW: int = Field(default=60)  # seconds
    
    # ========================================================================
    # VALIDATION
    # ========================================================================
    
    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Ensure secret key is strong enough"""
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v
    
    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level"""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {allowed}")
        return v_upper


# Create settings instance
settings = Settings()


# Export settings
__all__ = ["settings", "Settings"]