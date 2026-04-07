"""
WSGI config for gestion_academica project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_academica.settings')

application = get_wsgi_application()
