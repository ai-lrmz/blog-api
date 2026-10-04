from settings.base import *
from settings.conf import BLOG_DEBUG


DEBUG = BLOG_DEBUG

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}