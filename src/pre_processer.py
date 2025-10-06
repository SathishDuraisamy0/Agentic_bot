import os
import pandas as pd
from src.data_loader import load_all_raw_files
from src.PII_Masker import PIIMasker
from src.logger import get_logger
from src.custom_exception import CustomException

logger = get_logger(__name__)

# Define final output folder
FINAL_DATA = os.path.join("artifacts", "FINAL_DATA")
os.makedirs(FINAL_DATA, exist_ok=True)


def mask_dataframe(df, masker):
    """Apply PII masking to every cell in a DataFrame."""
    masked_df = df.copy()
    for col in masked_df.columns:
        masked_df[col] = masked_df[col].astype(str).apply(lambda x: masker.mask_text(x))
    return masked_df


def create_masked_final_data():
    try:
        logger.info("🚀 Starting PII masking pipeline...")

        # Step 1: Load all raw data
        docs = load_all_raw_files()

        # Step 2: Initialize the PII Masker
        masker = PIIMasker()

        # Step 3: Process each file
        for file_name, raw_text in docs:
            input_path = os.path.join("artifacts", "RAW_DATA", file_name)
            output_path = os.path.join(FINAL_DATA, f"masked_{file_name}")

            if file_name.endswith(".csv"):
                # Mask CSV while keeping structure
                df = pd.read_csv(input_path)
                masked_df = mask_dataframe(df, masker)
                masked_df.to_csv(output_path, index=False)
            else:
                # Mask plain text files
                masked_text = masker.mask_text(raw_text)
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(masked_text)

        logger.info("✅ PII masking pipeline completed. Masked files saved in FINAL_DATA.")

    except Exception as e:
        logger.error(f"❌ Error during masking pipeline: {e}")
        raise CustomException("Error during PII masking pipeline", e)


if __name__ == "__main__":
    create_masked_final_data()
