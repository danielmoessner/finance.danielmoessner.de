from .base import *

DEBUG = False

ALLOWED_HOSTS = get_secret("ALLOWED_HOSTS")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "info": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": os.path.join(BASE_DIR, "tmp/django.log"),
        },
    },
    "loggers": {
        "django": {
            "handlers": ["info"],
            "level": "INFO",
            "propagate": True,
        },
        "": {
            "handlers": ["info"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
