FROM python:3.11-slim

WORKDIR /app

# 1. Install system tools (Needed for building some AI libraries)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 2. MASTER INSTALL: Every single dependency
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    pydantic \
    streamlit \
    requests \
    python-dotenv \
    langchain \
    langchain-openai \
    langchain-community \
    langchain-huggingface \
    langchain-chroma \
    langchain-tavily \
    sentence-transformers \
    chromadb \
    torch \
    numpy \
    pandas \
    pypdf \
    beautifulsoup4

# --- NEW: ADDED FOR LOCAL MODEL & OFFLINE MODE ---
# 3. Copy the local model folder specifically first
COPY my_model /app/my_model

# 4. Force Hugging Face and Transformers to stay OFFLINE
ENV TRANSFORMERS_OFFLINE=1
ENV HF_HUB_OFFLINE=1
# ------------------------------------------------

# 5. Copy the rest of your project code
COPY . .

# 6. Set permissions for the startup script
RUN chmod +x /app/run.sh

EXPOSE 8080

CMD ["sh", "-c", "uvicorn Fast_api:app --host 0.0.0.0 --port ${PORT:-8080}"]