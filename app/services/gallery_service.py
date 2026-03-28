"""
Handles gallery CRUD: saving images to Supabase Storage, saving metadata to DB,
fetching user galleries, and deleting items.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from urllib.parse import urlparse
from app.database import get_service_client
from app.config import settings

logger = logging.getLogger(__name__)


def upload_image(image_bytes: bytes, user_id: str, filename: str | None = None) -> str:
    """
    Uploads image bytes to Supabase Storage.

    Returns:
        Public URL of the uploaded image.
    """
    client = get_service_client()
    if not filename:
        filename = f"{uuid.uuid4()}.png"

    storage_path = f"{user_id}/{filename}"

    client.storage.from_(settings.supabase_bucket).upload(
        path=storage_path,
        file=image_bytes,
        file_options={"content-type": "image/png", "upsert": "true"},
    )

    public_url = client.storage.from_(settings.supabase_bucket).get_public_url(storage_path)
    return public_url


def save_gallery_item(
    user_id: str,
    prompt: str,
    image_url: str,
    enhanced_prompt: str | None = None,
    style_preset: str = "akbari",
    model_used: str = "imagen-4",
    source_type: str = "generate",
    parent_id: str | None = None,
) -> dict:
    """
    Saves a gallery item record to the Supabase DB galleries table.

    Returns:
        The inserted row as a dict.
    """
    client = get_service_client()
    payload = {
        "user_id": user_id,
        "prompt": prompt,
        "enhanced_prompt": enhanced_prompt,
        "image_url": image_url,
        "style_preset": style_preset,
        "model_used": model_used,
        "source_type": source_type,
        "created_at": datetime.utcnow().isoformat(),
    }
    if parent_id:
        payload["parent_id"] = parent_id
    response = client.table("galleries").insert(payload).execute()
    return response.data[0] if response.data else payload


def get_user_gallery(user_id: str, limit: int = 50) -> list[dict]:
    """
    Fetches all gallery items for a user, newest first.

    Returns:
        List of gallery item dicts.
    """
    client = get_service_client()
    response = (
        client.table("galleries")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return response.data or []


def delete_gallery_item(item_id: str, user_id: str) -> bool:
    """
    Deletes a gallery item and its image from Storage. Validates user ownership.

    Returns:
        True if deleted successfully.
    """
    client = get_service_client()

    # Fetch item to get image_url and verify ownership
    response = (
        client.table("galleries")
        .select("image_url, user_id")
        .eq("id", item_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not response.data:
        logger.warning(f"Delete failed: item {item_id} not found or not owned by user {user_id}")
        return False

    item = response.data[0]

    # Delete from DB
    client.table("galleries").delete().eq("id", item_id).execute()

    # Delete from Storage — extract path from URL, stripping any query params
    try:
        image_url: str = item["image_url"]
        # Parse URL to remove query string (e.g. trailing ?t=... cache-busters)
        parsed = urlparse(image_url)
        path_only = parsed.path  # strips query string and fragment
        # URL path format: .../storage/v1/object/public/{bucket}/{user_id}/{filename}
        bucket_prefix = f"/object/public/{settings.supabase_bucket}/"
        if bucket_prefix in path_only:
            storage_path = path_only.split(bucket_prefix)[-1]
            client.storage.from_(settings.supabase_bucket).remove([storage_path])
    except Exception as e:
        logger.warning(f"Storage delete failed for item {item_id} (non-critical): {e}")

    return True
