import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    FLASK_ENV = os.getenv("FLASK_ENV", "production")
    SECRET_KEY = os.getenv("SECRET_KEY")
    
    FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID")
    FIREBASE_PRIVATE_KEY_ID = os.getenv("FIREBASE_PRIVATE_KEY_ID")
    FIREBASE_PRIVATE_KEY = os.getenv("FIREBASE_PRIVATE_KEY", "").replace("\\n", "\n")
    FIREBASE_CLIENT_EMAIL = os.getenv("FIREBASE_CLIENT_EMAIL")
    FIREBASE_CLIENT_ID = os.getenv("FIREBASE_CLIENT_ID")
    FIREBASE_CLIENT_CERT_URL = os.getenv("FIREBASE_CLIENT_CERT_URL")
    
    CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")
    
    FRONTEND_URL = os.getenv("FRONTEND_URL", "*")
    ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "change-me")
    MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE_MB", "50")) * 1024 * 1024
    
    @staticmethod
    def validate():
        required = [
            "SECRET_KEY", "FIREBASE_PROJECT_ID", "FIREBASE_PRIVATE_KEY",
            "FIREBASE_CLIENT_EMAIL", "CLOUDINARY_CLOUD_NAME",
            "CLOUDINARY_API_KEY", "CLOUDINARY_API_SECRET"
        ]
        missing = [k for k in required if not getattr(Config, k)]
        if missing:
            raise RuntimeError(f"Missing env vars: {missing}")
