import json
import logging
from logging.handlers import RotatingFileHandler
from backend.config import DATA

class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({'time':self.formatTime(record),'level':record.levelname,
                           'event':record.getMessage()}, ensure_ascii=False)

def configure_logging():
    logger = logging.getLogger('voice_studio')
    if not logger.handlers:
        folder = DATA.parent / 'logs'
        folder.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(folder / 'app.log',maxBytes=2*1024*1024,backupCount=3,encoding='utf-8')
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger
