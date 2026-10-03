import firebase_admin
from firebase_admin import credentials, firestore
from ..config import Config
import logging

logger = logging.getLogger(__name__)
_db = None

def init_firebase():
    global _db
    if _db is not None:
        return _db
    try:
        cred = credentials.Certificate({
            "type": "service_account",
            "project_id": Config.FIREBASE_PROJECT_ID,
            "private_key_id": Config.FIREBASE_PRIVATE_KEY_ID,
            "private_key": Config.FIREBASE_PRIVATE_KEY,
            "client_email": Config.FIREBASE_CLIENT_EMAIL,
            "client_id": Config.FIREBASE_CLIENT_ID,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": Config.FIREBASE_CLIENT_CERT_URL,
        })
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
        _db = firestore.client()
        logger.info("Firebase initialized")
        return _db
    except Exception as e:
        logger.error(f"Firebase init failed: {e}")
        raise

def get_db():
    global _db
    if _db is None:
        return init_firebase()
    return _db
