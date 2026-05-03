from .base import *

DEBUG = False

ALLOWED_HOSTS = get_secret("ALLOWED_HOSTS")

def _normalize_allowed_hosts(value):
    if isinstance(value, str):
        return [h.strip() for h in value.split(",") if h.strip()]
    try:
        return [str(h).strip() for h in value if str(h).strip()]
    except TypeError:
        return [str(value).strip()] if str(value).strip() else []


_hosts = _normalize_allowed_hosts(ALLOWED_HOSTS)

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

CSRF_TRUSTED_ORIGINS = [f"https://{h}" for h in _hosts if h and h != "*"]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "custom": {
            "format": "%(asctime)s: %(message)s",
            "datefmt": "%d.%m.%Y %H:%M",
        },
    },
    "handlers": {
        "info": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": os.path.join(BASE_DIR, "tmp/django.log"),
            "formatter": "custom",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["info"],
            "level": "INFO",
            "propagate": True,
        },
        "django.request": {
            "handlers": ["info"],
            "level": "ERROR",
            "propagate": False,
        },
        "": {
            "handlers": ["info"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
