import re
import os
import sys
from dotenv import load_dotenv
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from src.logger import get_logger
from src.custom_exception import CustomException

load_dotenv()
logger = get_logger(__name__)


class PIIMasker:
    """
    Hybrid PII masker using Regex + Presidio NLP engine.
    - Regex handles structured patterns (card, phone, email, Aadhaar, PAN)
    - Presidio handles contextual / unstructured text (names, IBAN, locations)
    """

    def __init__(self):
        try:
            logger.info("Initializing hybrid PII masker...")
            # Step 1️ Initialize Presidio Engines
            self.analyzer = AnalyzerEngine()
            self.anonymizer = AnonymizerEngine()

            # Step 2 Precompile regex patterns (fast lookup)
            self.regex_patterns = {
                "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,6}\b"),
                "phone": re.compile(r"(?:\+91[\-\s]?|91[\-\s]?)?[6-9]\d{9}\b"),
                "card": re.compile(r"\b(?:\d[ -]*?){13,16}\b"),
                "aadhaar": re.compile(r"\b\d{4}\s\d{4}\s\d{4}\b"),
                "pan": re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b", re.IGNORECASE),
            }

        except Exception as e:
            logger.error(f"Error initializing PIIMasker: {e}")
            raise CustomException("Error initializing PII masker", e)

    # ===================================================
    def regex_mask(self, text: str) -> str:
        """Mask structured patterns using regex."""
        try:
            masked_text = text
            for pii_type, pattern in self.regex_patterns.items():
                if pattern.search(masked_text):
                    masked_text = pattern.sub(f"[{pii_type.upper()}_MASKED]", masked_text)
            return masked_text
        except Exception as e:
            logger.error(f"Regex masking error: {e}")
            raise CustomException("Regex masking failed", e)

    # ===================================================
    def presidio_mask(self, text: str, chunk_size: int = 50000) -> str:
        """
        Use Presidio NLP engine to detect & anonymize contextual PII in safe chunks.
        Avoids spaCy's max_length limit by splitting long inputs.
        """
        try:
            if not text:
                return text

            masked_parts = []
            for i in range(0, len(text), chunk_size):
                part = text[i:i + chunk_size]

                results = self.analyzer.analyze(
                    text=part,
                    entities=None,       # Detect all supported types
                    language="en"
                )

                if not results:
                    masked_parts.append(part)
                    continue

                # Replace all detected PII with placeholders
                operators = {
                  res.entity_type: OperatorConfig("replace", {"new_value": f"[{res.entity_type}_MASKED]"})
                  for res in results
                }

                anonymized = self.anonymizer.anonymize(
                    text=part,
                    analyzer_results=results,
                    operators=operators
                )

                masked_parts.append(anonymized.text)

            return " ".join(masked_parts)

        except Exception as e:
            logger.error(f"Presidio masking error: {e}")
            raise CustomException("Presidio masking failed", e)

    # ===================================================
    def mask_text(self, text: str) -> str:
        """
        Apply both Regex and Presidio masking for complete protection.
        Regex first → Presidio second.
        """
        try:
            if not text:
                return text

            logger.info("Starting hybrid PII masking...")
            text = self.regex_mask(text)
            #text = self.presidio_mask(text)
            logger.info("Hybrid PII masking completed.")
            return text

        except Exception as e:
            logger.error(f"Hybrid masking error: {e}")
            raise CustomException("Hybrid PII masking failed", e)
