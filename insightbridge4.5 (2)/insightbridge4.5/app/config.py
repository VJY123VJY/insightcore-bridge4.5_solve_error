"""
Configuration management using Pydantic Settings.
12-factor app compliant with security best practices.
Sensitive values are loaded from environment variables or .env file.
"""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Application configuration with security hardening."""
    
    # Application
    app_name: str = Field(default="InsightBridge", env="APP_NAME")
    app_version: str = Field(default="4.5.0", env="APP_VERSION")
    environment: str = Field(default="development", env="ENVIRONMENT")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Security
    secret_key: str = Field(
        default="",
        env="SECRET_KEY",
        description="CRITICAL: Set unique value in production"
    )
    
    # Server
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    debug_mode: bool = Field(default=False, env="DEBUG_MODE")
    
    # JWT - Secure Configuration
    jwt_public_key_path: str = Field(default="./keys/public_key.pem", env="JWT_PUBLIC_KEY_PATH")
    jwt_private_key_path: str = Field(default="./keys/private_key.pem", env="JWT_PRIVATE_KEY_PATH")
    jwt_secret_key: str = Field(default="", env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="RS256", env="JWT_ALGORITHM")
    jwt_clock_drift_seconds: int = Field(default=30, env="JWT_CLOCK_DRIFT_SECONDS")
    jwt_expiration_hours: int = Field(default=1, env="JWT_EXPIRATION_HOURS")
    
    # Database - Secure Configuration
    database_url: str = Field(
        default="",
        env="DATABASE_URL",
        description="CRITICAL: Use environment variable in production"
    )
    db_pool_size: int = Field(default=10, env="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=20, env="DB_MAX_OVERFLOW")
    db_ssl_mode: str = Field(default="prefer", env="DB_SSL_MODE")
    
    # Redis - Secure Configuration
    redis_url: str = Field(default="", env="REDIS_URL")
    redis_max_connections: int = Field(default=50, env="REDIS_MAX_CONNECTIONS")
    redis_ssl: bool = Field(default=False, env="REDIS_SSL")
    
    # Rate Limiting
    rate_limit_requests_per_minute: int = Field(default=100, env="RATE_LIMIT_REQUESTS_PER_MINUTE")
    rate_limit_burst_size: int = Field(default=120, env="RATE_LIMIT_BURST_SIZE")
    
    # Score Provider - Secure Configuration
    score_provider_type: str = Field(default="database", env="SCORE_PROVIDER_TYPE")
    score_api_url: str = Field(default="", env="SCORE_API_URL")
    score_api_key: str = Field(default="", env="SCORE_API_KEY")
    score_cache_ttl_seconds: int = Field(default=300, env="SCORE_CACHE_TTL_SECONDS")
    
    # Telemetry
    telemetry_version: str = Field(default="1.0.0", env="TELEMETRY_VERSION")
    telemetry_emit_enabled: bool = Field(default=True, env="TELEMETRY_EMIT_ENABLED")
    
    # Replay Cache
    replay_cache_purge_interval_seconds: int = Field(default=300, env="REPLAY_CACHE_PURGE_INTERVAL_SECONDS")
    replay_cache_max_size: int = Field(default=1000000, env="REPLAY_CACHE_MAX_SIZE")
    
    @field_validator("jwt_algorithm")
    @classmethod
    def validate_jwt_algorithm(cls, v: str) -> str:
        """Validate JWT algorithm is secure."""
        allowed_algorithms = ["RS256", "RS384", "RS512", "ES256", "ES384", "ES512"]
        if v not in allowed_algorithms:
            raise ValueError(f"JWT algorithm must be one of {allowed_algorithms}")
        return v
    
    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment is one of the allowed values."""
        allowed_envs = ["development", "staging", "production"]
        if v not in allowed_envs:
            raise ValueError(f"Environment must be one of {allowed_envs}")
        return v
    
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"
    
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == "development"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    settings = Settings()
    
    # Security validation for production
    if settings.is_production():
        if not settings.secret_key:
            raise ValueError("SECRET_KEY must be set in production")
        if not settings.database_url:
            raise ValueError("DATABASE_URL must be set in production")
        if not settings.jwt_secret_key and settings.jwt_algorithm.startswith("HS"):
            raise ValueError("JWT_SECRET_KEY must be set for HMAC algorithms in production")
    
    return settings