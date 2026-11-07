import json

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.urls import reverse

from apps.blog.models import Post


def environment_callback(request):
    env_id = str(getattr(settings, "BLOG_ENV_ID", "local")).lower()
    
    if env_id in ("production", "prod"):
        return "Production", "danger"
    return "Local", "warning"

def drafts_badge(request):
    return Post.objects.filter(
        status=Post.Status.DRAFT
    ).count()


def superuser_only(request):
    return request.user.is_superuser


def posts_all_url(request):
    return reverse("admin:blog_post_changelist")


def posts_published_url(request):
    return (
        reverse("admin:blog_post_changelist")
        + "?status__exact=published"
    )


def posts_drafts_url(request):
    return (
        reverse("admin:blog_post_changelist")
        + "?status__exact=draft"
    )
    
def dashboard_callback(request, context):
    User = get_user_model()

    total_users = User.objects.count()

    published_count = Post.objects.filter(
        status=Post.Status.PUBLISHED
    ).count()

    draft_count = Post.objects.filter(
        status=Post.Status.DRAFT
    ).count()

    comments_count = Post.objects.filter(
        status=Post.Status.PUBLISHED
    ).aggregate(
        total=Count("comments")
    )["total"] or 0

    categories = (
        Post.objects
        .values("category__name")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    chart_data = {
        "labels": [
            item["category__name"] or "Uncategorized"
            for item in categories
        ],
        "datasets": [
            {
                "label": "Posts",
                "data": [
                    item["total"]
                    for item in categories
                ],
            }
        ],
    }

    top_authors = (
        User.objects
        .annotate(posts_count=Count("posts"))
        .order_by("-posts_count", "email")[:5]
    )
    
    authors_table = {
        "headers": ["Author", "Email", "Posts"],
        "rows": [
            [
                f"{author.first_name} {author.last_name}".strip(),
                author.email,
                author.posts_count,
            ]
            for author in top_authors
        ],
    }

    total_posts = published_count + draft_count

    published_percent = (
        round(published_count / total_posts * 100)
        if total_posts else 0
    )

    draft_percent = (
        round(draft_count / total_posts * 100)
        if total_posts else 0
    )

    context.update({
        "total_users": total_users,
        "published_count": published_count,
        "draft_count": draft_count,
        "comments_count": comments_count,
        "posts_chart": json.dumps(chart_data),
        "top_authors": top_authors,
        "published_percent": published_percent,
        "draft_percent": draft_percent,
        "authors_table":authors_table,
    })

    return context
