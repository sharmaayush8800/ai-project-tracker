FROM python:3.12-slim

WORKDIR /app

# Install dependencies first (cache layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (includes static/index.html)
COPY . .

# Ensure runtime directories exist
RUN mkdir -p uploads chroma_db static

EXPOSE 8000

# UI served at /  |  API at /api/v1  |  Docs at /docs
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
