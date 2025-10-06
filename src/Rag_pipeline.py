import os
import pandas as pd
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from src.logger import get_logger
from src.custom_exception import CustomException
from dotenv import load_dotenv
from langchain_community.embeddings import HuggingFaceEmbeddings

logger = get_logger(__name__)
load_dotenv()

# Paths
FINAL_DATA = os.path.join("artifacts", "FINAL_DATA")
VECTOR_DB_DIR = os.path.join("artifacts", "VECTOR_DB")
os.makedirs(VECTOR_DB_DIR, exist_ok=True)


def load_masked_csvs():
    """Load all masked CSVs from FINAL_DATA as row-wise text."""
    docs = []
    for file in os.listdir(FINAL_DATA):
        if file.endswith(".csv"):
            path = os.path.join(FINAL_DATA, file)
            df = pd.read_csv(path)

            # Convert each row into a string (row-aware retrieval)
            for _, row in df.iterrows():
                row_text = " | ".join([f"{col}: {str(val)}" for col, val in row.items()])
                docs.append(row_text)
    return docs


def build_retriever():
    try:
        logger.info("🚀 Starting RAG pipeline: chunking + embedding + retriever")

        # Step 1: Load masked CSVs
        all_texts = load_masked_csvs()

        # Step 2: Chunk data
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        chunks = []
        for text in all_texts:
            chunks.extend(splitter.split_text(text))

        logger.info(f"Total chunks created: {len(chunks)}")

        # Step 3: Convert chunks into embeddings
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        
        # Step 4: Store in FAISS vector DB
        vectorstore = FAISS.from_texts(chunks, embeddings)

        # Save locally
        vectorstore.save_local(VECTOR_DB_DIR)
        logger.info("✅ Retriever (FAISS) built and saved successfully.")

        return vectorstore.as_retriever()

    except Exception as e:
        logger.error(f"❌ Error in RAG pipeline: {e}")
        raise CustomException("RAG pipeline failed", e)


if __name__ == "__main__":
    retriever = build_retriever()
  
