from flask import Flask, send_from_directory
import os
from .config import Config
from .extensions import init_extensions
from .middleware.logging import setup_logging
from .middleware.errors import register_error_handlers
from .services.firebase_service import init_firebase
from .routes import health, session, quest, recordings, admin

def create_app():
    app = Flask(__name__, static_folder=None)
    app.config.from_object(Config)
    Config.validate()
    
    setup_logging(app)
    init_extensions(app)
    register_error_handlers(app)
    init_firebase()
    
    app.register_blueprint(health.bp)
    app.register_blueprint(session.bp)
    app.register_blueprint(quest.bp)
    app.register_blueprint(recordings.bp)
    app.register_blueprint(admin.bp)
    
    FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
    
    @app.route("/")
    def index():
        return send_from_directory(FRONTEND_DIR, "index.html")
    
    @app.route("/<path:path>")
    def static_files(path):
        full = os.path.join(FRONTEND_DIR, path)
        if os.path.isfile(full):
            return send_from_directory(FRONTEND_DIR, path)
        return send_from_directory(FRONTEND_DIR, "index.html")
    
    return app

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
