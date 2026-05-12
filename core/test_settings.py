"""
Configurações para execução dos testes – usa SQLite em memória.
"""
from core.settings import *

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Desabilita cache e sessões complexas durante testes
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# Evita envio real de e-mails
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Chaves falsas para testes
RESEND_API_KEY = "test-key"
SECRET_KEY = "django-test-secret-key-only-for-tests"

# Silencia logs durante testes
import logging
logging.disable(logging.CRITICAL)
