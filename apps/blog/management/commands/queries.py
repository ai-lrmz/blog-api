
"""Management command for running blog ORM queries."""

from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.db.models import Model, QuerySet
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from apps.auths.models import User
from apps.blog.models import Category, Post, Tag
from apps.blog.queries import QUERIES

PREVIEW_LIMIT = 5

MUTATING_QUERIES = {40, 41, 42, 43, 44}

SAMPLE_DAYS = 30
SAMPLE_PAGE = 1
SAMPLE_YEAR_DAYS = 365
SAMPLE_MIN_POSTS = 5

SAMPLE_WORD = "the"
SAMPLE_DOMAIN = "example.com"
SAMPLE_TAG_NAME = "Django ORM"
SAMPLE_TAG_SLUG = "django"
SAMPLE_SECOND_TAG_SLUG = "python"
SAMPLE_CATEGORY_SLUG = "web-development"
SAMPLE_TARGET_CATEGORY_SLUG = "devops"


class Command(BaseCommand):
    """Run ORM queries and display results and SQL statements."""

    help = "Run blog ORM queries and inspect SQL."

    def add_arguments(self, parser):
        """Register command-line arguments."""
        parser.add_argument(
            "--number",
            type=int,
            help="Run a specific query by number.",
        )
        parser.add_argument(
            "--sql",
            action="store_true",
            help="Show executed SQL statements.",
        )

    def get_sample_arguments(self) -> dict:
        """Prepare sample arguments for parameterized queries."""
        now = timezone.now()

        sample_post = Post.objects.order_by("pk").first()

        sample_author = (
            User.objects.filter(
                posts__isnull=False,
            )
            .distinct()
            .order_by("pk")
            .first()
        )

        sample_category = Category.objects.order_by("pk").first()
        sample_tag = Tag.objects.order_by("pk").first()

        post_slug = sample_post.slug if sample_post else ""
        author_email = sample_author.email if sample_author else ""

        category_slug = (
            sample_category.slug
            if sample_category
            else SAMPLE_CATEGORY_SLUG
        )

        tag_slug = (
            sample_tag.slug
            if sample_tag
            else SAMPLE_TAG_SLUG
        )

        return {
            4: {"slug": post_slug},
            7: {"page": SAMPLE_PAGE},
            8: {"word": SAMPLE_WORD},
            9: {"domain": SAMPLE_DOMAIN},
            11: {
                "slugs": [
                    category_slug,
                    SAMPLE_TARGET_CATEGORY_SLUG,
                ]
            },
            12: {
                "year": now.year,
                "month": now.month,
            },
            13: {"days": SAMPLE_YEAR_DAYS},
            14: {
                "start": (now - timedelta(days=SAMPLE_YEAR_DAYS)).date(),
                "end": now.date(),
            },
            15: {"email": author_email},
            16: {"tag_slug": tag_slug},
            17: {"category_slug": category_slug},
            21: {
                "first_slug": SAMPLE_TAG_SLUG,
                "second_slug": SAMPLE_SECOND_TAG_SLUG,
            },
            22: {"text": SAMPLE_WORD},
            34: {"min_posts": SAMPLE_MIN_POSTS},
            37: {"text": "a"},
            40: {"name": SAMPLE_TAG_NAME},
            41: {"days": SAMPLE_DAYS},
            42: {
                "category_slug": category_slug,
                "tag_slug": tag_slug,
            },
            43: {
                "source_slug": category_slug,
                "target_slug": SAMPLE_TARGET_CATEGORY_SLUG,
            },
        }

    def handle(self, *args, **options):
        """Execute requested queries."""
        number = options["number"]
        show_sql = options["sql"]

        if number is not None:
            if number not in QUERIES:
                raise CommandError(
                    f"Query {number} does not exist."
                )

            numbers = [number]
        else:
            numbers = [
                query_number
                for query_number in sorted(QUERIES)
                if query_number not in MUTATING_QUERIES
            ]

        sample_arguments = self.get_sample_arguments()

        for query_number in numbers:
            self.run_query(
                query_number,
                show_sql,
                sample_arguments.get(query_number, {}),
            )

    def format_model(self, obj: Model, queryset=None) -> str:
        """Format a model without triggering extra SQL queries."""
        if obj._meta.model_name == "comment":
            text = f"Comment #{obj.pk}"
        else:
            text = str(obj)

        if queryset is not None:
            annotation_names = queryset.query.annotations

            if annotation_names:
                values = {
                    name: getattr(obj, name)
                    for name in annotation_names
                }

                text = f"{text} {values}"

        return text

    def run_query(
        self,
        number: int,
        show_sql: bool,
        arguments: dict,
    ) -> None:
        """Run one query and capture all executed SQL."""
        function = QUERIES[number]

        with CaptureQueriesContext(connection) as context:
            result = function(**arguments)

            if isinstance(result, QuerySet):
                rows = list(result)
                total = len(rows)

                preview = [
                    self.format_model(row, result)
                    if isinstance(row, Model)
                    else str(row)
                    for row in rows[:PREVIEW_LIMIT]
                ]

            elif isinstance(result, list):
                total = len(result)

                preview = [
                    str(row)
                    for row in result[:PREVIEW_LIMIT]
                ]

            elif isinstance(result, (tuple, dict)):
                total = None
                preview = [str(result)]

            else:
                total = None
                preview = [str(result)]

        query_count = len(context.captured_queries)

        query_label = (
            "SQL query"
            if query_count == 1
            else "SQL queries"
        )

        self.stdout.write(
            f"\n{number} {function.__name__} "
            f"— {query_count} {query_label}"
        )

        if show_sql:
            for captured_query in context.captured_queries:
                self.stdout.write(
                    captured_query["sql"]
                )

        for row in preview:
            self.stdout.write(row)

        if total is not None:
            self.stdout.write(
                f"({total} rows)"
            )
