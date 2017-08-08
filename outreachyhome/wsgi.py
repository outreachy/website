"""
WSGI config for outreachyhome project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/howto/deployment/wsgi/
"""

from __future__ import absolute_import, unicode_literals

import os

from django.core.wsgi import get_wsgi_application
from dj_static import MediaCling

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "outreachyhome.settings.dev")

application = MediaCling(get_wsgi_application())
