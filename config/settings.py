"""
Modular configuration system using Pydantic for type-safe environment management.

Features:
- Environment-based configuration (dev/test/prod)
- Type validation for all settings
- Extensible for custom validators
- Support for environment variable overrides
"""

from typing import Optional
from pydantic import BaseSettings, Field, validator
from enum import Enum


class EnvironmentType(str, Enum):
    """Supported environment types."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class APISettings(BaseSettings):
    """API and server configuration."""

    host: str = Field(default="0.0.0.0", description="Flask host")
    port: int = Field(default=5000, description="Flask port")
    debug: bool = Field(default=False, description="Debug mode")
    reload: bool = Field(default=False, description="Auto-reload on changes")
    log_level: str = Field(default="INFO", description="Logging level")

    class Config:
        env_prefix = "API_"
        case_sensitive = False


class OpenAISettings(BaseSettings):
    """OpenAI API configuration."""

    api_key: str = Field(..., description="OpenAI API key")
    model: str = Field(default="gpt-4", description="Model name")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Temperature parameter")
    max_tokens: int = Field(default=2000, ge=1, description="Max tokens for response")
    timeout: int = Field(default=30, ge=1, description="Request timeout in seconds")

    @validator("api_key")
    def validate_api_key(cls, v):
        """Validate OpenAI API key format."""
        if not v.startswith("sk-"):
            raise ValueError("OpenAI API key must start with 'sk-'")
        return v

    class Config:
        env_prefix = "OPENAI_"
        case_sensitive = False


class DatabaseSettings(BaseSettings):
    """Database configuration."""

    url: str = Field(
        default="sqlite:///chatbot.db",
        description="Database connection URL"
    )
    echo: bool = Field(default=False, description="Log SQL statements")
    pool_size: int = Field(default=10, ge=1, description="Connection pool size")
    max_overflow: int = Field(default=20, ge=0, description="Max overflow connections")

    class Config:
        env_prefix = "DATABASE_"
        case_sensitive = False


class ChatbotSettings(BaseSettings):
    """Chatbot behavior configuration."""

    max_conversation_history: int = Field(
        default=50,
        ge=1,
        description="Maximum conversation history to retain"
    )
    conversation_timeout: int = Field(
        default=3600,
        ge=1,
        description="Conversation timeout in seconds"
    )
    system_prompt: Optional[str] = Field(
        default=None,
        description="System prompt for chatbot behavior"
    )

    class Config:
        env_prefix = "CHATBOT_"
        case_sensitive = False


class ValidationSettings(BaseSettings):
    """LLM response validation configuration."""

    enable_hallucination_detection: bool = Field(
        default=True,
        description="Enable hallucination detection"
    )
    enable_toxicity_check: bool = Field(
        default=True,
        description="Enable toxicity/safety checks"
    )
    enable_consistency_check: bool = Field(
        default=True,
        description="Enable response consistency checking"
    )
    hallucination_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Hallucination confidence threshold"
    )
    toxicity_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Toxicity score threshold"
    )

    class Config:
        env_prefix = "VALIDATION_"
        case_sensitive = False


class TestingSettings(BaseSettings):
    """Testing configuration."""

    use_mock_llm: bool = Field(
        default=False,
        description="Use mock LLM responses instead of real API"
    )
    mock_responses_file: Optional[str] = Field(
        default=None,
        description="Path to mock responses file"
    )

    class Config:
        env_prefix = "TESTING_"
        case_sensitive = False


class PlaywrightSettings(BaseSettings):
    """Playwright E2E testing configuration."""

    headless: bool = Field(default=True, description="Run browser in headless mode")
    browser_type: str = Field(default="chromium", description="Browser type (chromium, firefox, webkit)")
    timeout: int = Field(default=30000, description="Browser timeout in ms")
    screenshots_dir: Optional[str] = Field(
        default=None,
        description="Directory for test screenshots"
    )
    videos_dir: Optional[str] = Field(
        default=None,
        description="Directory for test videos"
    )
    base_url: str = Field(default="http://localhost:5000", description="Base URL for E2E tests")

    class Config:
        env_prefix = "PLAYWRIGHT_"
        case_sensitive = False


class Settings(BaseSettings):
    """Main settings class combining all configuration domains."""

    environment: EnvironmentType = Field(default=EnvironmentType.DEVELOPMENT)

    api: APISettings = Field(default_factory=APISettings)
    openai: OpenAISettings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    chatbot: ChatbotSettings = Field(default_factory=ChatbotSettings)
    validation: ValidationSettings = Field(default_factory=ValidationSettings)
    testing: TestingSettings = Field(default_factory=TestingSettings)
    playwright: PlaywrightSettings = Field(default_factory=PlaywrightSettings)

    @validator("api", "database", "chatbot", "validation", "testing", "playwright", pre=True, always=True)
    def set_defaults(cls, v, field):
        if v is None:
            return field.default_factory()
        return v

    @property
    def is_development(self) -> bool:
        return self.environment == EnvironmentType.DEVELOPMENT

    @property
    def is_testing(self) -> bool:
        return self.environment == EnvironmentType.TESTING

    @property
    def is_production(self) -> bool:
        return self.environment == EnvironmentType.PRODUCTION

    class Config:
        env_nested_delimiter = "__"
        case_sensitive = False

        @classmethod
        def customise_sources(
            cls,
            init_settings,
            env_settings,
            file_settings,
            settings_cls,
        ):
            return (
                env_settings,
                init_settings,
                file_settings,
            )


def get_settings() -> Settings:
    try:
        return Settings()
    except Exception as e:
        raise ValueError(f"Failed to load settings: {str(e)}") from e


_settings = None


def get_settings_cached() -> Settings:
    global _settings
    if _settings is None:
        _settings = get_settings()
    return _settings
