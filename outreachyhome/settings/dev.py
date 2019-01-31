from __future__ import absolute_import, unicode_literals

from .base import *  # noqa: F401,F403

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'k^)qcm)yhze23d2pk!zx7#ip3%)yxj!9&hpe1a3r_4#1gr_9&h'


EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


try:
    from .local import *  # noqa: F401,F403
except ImportError:
    pass
