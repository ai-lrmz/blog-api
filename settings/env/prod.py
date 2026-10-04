from settings.base import *


DEBUG = False

ALLOWED_HOSTS = []


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "blog_db",
        "USER": "blog_user",
        "PASSWORD": "change-me",
        "HOST": "localhost",
        "PORT": "5432",
    }
}