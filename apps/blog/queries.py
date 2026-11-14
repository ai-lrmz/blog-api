
"""Django ORM queries for Homework 3."""
from datetime import date, timedelta
from typing import Any

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import (
    Avg,
    Case,
    CharField,
    Count,
    Exists,
    F,
    Max,
    Min,
    OuterRef,
    Prefetch,
    Q,
    QuerySet,
    Subquery,
    Value,
    When,
)
from django.db.models.functions import Coalesce, Concat, TruncMonth
from django.utils import timezone
from django.utils.text import slugify

from apps.auths.models import User
from apps.blog.models import Category, Comment, Post, Tag

PAGE_SIZE = 10
NEWEST_POSTS_LIMIT = 5
UNCATEGORIZED_LABEL = "Uncategorized"
AVERAGE_DECIMAL_PLACES = 2
TOP_AUTHORS_LIMIT = 5


def categories_by_name() -> QuerySet[Category]:
    """Return all categories sorted alphabetically."""
    return Category.objects.order_by("name")


def published_posts() -> QuerySet[Post]:
    """Return published posts ordered from newest to oldest."""
    return Post.objects.filter(
        status=Post.Status.PUBLISHED,
    ).order_by("-created_at")


def newest_published_posts() -> QuerySet[Post]:
    """Return the five newest published posts."""
    return published_posts()[:NEWEST_POSTS_LIMIT]


def post_by_slug(slug: str) -> Post | None:
    """Return a post by slug or None if it does not exist."""
    return Post.objects.filter(slug=slug).first()


def active_users_count() -> int:
    """Count active users excluding staff users."""
    user_model = get_user_model()

    return user_model.objects.filter(
        is_active=True,
        is_staff=False,
    ).count()


def has_drafts() -> bool:
    """Check whether at least one draft post exists."""
    return Post.objects.filter(
        status=Post.Status.DRAFT,
    ).exists()


def published_posts_page(page: int) -> QuerySet[Post]:
    """Return a page of published posts with ten posts per page."""
    start = (page - 1) * PAGE_SIZE
    end = start + PAGE_SIZE

    return published_posts()[start:end]


def posts_with_word_in_title(word: str) -> QuerySet[Post]:
    """Return posts containing a word in the title."""
    return Post.objects.filter(
        title__icontains=word,
    )


def users_with_email_domain(domain: str) -> QuerySet[User]:
    """Return users whose email belongs to the given domain."""
    return User.objects.filter(
        email__iendswith=f"@{domain}",
    )


def posts_without_category() -> QuerySet[Post]:
    """Return posts that have no category."""
    return Post.objects.filter(
        category__isnull=True,
    )


def categories_by_slugs(
    slugs: list[str],
) -> QuerySet[Category]:
    """Return categories matching the provided slugs."""
    return Category.objects.filter(
        slug__in=slugs,
    )


def posts_in_month(
    year: int,
    month: int,
) -> QuerySet[Post]:
    """Return posts created in the given month and year."""
    return Post.objects.filter(
        created_at__year=year,
        created_at__month=month,
    )


def posts_last_days(days: int) -> QuerySet[Post]:
    """Return posts created within the last number of days."""
    cutoff = timezone.now() - timedelta(days=days)

    return Post.objects.filter(
        created_at__gte=cutoff,
    )


def posts_between(
    start: date,
    end: date,
) -> QuerySet[Post]:
    """Return posts created between two inclusive dates."""
    return Post.objects.filter(
        created_at__date__gte=start,
        created_at__date__lte=end,
    )


def author_published_posts(email: str) -> QuerySet[Post]:
    """Return published posts written by the given author."""
    return Post.objects.filter(
        author__email__iexact=email,
        status=Post.Status.PUBLISHED,
    )


def posts_with_tag(tag_slug: str) -> QuerySet[Post]:
    """Return posts containing the specified tag."""
    return Post.objects.filter(
        tags__slug=tag_slug,
    )


def comments_in_category(
    category_slug: str,
) -> QuerySet[Comment]:
    """Return comments on posts in the given category."""
    return Comment.objects.filter(
        post__category__slug=category_slug,
    )


def users_with_published_posts() -> QuerySet[User]:
    """Return unique users who have published posts."""
    return User.objects.filter(
        posts__status=Post.Status.PUBLISHED,
    ).distinct()


def posts_without_tags() -> QuerySet[Post]:
    """Return posts without any tags."""
    return Post.objects.filter(
        tags__isnull=True,
    )


def users_without_comments() -> QuerySet[User]:
    """Return users who have never written comments."""
    return User.objects.filter(
        comments__isnull=True,
    )


def posts_with_both_tags(
    first_slug: str,
    second_slug: str,
) -> QuerySet[Post]:
    """Return posts containing both specified tags."""
    return (
        Post.objects.filter(
            tags__slug=first_slug,
        )
        .filter(
            tags__slug=second_slug,
        )
        .distinct()
    )


# Level 4 — Q and F expressions

EDIT_THRESHOLD_HOURS = 1


def search_posts(text: str) -> QuerySet[Post]:
    """Find posts containing text in the title or body."""
    return Post.objects.filter(
        Q(title__icontains=text)
        | Q(body__icontains=text)
    )


def published_posts_missing_info() -> QuerySet[Post]:
    """Find published posts missing a category or tags."""
    return Post.objects.filter(
        Q(category__isnull=True)
        | Q(tags__isnull=True),
        status=Post.Status.PUBLISHED,
    ).distinct()


def edited_posts() -> QuerySet[Post]:
    """Find posts edited more than one hour after creation."""
    return Post.objects.filter(
        updated_at__gt=(
            F("created_at")
            + timedelta(hours=EDIT_THRESHOLD_HOURS)
        )
    )


def comments_by_post_author() -> QuerySet[Comment]:
    """Find comments written by their post's author."""
    return Comment.objects.filter(
        author=F("post__author"),
    )


def comments_before_post() -> QuerySet[Comment]:
    """Find comments created before their parent post."""
    return Comment.objects.filter(
        created_at__lt=F("post__created_at"),
    )


# Level 5 — values and values_list


def published_authors_emails() -> list[str]:
    """Return unique published authors' emails sorted alphabetically."""
    return list(
        User.objects.filter(
            posts__status=Post.Status.PUBLISHED,
        )
        .order_by("email")
        .values_list("email", flat=True)
        .distinct()
    )


def published_posts_overview() -> list[dict[str, Any]]:
    """Return published posts with title, author and category."""
    return list(
        Post.objects.filter(
            status=Post.Status.PUBLISHED,
        )
        .values(
            "title",
            author_email=F("author__email"),
            category_name=Coalesce(
                F("category__name"),
                Value(UNCATEGORIZED_LABEL),
                output_field=CharField(),
            ),
        )
    )


# Level 6 — Aggregation


def posts_stats() -> dict[str, Any]:
    """Return post counts and earliest/latest creation dates."""
    return Post.objects.aggregate(
        total=Count("id"),
        published=Count(
            "id",
            filter=Q(status=Post.Status.PUBLISHED),
        ),
        drafts=Count(
            "id",
            filter=Q(status=Post.Status.DRAFT),
        ),
        first_post_at=Min("created_at"),
        last_post_at=Max("created_at"),
    )


def average_comments_per_post() -> float:
    """Return average comment count per published post."""
    average = (
        Post.objects.filter(
            status=Post.Status.PUBLISHED,
        )
        .annotate(
            comment_count=Count("comments"),
        )
        .aggregate(
            average=Avg("comment_count"),
        )["average"]
    )

    return round(average or 0.0, AVERAGE_DECIMAL_PLACES)


# Level 7 — Annotations


def categories_with_post_count() -> QuerySet[Category]:
    """Return categories ordered by their post count."""
    return Category.objects.annotate(
        post_count=Count("posts"),
    ).order_by("-post_count", "name")


def categories_with_published_count() -> QuerySet[Category]:
    """Return categories with their published post counts."""
    return Category.objects.annotate(
        published_count=Count(
            "posts",
            filter=Q(
                posts__status=Post.Status.PUBLISHED,
            ),
        ),
    ).order_by("-published_count", "name")


def top_authors() -> QuerySet[User]:
    """Return the five authors with most published posts."""
    return User.objects.annotate(
        published_count=Count(
            "posts",
            filter=Q(
                posts__status=Post.Status.PUBLISHED,
            ),
        ),
    ).order_by("-published_count", "email")[:TOP_AUTHORS_LIMIT]


def popular_tags(min_posts: int) -> QuerySet[Tag]:
    """Return tags used in at least min_posts posts."""
    return Tag.objects.annotate(
        post_count=Count("posts"),
    ).filter(
        post_count__gte=min_posts,
    ).order_by("-post_count", "name")


def posts_per_status() -> list[dict[str, Any]]:
    """Return the number of posts grouped by status."""
    return list(
        Post.objects.values("status")
        .annotate(count=Count("id"))
        .order_by("status")
    )


def users_activity() -> QuerySet[User]:
    """Return users with correct post and comment counts."""
    return User.objects.annotate(
        post_count=Count("posts", distinct=True),
        comment_count=Count("comments", distinct=True),
    ).order_by("email")


# Level 8 — Database Functions and Conditions

HOT_COMMENTS_LIMIT = 10
NORMAL_COMMENTS_LIMIT = 3

POPULARITY_HOT = "hot"
POPULARITY_NORMAL = "normal"
POPULARITY_QUIET = "quiet"

FULL_NAME_SEPARATOR = " "


def search_users_by_full_name(text: str) -> QuerySet[User]:
    """Find users by their full name, ignoring letter case."""
    return User.objects.annotate(
        full_name=Concat(
            F("first_name"),
            Value(FULL_NAME_SEPARATOR),
            F("last_name"),
            output_field=CharField(),
        ),
    ).filter(
        full_name__icontains=text,
    )


def published_posts_per_month() -> list[dict[str, Any]]:
    """Count published posts grouped by creation month."""
    return list(
        Post.objects.filter(
            status=Post.Status.PUBLISHED,
        )
        .annotate(
            month=TruncMonth("created_at"),
        )
        .values("month")
        .annotate(
            count=Count("id"),
        )
        .order_by("month")
    )


def posts_with_popularity() -> QuerySet[Post]:
    """Annotate posts with comment counts and popularity labels."""
    return Post.objects.annotate(
        comment_count=Count("comments"),
    ).annotate(
        popularity=Case(
            When(
                comment_count__gte=HOT_COMMENTS_LIMIT,
                then=Value(POPULARITY_HOT),
            ),
            When(
                comment_count__gte=NORMAL_COMMENTS_LIMIT,
                then=Value(POPULARITY_NORMAL),
            ),
            default=Value(POPULARITY_QUIET),
            output_field=CharField(),
        ),
    )


# Level 9 — Changing Data


def get_or_create_tag(name: str) -> tuple[Tag, bool]:
    """Get a tag by slug or create it if missing."""
    slug = slugify(name)

    return Tag.objects.get_or_create(
        slug=slug,
        defaults={"name": name},
    )


def publish_old_drafts(days: int) -> int:
    """Publish drafts older than the specified number of days."""
    cutoff = timezone.now() - timedelta(days=days)

    return Post.objects.filter(
        status=Post.Status.DRAFT,
        created_at__lt=cutoff,
    ).update(
        status=Post.Status.PUBLISHED,
        updated_at=timezone.now(),
    )



def tag_category_posts(
    category_slug: str,
    tag_slug: str,
) -> int:
    """Add a tag to all category posts without duplicates."""
    posts = Post.objects.filter(
        category__slug=category_slug,
    )

    tag = Tag.objects.get(slug=tag_slug)

    post_count = posts.count()

    tag.posts.add(*posts)

    return post_count


def merge_categories(
    source_slug: str,
    target_slug: str,
) -> int:
    """Move posts to another category and delete the source."""
    if source_slug == target_slug:
        return 0

    with transaction.atomic():
        source = Category.objects.get(slug=source_slug)
        target = Category.objects.get(slug=target_slug)

        moved_count = Post.objects.filter(
            category=source,
        ).update(
            category=target,
        )

        source.delete()

    return moved_count


def delete_inactive_users_comments() -> int:
    """Delete comments written by inactive users."""
    deleted_count, _ = Comment.objects.filter(
        author__is_active=False,
    ).delete()

    return deleted_count


# Level 10 — select_related and prefetch_related

FEED_LIMIT = 50
NEWEST_TAGGED_POSTS_LIMIT = 20
TAG_SEPARATOR = ", "
FEED_SEPARATOR = " | "


def published_feed() -> list[str]:
    """Return published post feed using one SQL query."""
    posts = (
        Post.objects.filter(
            status=Post.Status.PUBLISHED,
        )
        .select_related("author", "category")
        .order_by("-created_at", "-pk")[:FEED_LIMIT]
    )

    return [
        FEED_SEPARATOR.join(
            [
                post.title,
                post.author.email,
                (
                    post.category.name
                    if post.category is not None
                    else UNCATEGORIZED_LABEL
                ),
            ]
        )
        for post in posts
    ]


def newest_posts_with_tags() -> list[str]:
    """Return newest posts with tags using at most two queries."""
    posts = (
        Post.objects.order_by("-created_at", "-pk")
        .prefetch_related("tags")[:NEWEST_TAGGED_POSTS_LIMIT]
    )

    return [
        f"{post.title}: "
        f"{TAG_SEPARATOR.join(tag.name for tag in post.tags.all())}"
        for post in posts
    ]


def categories_with_published_posts() -> dict[str, list[str]]:
    """Return categories and their published post titles."""
    categories = Category.objects.prefetch_related(
        Prefetch(
            "posts",
            queryset=Post.objects.filter(
                status=Post.Status.PUBLISHED,
            ).order_by("-created_at", "-pk"),
            to_attr="published_posts_list",
        )
    )

    return {
        category.name: [
            post.title
            for post in category.published_posts_list
        ]
        for category in categories
    }


# Level 11 — Subquery and Exists


def posts_with_last_comment() -> QuerySet[Post]:
    """Return published posts with their newest comment body."""
    latest_comment = (
        Comment.objects.filter(
            post=OuterRef("pk"),
        )
        .order_by("-created_at", "-pk")
        .values("body")[:1]
    )

    return Post.objects.filter(
        status=Post.Status.PUBLISHED,
    ).annotate(
        last_comment=Subquery(latest_comment),
    )


def posts_with_staff_comments() -> QuerySet[Post]:
    """Return posts with at least one comment from a staff user."""
    staff_comments = Comment.objects.filter(
        post=OuterRef("pk"),
        author__is_staff=True,
    )

    return Post.objects.filter(
        Exists(staff_comments),
    )


def users_with_draft_as_latest_post() -> QuerySet[User]:
    """Return users whose newest post is a draft."""
    latest_post = (
        Post.objects.filter(
            author=OuterRef("pk"),
        )
        .order_by("-created_at", "-pk")
        .values("status")[:1]
    )

    return User.objects.annotate(
        latest_post_status=Subquery(latest_post),
    ).filter(
        latest_post_status=Post.Status.DRAFT,
    )


QUERIES = {
    1: categories_by_name,
    2: published_posts,
    3: newest_published_posts,
    4: post_by_slug,
    5: active_users_count,
    6: has_drafts,
    7: published_posts_page,
    8: posts_with_word_in_title,
    9: users_with_email_domain,
    10: posts_without_category,
    11: categories_by_slugs,
    12: posts_in_month,
    13: posts_last_days,
    14: posts_between,
    15: author_published_posts,
    16: posts_with_tag,
    17: comments_in_category,
    18: users_with_published_posts,
    19: posts_without_tags,
    20: users_without_comments,
    21: posts_with_both_tags,
    22: search_posts,
    23: published_posts_missing_info,
    24: edited_posts,
    25: comments_by_post_author,
    26: comments_before_post,
    27: published_authors_emails,
    28: published_posts_overview,
    29: posts_stats,
    30: average_comments_per_post,
    31: categories_with_post_count,
    32: categories_with_published_count,
    33: top_authors,
    34: popular_tags,
    35: posts_per_status,
    36: users_activity,
    37: search_users_by_full_name,
    38: published_posts_per_month,
    39: posts_with_popularity,
    40: get_or_create_tag,
    41: publish_old_drafts,
    42: tag_category_posts,
    43: merge_categories,
    44: delete_inactive_users_comments,
    45: published_feed,
    46: newest_posts_with_tags,
    47: categories_with_published_posts,
    48: posts_with_last_comment,
    49: posts_with_staff_comments,
    50: users_with_draft_as_latest_post,
}
