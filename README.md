# Control-system-Agent

FastAPI + LangGraph агент для вопросов по системам управления (CLS Ogata, Discrete Ogata, Nonlinear Khalil) с retrieval через Qdrant и эмбеддингами Ollama.

## Быстрый старт

```bash
docker-compose up --build ingest   # прогоняем ingestion из results/recognition_json
docker-compose up --build app      # или просто docker-compose up
```

Сервисы: `ollama`, `qdrant`, `redis`, `app` (FastAPI), `ingest` (разовый прогон). По умолчанию Ollama тянет `qwen3:8b` и `embeddinggemma` (эмбеддинг).

API:
- `GET /health` — liveness
- `POST /v1/ask` — тело: `{"question": "..."}`. Возвращает `answer`, `citations`, `theory`.

Входные JSON: `results/recognition_json/*.json`. Текстовые чанки сохраняются в `chunks/`, ключи для поиска — в Redis, сами вектора — в Qdrant (3 коллекции).
