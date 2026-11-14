import random
import time
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify
from faker import Faker

from apps.blog.models import Category, Comment, Post, Tag

DEFAULT_USERS = 20
DEFAULT_POSTS = 100
DEFAULT_COMMENTS = 500

SEED_PASSWORD = "TestPassword123!"

POST_AGE_DAYS = 365
UPDATED_POST_RATIO = 0.30
MIN_UPDATE_DAYS = 1
MAX_UPDATE_DAYS = 30

MAX_TAGS_PER_POST = 5

CATEGORIES = [
            "Web Development",
            "Mobile Development",
            "Artificial Intelligence",
            "Data Science",
            "Cybersecurity",
            "DevOps",
            "Cloud Computing",
            "Software Engineering",
        ]

TAGS = [
            "Python",
            "Django",
            "REST API",
            "PostgreSQL",
            "Docker",
            "Git",
            "GitHub",
            "Linux",
            "JavaScript",
            "HTML",
            "CSS",
            "React",
            "Machine Learning",
            "Deep Learning",
            "Data Analysis",
            "AWS",
            "Testing",
            "Security",
            "Backend",
            "Flutter",
        ]

def random_datetime_betwwen(start, end):
    """Generate a random datetime between two datetime objects."""
    if start >= end:
        return start
    total_seconds = int((end - start).total_seconds())

    return start + timedelta(seconds=random.randint(0, total_seconds))

def generate_post_dates(now):
    """Generate random created and updated dates for a post."""
    earliest_date = now - timedelta(days=POST_AGE_DAYS)

    created_at = random_datetime_betwwen(
        earliest_date,
        now,
    )

    updated_at = created_at

    if random.random() < UPDATED_POST_RATIO:
        days_after = random.randint(
            MIN_UPDATE_DAYS,
            MAX_UPDATE_DAYS,
        )
        candidate_date = created_at + timedelta(
            days = days_after,
        )

        if candidate_date <= now:
            updated_at = candidate_date

    return created_at, updated_at

class Command(BaseCommand):

    help = "Fill the database with fake data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--users",
            type=int,
            default=DEFAULT_USERS,
            help="Number of users to create",
        )

        parser.add_argument(
            "--posts",
            type=int,
            default=DEFAULT_POSTS,
            help="Number of posts to create",
        )

        parser.add_argument(
            "--comments",
            type=int,
            default=DEFAULT_COMMENTS,
            help="Number of comments to create",
        )

        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing data before seeding",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        start_time = time.perf_counter()

        users_count = options["users"]
        posts_count = options["posts"]
        comments_count = options["comments"]
        clear = options["clear"]

        if users_count < 0:
            raise CommandError("Users count cannot be negative.")
        if posts_count < 0:
            raise CommandError("Posts count cannot be negative.")
        if comments_count < 0:
            raise CommandError("Comments count cannot be negative.")

        fake = Faker()
        user_model = get_user_model()
        now = timezone.now()

        #1. Clear existing data
        if clear:
            Comment.objects.all().delete()
            Post.objects.all().delete()
            Tag.objects.all().delete()
            Category.objects.all().delete()

            user_model.objects.filter(
                is_superuser=False,
            ).delete()

            self.stdout.write(
                self.style.SUCCESS(
                    "Existing data cleared successfully!"
                )
            )
        # 2. Create users
        existing_emails = set(
            user_model.objects.values_list(
                "email",
                flat=True
            )
        )

        hashed_password = make_password(SEED_PASSWORD)
        new_users = []

        for i in range(users_count):
            first_name = fake.first_name()
            last_name = fake.last_name()

            email_base = slugify(
                f"{first_name}.{last_name}"
            )

            email = f"{email_base}@example.com"
            suffix = 2

            while email in existing_emails:
                email = f"{email_base}{suffix}@example.com"
                suffix += 1



            new_users.append(
                user_model(
                    email = email,
                    first_name = first_name,
                    last_name = last_name,
                    password = hashed_password,
                    is_active = (i % 10 != 0),
                    is_staff = (i % 10 == 1),
                )
            )
            existing_emails.add(email)

        user_model.objects.bulk_create(new_users)

        # 3. Create categories

        categories_created = 0

        for name in CATEGORIES:
            _category, created = Category.objects.get_or_create(
                name=name,
                defaults={"slug": slugify(name)},
            )

            if created:
                categories_created += 1

        #4 . Create tags

        tags_created = 0

        for name in TAGS:
            _tag, created = Tag.objects.get_or_create(
                name=name,
                defaults={"slug": slugify(name)},
            )

            if created:
                tags_created += 1

        # 5. Load users and related data

        users = list(
            user_model.objects.filter(is_superuser=False)
        )

        category_list = list(Category.objects.all())
        tag_list = list(Tag.objects.all())

        if (posts_count > 0 or comments_count > 0) and not users:
            raise CommandError(
                "Cannot create posts or comments without users."
            )

        if posts_count > 0 and not category_list:
            raise CommandError(
                "Cannot create posts without categories."
            )

        # 6. Create posts

        used_slugs = set(
            Post.objects.values_list("slug", flat=True)
        )

        new_posts = []

        for i in range(posts_count):
            title = fake.sentence(nb_words=6)

            base_slug = slugify(title)[:45] or "post"
            slug = base_slug
            suffix = 2

            while slug in used_slugs:
                suffix_text = f"-{suffix}"
                slug = (
                    f"{base_slug[:50 - len(suffix_text)]}"
                    f"{suffix_text}"
                )
                suffix += 1

            used_slugs.add(slug)

            post = Post(
                author=random.choice(users),
                title=title,
                slug=slug,
                body="\n\n".join(fake.paragraphs(nb=3)),
                category=(
                    None
                    if i % 10 == 0
                    else random.choice(category_list)
                ),
                status=(
                    Post.Status.PUBLISHED
                    if i % 10 < 7
                    else Post.Status.DRAFT
                ),
            )

            new_posts.append(post)

        Post.objects.bulk_create(new_posts)

        # 7. Set realistic post dates

        for post in new_posts:
            created_at, updated_at = (
                generate_post_dates(now)
            )
            post.created_at = created_at
            post.updated_at = updated_at

        if new_posts:
            Post.objects.bulk_update(
                new_posts,
                ["created_at", "updated_at"]
            )

        # 8. Assign tags

        for post in new_posts:
            selected_tags = random.sample(
                tag_list,
                k=random.randint(
                    0,
                    min(
                        MAX_TAGS_PER_POST,
                        len(tag_list),
                    ),

                ),
            )
            post.tags.set(selected_tags)

        # 9. Get published posts from memory

        published_posts = [
            post
            for post in new_posts
            if post.status == Post.Status.PUBLISHED
        ]

        if comments_count > 0 and not published_posts:
            raise CommandError(
                "Cannot create comments without published posts."
            )

        # 10. Create comments

        new_comments = []
        comment_dates = []

        for _ in range(comments_count):
            post = random.choice(published_posts)
            comment = Comment(
                post=post,
                author=random.choice(users),
                body=" ".join(
                    fake.sentences(
                        nb=random.randint(1, 3)
                    )
                ),
            )

            new_comments.append(comment)

            # Comment date must not be
            # earlier than its post date.

            comment_created_at = (
                random_datetime_betwwen(
                    post.created_at,
                    now,
                )
            )

            comment_dates.append(comment_created_at)

        Comment.objects.bulk_create(new_comments)

        # 11. Update comment dates

        for comment, created_at in zip(
            new_comments,
            comment_dates,
        ):
            comment.created_at = created_at

        if new_comments:
            Comment.objects.bulk_update(
                new_comments,
                ["created_at"],
            )

        # 12. Print summary

        elapsed_time = (
            time.perf_counter() - start_time
        )

        updated_posts_count = sum(
            post.updated_at > post.created_at
            for post in new_posts
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Users:      {len(new_users)} created\n"
                f"Categories: {categories_created} created\n"
                f"Tags:       {tags_created} created\n"
                f"Posts:      {len(new_posts)} created\n"
                f"Updated posts: {updated_posts_count}\n"
                f"Comments:   {len(new_comments)} created\n"
                f"Done in {elapsed_time:.2f} seconds"
            )
        )