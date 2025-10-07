FROM python:3.11-slim

# Avoid bytecode and buffering
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

# Install required system packages (for numpy, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy project
COPY . .

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Expose port (Cloud Run uses $PORT automatically)
EXPOSE 8080

# Start FastAPI app
CMD ["uvicorn", "bot:app", "--host", "0.0.0.0", "--port", "8080"]
