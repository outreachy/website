from __future__ import absolute_import, unicode_literals

from .base import *  # noqa: F401,F403

import os

DEBUG = False

COMPRESS_OFFLINE = True

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '162.242.218.160 .outreachy.org').split()

# Make sure the specified address matches the IP address of the reverse
# proxy that gunicorn receives connections from. This is the default
# value if you deploy in Docker, and you haven't changed Docker's
# default subnet, and the reverse proxy is running on the host machine
# that's running Docker. These conditions apply to a default Dokku
# installation, for example.
TRUSTED_PROXIES = os.getenv('TRUSTED_PROXIES', '172.17.0.1').split()

SECRET_KEY = os.environ['SECRET_KEY']

EMAIL_HOST = os.environ.get('EMAIL_HOST')
if EMAIL_HOST:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    # Environment variables are strings, so we need to convert to an integer
    EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 25))
    EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
    # Environment variables are strings, so we need to convert to an bool
    EMAIL_USE_SSL = bool(os.environ.get('EMAIL_USE_SSL', False))
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# In production, log warnings and errors to the console where Dokku will
# capture them for display using `dokku logs`. You can get more detailed
# logs by running `dokku config:set $APP DJANGO_LOG_LEVEL=DEBUG`, but
# you should probably undo that again when you're done debugging.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[%(levelname)s] %(name)s: %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'WARNING'),
        },
    },
}

try:
    from .local import *  # noqa: F401,F403
except ImportError:
    pass
