FROM python:3.12-slim-bookworm

WORKDIR /app

RUN useradd -m -u 1000 appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chown -R appuser:appuser /app

USER appuser

ENV PORT=8080
EXPOSE 8080

CMD ["sh", "-c", "exec uvicorn server:app --host 0.0.0.0 --port ${PORT:-8080}"]
