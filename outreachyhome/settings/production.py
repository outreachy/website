from __future__ import absolute_import, unicode_literals

from .base import *

import os

DEBUG = False

# Only minify CSS and JavaScript when in production.
COMPRESS_CSS_FILTERS.append('compressor.filters.cssmin.rCSSMinFilter')
COMPRESS_JS_FILTERS.append('compressor.filters.jsmin.JSMinFilter')

ALLOWED_HOSTS = [ '162.242.218.160', '.outreachy.org' ]

SECRET_KEY = os.environ['SECRET_KEY']
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'localhost')
# Environment variables are strings, so we need to convert to an integer
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 25))
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
# Environment variables are strings, so we need to convert to an bool
EMAIL_USE_SSL = bool(os.environ.get('EMAIL_USE_SSL', False))

try:
    from .local import *
except ImportError:
    pass
