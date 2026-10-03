from flask_cors import CORS
from .config import Config

cors = CORS()

def init_extensions(app):
    cors.init_app(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "X-Session-Id", "X-Admin-Token"]
        }
    })
