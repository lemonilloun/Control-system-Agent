from langchain_ollama import ChatOllama, OllamaEmbeddings

from app.config import settings


def get_llm():
    return ChatOllama(
        base_url=settings.OLLAMA_BASE_URL,
        model=settings.OLLAMA_MODEL_NAME,
        temperature=0.2,
    )


def get_embedding_model():
    return OllamaEmbeddings(
        base_url=settings.OLLAMA_BASE_URL,
        model=settings.OLLAMA_EMBED_MODEL_NAME,
    )
