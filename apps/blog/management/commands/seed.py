import random
import time

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify
from faker import Faker

from apps.blog.models import Category, Comment, Post, Tag

DEFAULT_USERS = 20
DEFAULT_POSTS = 100
DEFAULT_COMMENTS = 500
SEED_PASSWORD = "TestPassword123!"


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
        User = get_user_model()
        
        if clear:
            with transaction.atomic():
                Comment.objects.all().delete()
                Post.objects.all().delete()
                Tag.objects.all().delete()
                Category.objects.all().delete()
                User.objects.filter(is_superuser=False).delete()
                
            self.stdout.write(
                self.style.SUCCESS(
                    "Existing data cleared successfully!"
                )
            )
#-----------------------------------------------------------------      
        existing_emails = set(
            User.objects.values_list("email", flat=True)
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
                User(
                    email = email,
                    first_name = first_name,
                    last_name = last_name,
                    password = hashed_password,
                    is_active = (i % 10 != 0),
                    is_staff = (i % 10 == 1),
                )
            )
            existing_emails.add(email)
            
        User.objects.bulk_create(new_users)
#-----------------------------------------------------
        categories = [
            "Web Development",
            "Mobile Development",
            "Artificial Intelligence",
            "Data Science",
            "Cybersecurity",
            "DevOps",
            "Cloud Computing",
            "Software Engineering",
        ]
        
        categories_created = 0

        for name in categories:
            _category, created = Category.objects.get_or_create(
                name=name,
                defaults={"slug": slugify(name)},
            )

            if created:
                categories_created += 1
            
        tags = [
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

        
        tags_created = 0

        for name in tags:
            _tag, created = Tag.objects.get_or_create(
                name=name,
                defaults={"slug": slugify(name)},
            )

            if created:
                tags_created += 1

        #-----------------------------------------------------
        
        users = list(
            User.objects.filter(is_superuser=False)
        )

        category_list = list(Category.objects.all())
        tag_list = list(Tag.objects.all())

        if (posts_count > 0 or comments_count > 0) and not users:
            raise CommandError(
                "Cannot create posts or comments without users."
            )
            
        #--------------------------------------------------------
        
        if posts_count > 0 and not category_list:
            raise CommandError(
                "Cannot create posts without categories."
            )
        
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
                slug = f"{base_slug}-{suffix}"
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

        for post in new_posts:
            post.tags.set(
                random.sample(
                    tag_list,
                    k=random.randint(0, min(5, len(tag_list)))
                )
            )
            
        #-------------------------------------------------------------------
        published_posts = list(
            Post.objects.filter(status=Post.Status.PUBLISHED)
        )

        if comments_count > 0 and not published_posts:
            raise CommandError(
                "Cannot create comments without published posts."
            )

        new_comments = []

        for i in range(comments_count):
            comment = Comment(
                post=random.choice(published_posts),
                author=random.choice(users),
                body=" ".join(
                    fake.sentences(
                        nb=random.randint(1, 3)
                    )
                ),
            )

            new_comments.append(comment)

        Comment.objects.bulk_create(new_comments)
        
        elapsed_time = time.perf_counter() - start_time

        self.stdout.write(
            self.style.SUCCESS(
                f"Users:      {len(new_users)} created\n"
                f"Categories: {categories_created} processed\n"
                f"Tags:       {tags_created} processed\n"
                f"Posts:      {len(new_posts)} created\n"
                f"Comments:   {len(new_comments)} created\n"
                f"Done in {elapsed_time:.2f} seconds"
            )
        )