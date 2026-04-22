from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional

# Google API scopes
CALENDAR_SCOPE = 'https://www.googleapis.com/auth/calendar'
GMAIL_SCOPE = 'https://www.googleapis.com/auth/gmail.readonly'
SCOPES = [CALENDAR_SCOPE, GMAIL_SCOPE]

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # OpenRouter
    openrouter_api_key: Optional[str] = Field(None, env="OPENROUTER_API_KEY")
    openrouter_model: str = Field("meta-llama/llama-3.1-70b-instruct", env="OPENROUTER_MODEL")
    openrouter_base_url: str = Field("https://openrouter.ai/api/v1", env="OPENROUTER_BASE_URL")

    # App
    app_api_key: Optional[str] = Field(None, env="APP_API_KEY")
    remote_data_analyst_url: Optional[str] = Field(None, env="REMOTE_DATA_ANALYST_URL")

    # Google OAuth (Calendar & Gmail)
    google_client_id: Optional[str] = Field(None, env="GOOGLE_CLIENT_ID")
    google_client_secret: Optional[str] = Field(None, env="GOOGLE_CLIENT_SECRET")
    google_refresh_token: Optional[str] = Field(None, env="GOOGLE_REFRESH_TOKEN")
    google_access_token: Optional[str] = Field(None, env="GOOGLE_ACCESS_TOKEN")
    google_token_expiry: Optional[str] = Field(None, env="GOOGLE_TOKEN_EXPIRY")
    calendar_timezone: str = Field("UTC", env="CALENDAR_TIMEZONE")
