from .base import *

# Secret Settings

DEBUG = False

ALLOWED_HOSTS = get_secret("ALLOWED_HOSTS")


# Logging

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "info": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": os.path.join(BASE_DIR, "tmp/logs/django.log"),
        },
        # "warning": {
        #     "level": "WARNING",
        #     "class": "logging.FileHandler",
        #     "filename": os.path.join(BASE_DIR, "tmp/logs/django.log"),
        # },
    },
    "loggers": {
        "django": {
            "handlers": ["info"],
            "level": "INFO",
            "propagate": True,
        }
    },
}
