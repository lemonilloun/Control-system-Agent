# Control-system-Agent

FastAPI + LangGraph агент для ответов по системам управления (CLS Ogata, Discrete Ogata, Nonlinear Khalil) с поиском по Qdrant и эмбеддингами Ollama.

## 1. Подготовка данных (`/results`)

В репо ожидается структура:
```
results/
  recognition_json/
    CLS-Ogata-10-40.json
    DС-Ogata-13-40.json
    NL-Khalil-11-40.json
  markdown/
    CLS-Ogata-10-40.md
    DС-Ogata-13-40.md
    NL-Khalil-11-40.md
```

Если у вас те же файлы, просто скопируйте их в `results/recognition_json` и `results/markdown` (как у меня). Если файлов нет:
- Прогоните ваши PDF через Dolphin-OCR (или другой OCR), чтобы получить `.json` с разметкой страниц и элементов; сохраните в `results/recognition_json`.
- Markdown-версии нужны только для чтения вручную, на работу агента не влияют.

Входные JSON — единственный источник для инжеста в Qdrant. Чанки сохраняются в `chunks/`, путевики — в Redis, вектора — в Qdrant (3 коллекции).

## 2. Запуск

```bash
docker-compose up --build ingest   # один раз: создаёт коллекции, пишет чанки/Redis
docker-compose up --build          # поднимает API + все сервисы
```

Сервисы: `ollama`, `qdrant`, `redis`, `app` (FastAPI), `ingest` (одноразовый прогон). По умолчанию тянутся модели Ollama: `qwen3:8b` и `embeddinggemma`.

## 3. API

- `GET /health` — проверка живости
- `POST /v1/ask` — тело: `{"question": "..."}` → ответ: `answer`, `citations`, `theory`.

## 4. Быстрый тест

В репо есть `scripts/test_agent_api.py`. Примеры вопросов уже зашиты:

```bash
python scripts/test_agent_api.py            # все кейсы
python scripts/test_agent_api.py --case ds_signals
```

URL можно переопределить переменной `AGENT_URL` (по умолчанию `http://localhost:8000/v1/ask`).

## 5. Примечания

- Перед первым запуском убедитесь, что в `results/recognition_json` лежат ваши JSON (или мои образцы выше).
- Если меняете модели Ollama, поправьте переменные окружения `OLLAMA_MODEL_NAME` / `OLLAMA_EMBED_MODEL_NAME` в `docker-compose.yml`.
