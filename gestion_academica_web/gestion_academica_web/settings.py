from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-+c+anc-%$wtwf2qgsmeyd&oghuu&9yc4h(v)llg&4(5hj4*k3b'

DEBUG = True

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'academica',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'gestion_academica_web.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'academica' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'gestion_academica_web.wsgi.application'

# Apuntar a la base de datos existente del CLI
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR.parent / 'gestion_academica.db',
    }
}

LANGUAGE_CODE = 'es-ar'
TIME_ZONE = 'America/Argentina/Buenos_Aires'
USE_I18N = True
USE_TZ = False

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

SESSION_ENGINE = 'django.contrib.sessions.backends.db'
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── Email ──────────────────────────────────────────────────────────────────
# En desarrollo: imprime el email en la consola del servidor
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Para producción, reemplazar con SMTP real:
# EMAIL_BACKEND   = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST      = 'smtp.gmail.com'
# EMAIL_PORT      = 587
# EMAIL_USE_TLS   = True
# EMAIL_HOST_USER = 'tucuenta@gmail.com'
# EMAIL_HOST_PASSWORD = 'tu_app_password'

EMAIL_FROM = 'GestiónAcadémica <no-reply@gestionacademica.edu>'
SITE_URL   = 'http://localhost:8000'   # base para armar el link de recuperación
PASSWORD_RESET_EXPIRE_HOURS = 2
