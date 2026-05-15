"""Campaign asset storage — Google Cloud Storage with local fallback."""

from __future__ import annotations

import logging
import uuid
from pathlib import Path

from settings import REPO_ROOT, settings

log = logging.getLogger(__name__)

_LOCAL_UPLOADS = REPO_ROOT / "backend" / "uploads"


def _local_save(data: bytes, *, campaign_id: int, file_name: str, content_type: str) -> str:
    dest_dir = _LOCAL_UPLOADS / str(campaign_id)
    dest_dir.mkdir(parents=True, exist_ok=True)
    safe = "".join(c if c.isalnum() or c in ".-_" else "_" for c in file_name)[:120]
    path = dest_dir / f"{uuid.uuid4().hex[:8]}_{safe}"
    path.write_bytes(data)
    return f"/api/campaigns/{campaign_id}/assets/file/{path.name}"


def _gcs_save(
    data: bytes,
    *,
    campaign_id: int,
    file_name: str,
    content_type: str,
) -> str:
    from google.cloud import storage

    client = storage.Client(project=settings.gcp_project_id)
    bucket = client.bucket(settings.gcs_bucket)
    safe = "".join(c if c.isalnum() or c in ".-_" else "_" for c in file_name)[:120]
    blob_name = f"campaigns/{campaign_id}/{uuid.uuid4().hex}_{safe}"
    blob = bucket.blob(blob_name)
    blob.upload_from_string(data, content_type=content_type)
    return f"https://storage.googleapis.com/{settings.gcs_bucket}/{blob_name}"


async def upload_campaign_asset(
    data: bytes,
    *,
    campaign_id: int,
    file_name: str,
    content_type: str,
) -> str:
    if settings.gcs_bucket:
        try:
            return _gcs_save(
                data,
                campaign_id=campaign_id,
                file_name=file_name,
                content_type=content_type,
            )
        except Exception as exc:
            log.warning("GCS upload failed, using local: %s", exc)
    return _local_save(
        data,
        campaign_id=campaign_id,
        file_name=file_name,
        content_type=content_type,
    )


def resolve_local_asset_path(campaign_id: int, file_name: str) -> Path | None:
    path = _LOCAL_UPLOADS / str(campaign_id) / file_name
    if path.is_file():
        return path
    return None
