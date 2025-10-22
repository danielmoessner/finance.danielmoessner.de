from .base import *

DEBUG = True

INSTALLED_APPS += [
    "debug_toolbar",
]

MIDDLEWARE += [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

INTERNAL_IPS = [
    "127.0.0.1",
]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "info": {
            "level": "INFO",
            "class": "logging.StreamHandler",
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
