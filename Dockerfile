FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY results ./results
COPY scripts/init_and_run.sh /app/scripts/init_and_run.sh
RUN chmod +x /app/scripts/init_and_run.sh

RUN mkdir -p /app/chunks

EXPOSE 8000

ENTRYPOINT ["/app/scripts/init_and_run.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
