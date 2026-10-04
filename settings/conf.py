from pathlib import Path

from decouple import Config, RepositoryEnv


BASE_DIR = Path(__file__).resolve().parent.parent

config = Config(RepositoryEnv(BASE_DIR / "settings" / ".env"))

BLOG_ENV_ID = config("BLOG_ENV_ID", default="local")
BLOG_SECRET_KEY = config("BLOG_SECRET_KEY")
BLOG_DEBUG = config("BLOG_DEBUG", default=True, cast=bool)