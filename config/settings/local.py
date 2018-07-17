from .base import *


# Secret Settings

DEBUG = True

ALLOWED_HOSTS = get_secret("ALLOWED_HOSTS")


# Application Definition

INSTALLED_APPS += ['debug_toolbar', ]

MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware', ]


# Other

INTERNAL_IPS = ["127.0.0.1", ]


# Logging

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'handlers': {
        'task': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/task.log'),
        }
    },
    'loggers': {
        'django': {
            'handlers': [],
            'level': 'INFO',
            'propagate': False,
        },
        'background_tasks': {
            'handlers': ['task'],
            'level': 'INFO',
            'propagate': False,
        }
    },
}