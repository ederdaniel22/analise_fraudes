FROM python:3.11-slim
WORKDIR /app

# Dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código + modelo + dados necessários (ver .dockerignore)
COPY . .

# A maioria dos hosts (Render/Railway/Cloud Run) injeta a porta via $PORT
ENV PORT=8000
EXPOSE 8000

# API completa: dashboard, login (JWT) e scoring
CMD ["sh", "-c", "uvicorn src.api:app --host 0.0.0.0 --port ${PORT:-8000}"]
