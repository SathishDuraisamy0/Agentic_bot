import logging
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

LOG_FILE= os.path.join(LOGS_DIR,f"log_{datetime.now().strftime('%Y-%m-%d')}.log")

logging.basicConfig(

filename=LOG_FILE,
format= '%(asctime)s-%(levelname)s-%(message)s',
level=logging.INFO
)

def get_logger(name):
    logger=logging.getLogger(name)
    logger.setLevel(logging.INFO)
    return logger