from __future__ import absolute_import, unicode_literals

from .base import *

import os

DEBUG = False

ALLOWED_HOSTS = [ '162.242.218.160', '.outreachy.org' ]

SECRET_KEY = os.environ['SECRET_KEY']

try:
    from .local import *
except ImportError:
    pass
