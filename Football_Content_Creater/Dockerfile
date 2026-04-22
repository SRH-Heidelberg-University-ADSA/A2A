# 1. Base Image
FROM python:3.11-slim

# 2. Set working directory
WORKDIR /app

# 3. Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy the rest of the code
COPY . .

# 5. Expose the port (Render needs to know this)
EXPOSE 8000

# 6. Start the app on port 8000
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]