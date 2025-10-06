from config.path_config import RAW_DIR
from src.logger import get_logger
from src.custom_exception import CustomException
import os
import pandas as pd

logger = get_logger(__name__)

def load_all_raw_files():
    try:
        files = [f for f in os.listdir(RAW_DIR) if f.endswith(('.csv', '.txt'))]
        docs = []
        for file in files:
            path = os.path.join(RAW_DIR, file)
            if file.endswith(".csv"):
                df = pd.read_csv(path)
                logger.info(f"Loaded CSV: {file} rows={len(df)}")
                text = df.to_string()
            else:
                with open(path, "r", encoding="utf-8") as f:
                    text = f.read()
            docs.append((file, text))
        return docs
    except Exception as e:
        logger.error(f"Error loading raw files: {e}")
        raise CustomException("Error while loading raw files", e)
