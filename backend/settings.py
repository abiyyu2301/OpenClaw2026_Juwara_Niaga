"""Settings loaded from .env. Single source of truth for env vars."""

from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


REPO_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(REPO_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        protected_namespaces=(),  # allow "model_*" field names without warnings
    )

    # --- GCP ---
    gcp_project_id: str = "niaga-496405"
    gcp_location: str = "us-central1"
    google_application_credentials: str = "./credentials/niaga-backend-key.json"

    # --- Per-agent model selection ---
    model_prospector: str = "gemini-2.5-flash"
    model_bull: str = "gemini-2.5-flash"
    model_bear: str = "gemini-2.5-flash"
    model_judge: str = "gemini-2.5-pro"
    model_outreach: str = "gemini-2.5-pro"
    model_reply: str = "gemini-2.5-flash"
    model_closer: str = "gemini-2.5-pro"
    model_aftercare: str = "gemini-2.5-flash"

    # --- Cost safety ---
    max_leads_per_run: int = 3
    agent_call_timeout_seconds: int = 90
    run_cost_cap_usd: float = 5.00

    # --- Email ---
    gmail_address: str = ""
    gmail_app_password: str = ""
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    imap_host: str = "imap.gmail.com"
    imap_port: int = 993
    imap_poll_interval_seconds: int = 15

    # --- DOKU ---
    payment_provider: str = "mock"
    doku_client_id: str = ""
    doku_secret_key: str = ""
    doku_webhook_secret: str = ""
    doku_base_url: str = "https://api-sandbox.doku.com"

    # --- Web search ---
    serper_api_key: str = ""

    # --- Backend ---
    database_url: str = "sqlite:///./backend/niaga.db"
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    cors_origins_raw: str = "http://localhost:5173,http://localhost:3000"
    log_level: str = "INFO"

    # --- Deployment ---
    public_base_url: str = ""

    # --- GCS asset storage ---
    gcs_bucket: str = ""  # e.g. niaga-496405-assets

    # --- Google Maps (frontend Places; optional backend geocode later) ---
    google_maps_api_key: str = ""

    @property
    def cors_origins(self) -> List[str]:
        return [o.strip() for o in self.cors_origins_raw.split(",") if o.strip()]


settings = Settings()
