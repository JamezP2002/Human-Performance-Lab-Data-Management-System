FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

# System deps (add libpoppler, ghostscript, etc., if your PDFs need them)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd -m appuser

# Copy your code
COPY . .

# Streamlit runtime settings
ENV STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
# Optional: Streamlit config baked into container
RUN mkdir -p /home/appuser/.streamlit && chown -R appuser /home/appuser/.streamlit
USER appuser
EXPOSE 8501

# ✅ Entry point
CMD ["streamlit", "run", "app/streamlit_app.py", "--server.port=8501", "--server.headless=true"]
