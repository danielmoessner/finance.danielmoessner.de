from .base import *

# Secret Settings

DEBUG = False

ALLOWED_HOSTS = get_secret("ALLOWED_HOSTS")


# Logging

LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "handlers": {
        "warning": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "filename": os.path.join(BASE_DIR, "tmp/logs/django.log"),
        },
        "task": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": os.path.join(BASE_DIR, "tmp/logs/task.log"),
        },
    },
    "loggers": {
        "django": {
            "handlers": ["warning"],
            "level": "INFO",
            "propagate": True,
        },
        "background_tasks": {
            "handlers": ["task"],
            "level": "INFO",
            "propagate": True,
        },
    },
}
