from __future__ import absolute_import, unicode_literals

from .base import *

import os

DEBUG = False

# Only minify CSS and JavaScript when in production.
COMPRESS_CSS_FILTERS.append('compressor.filters.cssmin.rCSSMinFilter')
COMPRESS_JS_FILTERS.append('compressor.filters.jsmin.JSMinFilter')

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '162.242.218.160 .outreachy.org').split()

SECRET_KEY = os.environ['SECRET_KEY']
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'localhost')
# Environment variables are strings, so we need to convert to an integer
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 25))
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
# Environment variables are strings, so we need to convert to an bool
EMAIL_USE_SSL = bool(os.environ.get('EMAIL_USE_SSL', False))

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
    from .local import *
except ImportError:
    pass
