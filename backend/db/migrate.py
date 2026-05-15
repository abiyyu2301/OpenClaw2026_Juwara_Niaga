"""Lightweight SQLite column migration — add new columns if missing."""

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


_CAMPAIGN_COLUMNS = {
    "sales_target_revenue": "INTEGER",
    "geo_place_name": "VARCHAR(300)",
    "geo_lat": "FLOAT",
    "geo_lng": "FLOAT",
    "geo_radius_km": "INTEGER",
    "rep_name": "VARCHAR(200)",
    "rep_email": "VARCHAR(300)",
    "rep_phone": "VARCHAR(50)",
    "rep_title": "VARCHAR(200)",
    "sales_voice": "TEXT",
    "sales_voice_samples": "TEXT",
    "promo_asset_url": "VARCHAR(1000)",
    "promo_asset_type": "VARCHAR(20)",
}


def migrate(engine: Engine) -> None:
    insp = inspect(engine)
    if not insp.has_table("campaigns"):
        return
    existing = {c["name"] for c in insp.get_columns("campaigns")}
    with engine.begin() as conn:
        for col, sql_type in _CAMPAIGN_COLUMNS.items():
            if col not in existing:
                conn.execute(text(f"ALTER TABLE campaigns ADD COLUMN {col} {sql_type}"))


def ensure_campaign_assets_table(engine: Engine) -> None:
    from db.models import CampaignAsset  # noqa: F401
    from db.session import Base

    Base.metadata.create_all(bind=engine, tables=[CampaignAsset.__table__])
