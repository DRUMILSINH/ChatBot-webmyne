"""
Django settings for chatbot_ui project.
"""

import json
import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_list(name: str, default: str) -> list[str]:
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


def _env_json(name: str, default):
    raw = os.getenv(name)
    if not raw:
        return default
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return default


SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "django-insecure-local-dev-only")
DEBUG = _env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = _env_list("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost,*")
CSRF_TRUSTED_ORIGINS = _env_list("DJANGO_CSRF_TRUSTED_ORIGINS", "")

API_V2_PREFIX = os.getenv("API_V2_PREFIX", "api/v2")
ENABLE_LEGACY_CHAT_ROUTES = _env_bool("ENABLE_LEGACY_CHAT_ROUTES", False)
ENABLE_INGESTION_API = _env_bool("ENABLE_INGESTION_API", False)

FRONTEND_DEV_ORIGIN = os.getenv("FRONTEND_DEV_ORIGIN", "http://127.0.0.1:5173").rstrip("/")
if DEBUG and FRONTEND_DEV_ORIGIN and FRONTEND_DEV_ORIGIN not in CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS.append(FRONTEND_DEV_ORIGIN)

CHROMA_PERSIST_ROOT = os.getenv("CHROMA_PERSIST_ROOT", str(BASE_DIR / "db"))
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "chat",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "chat.middleware.TraceIdMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "chatbot_ui.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "chatbot_ui.wsgi.application"


def _build_db_config(
    *,
    engine: str,
    sqlite_name: Path,
    name: str,
    user: str,
    password: str,
    host: str,
    port: str,
) -> dict:
    if engine == "django.db.backends.sqlite3":
        return {"ENGINE": engine, "NAME": sqlite_name}
    return {
        "ENGINE": engine,
        "NAME": name,
        "USER": user,
        "PASSWORD": password,
        "HOST": host,
        "PORT": port,
    }


default_db_engine = os.getenv("DEFAULT_DB_ENGINE", "django.db.backends.sqlite3")
default_db = _build_db_config(
    engine=default_db_engine,
    sqlite_name=BASE_DIR / "db.sqlite3",
    name=os.getenv("DEFAULT_DB_NAME", "chatbot_db"),
    user=os.getenv("DEFAULT_DB_USER", "openpg"),
    password=os.getenv("DEFAULT_DB_PASSWORD", "openpgpwd"),
    host=os.getenv("DEFAULT_DB_HOST", "localhost"),
    port=os.getenv("DEFAULT_DB_PORT", "5432"),
)

logs_db_engine = os.getenv("LOGS_DB_ENGINE", default_db_engine)
logs_db = _build_db_config(
    engine=logs_db_engine,
    sqlite_name=BASE_DIR / "logs.sqlite3",
    name=os.getenv("LOGS_DB_NAME", os.getenv("DEFAULT_DB_NAME", "chatbot_db")),
    user=os.getenv("LOGS_DB_USER", os.getenv("DEFAULT_DB_USER", "openpg")),
    password=os.getenv("LOGS_DB_PASSWORD", os.getenv("DEFAULT_DB_PASSWORD", "openpgpwd")),
    host=os.getenv("LOGS_DB_HOST", os.getenv("DEFAULT_DB_HOST", "localhost")),
    port=os.getenv("LOGS_DB_PORT", os.getenv("DEFAULT_DB_PORT", "5432")),
)

DATABASES = {
    "default": default_db,
    "logs": logs_db,
}

DATABASE_ROUTERS = ["chat.db_routers.LogRouter"]


AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


LANGUAGE_CODE = "en-us"
TIME_ZONE = os.getenv("DJANGO_TIME_ZONE", "UTC")
USE_I18N = True
USE_TZ = True

SESSION_COOKIE_AGE = int(os.getenv("SESSION_COOKIE_AGE", "3600"))
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = os.getenv("CSRF_COOKIE_SAMESITE", "Lax")

if not DEBUG:
    SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "3600"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = _env_bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", True)
    SECURE_HSTS_PRELOAD = _env_bool("SECURE_HSTS_PRELOAD", False)
    SECURE_SSL_REDIRECT = _env_bool("SECURE_SSL_REDIRECT", True)
    SESSION_COOKIE_SECURE = _env_bool("SESSION_COOKIE_SECURE", True)
    CSRF_COOKIE_SECURE = _env_bool("CSRF_COOKIE_SECURE", True)
else:
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False


STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "chatbot-local-cache",
    }
}


# --- Production upgrade feature flags / policy ---
ENFORCE_RBAC = _env_bool("ENFORCE_RBAC", False)
SAFE_BLOCK_MESSAGE = os.getenv(
    "SAFE_BLOCK_MESSAGE",
    "I cannot help with that request because it violates data safety policy.",
)

CRAWL_DOMAIN_ALLOWLIST = _env_json("CRAWL_DOMAIN_ALLOWLIST", {})
CRAWL_MAX_PAGES = int(os.getenv("CRAWL_MAX_PAGES", "20"))
CRAWL_VALIDATE_REDIRECTS = _env_bool("CRAWL_VALIDATE_REDIRECTS", True)
CRAWL_REQUIRE_ALLOWLIST = _env_bool("CRAWL_REQUIRE_ALLOWLIST", False)
MAX_JOBS_PER_USER = int(os.getenv("MAX_JOBS_PER_USER", "5"))
MAX_QUEUE_SIZE = int(os.getenv("MAX_QUEUE_SIZE", "100"))
MAX_PARALLEL_CRAWL_WORKERS = int(os.getenv("MAX_PARALLEL_CRAWL_WORKERS", "4"))

RAG_DENSE_K = int(os.getenv("RAG_DENSE_K", "30"))
RAG_BM25_K = int(os.getenv("RAG_BM25_K", "30"))
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "8"))
RAG_MIN_TOP_K = int(os.getenv("RAG_MIN_TOP_K", "4"))
RAG_MAX_CONTEXT_CHARS = int(os.getenv("RAG_MAX_CONTEXT_CHARS", "9000"))
RERANKER_MODEL = os.getenv("RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
ENABLE_RERANKER = _env_bool("ENABLE_RERANKER", False)
RAG_LATENCY_KILL_SWITCH_MS = int(os.getenv("RAG_LATENCY_KILL_SWITCH_MS", "1500"))
RAG_ADAPTIVE_DISABLE_TTL_SEC = int(os.getenv("RAG_ADAPTIVE_DISABLE_TTL_SEC", "60"))
MIN_CONFIDENCE_TO_ANSWER = float(os.getenv("MIN_CONFIDENCE_TO_ANSWER", "0.25"))
ENABLE_QUERY_CACHE = _env_bool("ENABLE_QUERY_CACHE", True)
QUERY_CACHE_TTL_SEC = int(os.getenv("QUERY_CACHE_TTL_SEC", "120"))
ENABLE_RETRIEVAL_CACHE = _env_bool("ENABLE_RETRIEVAL_CACHE", True)
RETRIEVAL_CACHE_TTL_SEC = int(os.getenv("RETRIEVAL_CACHE_TTL_SEC", "60"))
SSE_REQUIRE_ASGI = _env_bool("SSE_REQUIRE_ASGI", True)
MAX_CONCURRENT_STREAMS = int(os.getenv("MAX_CONCURRENT_STREAMS", "50"))
HIGH_LOAD_STREAM_THRESHOLD = int(os.getenv("HIGH_LOAD_STREAM_THRESHOLD", "20"))
HIGH_LOAD_QUEUE_THRESHOLD = int(os.getenv("HIGH_LOAD_QUEUE_THRESHOLD", "40"))
ENABLE_COLD_START_PRELOAD = _env_bool("ENABLE_COLD_START_PRELOAD", False)
PRELOAD_VECTOR_IDS = _env_list("PRELOAD_VECTOR_IDS", "")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")
OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434"),
)


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
        },
        "json": {
            "()": "chat.logging_utils.JsonLogFormatter",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json" if _env_bool("LOG_AS_JSON", True) else "standard",
        }
    },
    "loggers": {
        "chat.observability": {
            "handlers": ["console"],
            "level": os.getenv("CHAT_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
    },
}
