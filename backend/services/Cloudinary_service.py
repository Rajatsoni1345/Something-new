import cloudinary
import cloudinary.uploader
from ..config import Config
import logging

logger = logging.getLogger(__name__)

cloudinary.config(
    cloud_name=Config.CLOUDINARY_CLOUD_NAME,
    api_key=Config.CLOUDINARY_API_KEY,
    api_secret=Config.CLOUDINARY_API_SECRET,
    secure=True
)

def upload_video(file_obj, session_id, recording_type):
    public_id = f"birthday-quest/sessions/{session_id}/{recording_type}/{recording_type}"
    try:
        result = cloudinary.uploader.upload_large(
            file_obj,
            resource_type="video",
            public_id=public_id,
            overwrite=False,
            unique_filename=True,
            use_filename=False,
            invalidate=True,
        )
        return {
            "public_id": result.get("public_id"),
            "secure_url": result.get("secure_url"),
            "resource_type": result.get("resource_type"),
            "duration": result.get("duration"),
            "size": result.get("bytes"),
            "format": result.get("format"),
            "uploaded_at": result.get("created_at"),
        }
    except Exception as e:
        logger.error(f"Cloudinary upload failed: {e}")
        raise

def delete_video(public_id):
    try:
        cloudinary.uploader.destroy(public_id, resource_type="video")
        return True
    except Exception as e:
        logger.error(f"Cloudinary delete failed: {e}")
        return False
