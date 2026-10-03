import logging
import sys

def setup_logging(app):
    handler = logging.StreamHandler(sys.stdout)
    fmt = logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s")
    handler.setFormatter(fmt)
    app.logger.handlers = [handler]
    app.logger.setLevel(logging.INFO)
    logging.getLogger().setLevel(logging.INFO)
