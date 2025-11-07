FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Используйте переменную $PORT, если она задается платформой (Render/Railway)
ENV PORT=8080

CMD ["uvicorn", "webhook_bot:app", "--host", "0.0.0.0", "--port", "8080"]
