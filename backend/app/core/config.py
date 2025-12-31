# backend/app/core/config.py
"""
Application configuration settings - COMPLETE FIX with all settings
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
    # CORS CONFIGURATION - CRITICAL FIX
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
        """Construct asynchronous database URL"""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
    
    # ========================================================================
    # GRAPH DATABASE - FALKORDB
    # ========================================================================
    FALKORDB_HOST: str = Field(default="falkordb")
    FALKORDB_PORT: int = Field(default=6379)
    FALKORDB_PASSWORD: str = Field(default="")
    FALKORDB_DB: int = Field(default=0)
    FALKORDB_GRAPH_NAME: str = Field(default="modeling_graph")
    
    # Connection settings
    FALKORDB_MAX_RETRIES: int = Field(default=3)
    FALKORDB_RETRY_DELAY: int = Field(default=1)
    FALKORDB_CONNECTION_TIMEOUT: int = Field(default=5)
    
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
    REDIS_PORT: int = Field(default=6380)
    REDIS_PASSWORD: str = Field(default="")
    REDIS_DB: int = Field(default=0)
    
    # Cache settings
    REDIS_MAX_CONNECTIONS: int = Field(default=10)
    REDIS_SOCKET_TIMEOUT: int = Field(default=5)
    REDIS_SOCKET_CONNECT_TIMEOUT: int = Field(default=5)
    
    @property
    def REDIS_URL(self) -> str:
        """Construct Redis connection URL"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # ========================================================================
    # SECURITY & AUTHENTICATION - CRITICAL FIX: All JWT settings included
    # ========================================================================
    SECRET_KEY: str = Field(default="your-super-secret-key-change-this-in-production-please-make-it-at-least-32-characters")
    ALGORITHM: str = Field(default="HS256")
    
    # Token expiration settings
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)
    
    # Password hashing
    BCRYPT_ROUNDS: int = Field(default=12)
    
    # JWT Settings (alternative names for backward compatibility)
    JWT_SECRET_KEY: Optional[str] = Field(default=None)
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: Optional[int] = Field(default=None)
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: Optional[int] = Field(default=None)
    
    def model_post_init(self, __context: Any) -> None:
        """Post initialization to handle JWT aliases"""
        # If JWT_ prefixed versions are provided, use them
        if self.JWT_SECRET_KEY:
            self.SECRET_KEY = self.JWT_SECRET_KEY
        if self.JWT_ACCESS_TOKEN_EXPIRE_MINUTES:
            self.ACCESS_TOKEN_EXPIRE_MINUTES = self.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        if self.JWT_REFRESH_TOKEN_EXPIRE_DAYS:
            self.REFRESH_TOKEN_EXPIRE_DAYS = self.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    
    # ========================================================================
    # EMAIL CONFIGURATION (Optional)
    # ========================================================================
    SMTP_HOST: Optional[str] = Field(default=None)
    SMTP_PORT: int = Field(default=587)
    SMTP_USER: Optional[str] = Field(default=None)
    SMTP_PASSWORD: Optional[str] = Field(default=None)
    SMTP_TLS: bool = Field(default=True)
    
    EMAILS_FROM_EMAIL: Optional[str] = Field(default=None)
    EMAILS_FROM_NAME: Optional[str] = Field(default="Enterprise Modeling Platform")
    
    # ========================================================================
    # WEBSOCKET CONFIGURATION
    # ========================================================================
    WS_MESSAGE_QUEUE_SIZE: int = Field(default=100)
    WS_HEARTBEAT_INTERVAL: int = Field(default=30)
    WS_CONNECTION_TIMEOUT: int = Field(default=60)
    
    # ========================================================================
    # FILE UPLOAD CONFIGURATION
    # ========================================================================
    MAX_UPLOAD_SIZE: int = Field(default=10485760)  # 10 MB
    ALLOWED_EXTENSIONS: List[str] = Field(default=["jpg", "jpeg", "png", "gif", "pdf", "svg", "json", "xml"])
    UPLOAD_DIR: str = Field(default="uploads")
    
    # ========================================================================
    # RATE LIMITING
    # ========================================================================
    RATE_LIMIT_ENABLED: bool = Field(default=True)
    RATE_LIMIT_PER_MINUTE: int = Field(default=100)
    RATE_LIMIT_WINDOW: int = Field(default=60)
    
    # ========================================================================
    # FEATURE FLAGS
    # ========================================================================
    ENABLE_GRAPH_FEATURES: bool = Field(default=True)
    ENABLE_REAL_TIME_COLLABORATION: bool = Field(default=True)
    ENABLE_EMAIL_VERIFICATION: bool = Field(default=False)
    ENABLE_AUDIT_LOGGING: bool = Field(default=True)
    ENABLE_QUERY_CACHING: bool = Field(default=True)
    ENABLE_COMPRESSION: bool = Field(default=True)
    
    # Cache TTL
    CACHE_TTL: int = Field(default=3600)
    
    # Development tools
    ENABLE_HOT_RELOAD: bool = Field(default=True)
    ENABLE_PROFILING: bool = Field(default=False)
    ENABLE_DEBUG_TOOLBAR: bool = Field(default=False)
    
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
    
    @field_validator("ACCESS_TOKEN_EXPIRE_MINUTES")
    @classmethod
    def validate_access_token_expire(cls, v: int) -> int:
        """Validate access token expiration"""
        if v < 1 or v > 1440:  # Max 24 hours
            raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES must be between 1 and 1440")
        return v
    
    @field_validator("REFRESH_TOKEN_EXPIRE_DAYS")
    @classmethod
    def validate_refresh_token_expire(cls, v: int) -> int:
        """Validate refresh token expiration"""
        if v < 1 or v > 90:  # Max 90 days
            raise ValueError("REFRESH_TOKEN_EXPIRE_DAYS must be between 1 and 90")
        return v


# Create settings instance
settings = Settings()


# Export settings
__all__ = ["settings", "Settings"]