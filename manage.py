import os
import sys
from pathlib import Path

from decouple import Config, RepositoryEnv


BASE_DIR = Path(__file__).resolve().parent

env = Config(
    RepositoryEnv(BASE_DIR / "settings" / ".env")
)

environment = env("BLOG_ENV_ID", default="local")

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    f"settings.env.{environment}",
)


def main():
    """Run administrative tasks."""
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Make sure it is installed."
        ) from exc

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()