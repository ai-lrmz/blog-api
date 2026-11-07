from django.contrib import admin, messages
from django.db import models
from django.db.models import Count
from django.http import HttpResponseRedirect
from django.urls import reverse
from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.filters.admin import (
    AutocompleteSelectFilter,
    ChoicesDropdownFilter,
    MultipleRelatedDropdownFilter,
    RangeDateTimeFilter,
    RelatedDropdownFilter,
)
from unfold.contrib.forms.widgets import WysiwygWidget
from unfold.decorators import action, display
from unfold.sections import TableSection

from .models import Category, Comment, Post, Tag


class CategoryPostsSection(TableSection):
    related_name = "posts"
    verbose_name = "Posts in this category"
    fields = ["title", "status", "created_at"]

@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    
    list_sections = [CategoryPostsSection]
    
    list_display = (
        "name",
        "slug",
        "posts_count",
    )

    search_fields = ("name",)

    prepopulated_fields = {
        "slug": ("name",),
    }

    def get_queryset(self, request):
        queryset = super().get_queryset(request)

        return queryset.annotate(
            _posts_count=Count("posts")
        )

    @display(
        description="Posts",
        ordering="_posts_count",
    )
    def posts_count(self, obj):
        return obj._posts_count


@admin.register(Tag)
class TagAdmin(ModelAdmin):
    list_display = (
        "name",
        "slug",
        "posts_count",
    )

    search_fields = ("name",)

    prepopulated_fields = {
        "slug": ("name",),
    }

    def get_queryset(self, request):
        queryset = super().get_queryset(request)

        return queryset.annotate(
            _posts_count=Count("posts")
        )

    @display(
        description="Posts",
        ordering="_posts_count",
    )
    def posts_count(self, obj):
        return obj._posts_count


class PostCommentsSection(TableSection):
    related_name = "comments"
    verbose_name = "Comments on this post"
    fields = ["author", "body", "created_at"]
    
    
class CommentInline(TabularInline):
    model = Comment
    extra = 0 
    tab = True
    per_page = 10
    
    fields = (
        "author",
        "body",
        "created_at",
    )
    
    readonly_fields = ("created_at",)
    autocomplete_fields = ("author",)

@admin.register(Post)
class PostAdmin(ModelAdmin):
    inlines = [CommentInline]
    list_sections = [PostCommentsSection]
    
    actions = [
        "publish_selected",
        "move_to_drafts",
    ]
    
    formfield_overrides = {
    models.TextField: {
        "widget": WysiwygWidget,
        },
    }
    
    list_display = (
        "post_header",
        "status_label",
        "category",
        "tags_dropdown",
        "comments_count",
        "created_at",
    )
    
    list_filter = [
        ("status", ChoicesDropdownFilter),
        ("category", RelatedDropdownFilter),
        ("tags", MultipleRelatedDropdownFilter),
        ("author", AutocompleteSelectFilter),
        ("created_at", RangeDateTimeFilter),
    ]

    list_filter_submit = True

    autocomplete_fields = (
        "author",
        "category",
        "tags",
    )

    search_fields = (
        "title",
        "body",
        "author__email",
    )

    list_select_related = (
        "author",
        "category",
    )

    prepopulated_fields = {
        "slug": ("title",),
    }
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)

        return queryset.select_related(
            "author",
            "category",
        ).prefetch_related(
            "tags",
        ).annotate(
            _comments_count=Count("comments")
        )

    @display(description="Post", header=True)
    def post_header(self, obj):
        return obj.title, obj.author.email

    @display(
        description="Status",
        label={
            "published": "success",
            "draft": "warning",
        },
    )
    def status_label(self, obj):
        return obj.status, obj.get_status_display()

    @display(description="Tags", dropdown=True)
    def tags_dropdown(self, obj):
        return [
            tag.name
            for tag in obj.tags.all()
        ]

    @display(
        description="Comments",
        ordering="_comments_count",
    )
    def comments_count(self, obj):
        return obj._comments_count
    
    
    @action(description="Publish selected")
    def publish_selected(self, request, queryset):
        updated = queryset.update(
            status=Post.Status.PUBLISHED
        )

        self.message_user(
            request,
            f"{updated} posts published successfully.",
            messages.SUCCESS,
        )

    @action(description="Move to drafts")
    def move_to_drafts(self, request, queryset):
        updated = queryset.update(
            status=Post.Status.DRAFT
        )

        self.message_user(
            request,
            f"{updated} posts moved to drafts.",
            messages.SUCCESS,
        )
    
    actions_row = ["toggle_publish"]
    actions_list = ["publish_all_drafts"]
    actions_submit_line = ["save_and_publish"]
    
    @action(
        description="Publish / Unpublish",
        icon="published_with_changes",
    )
    def toggle_publish(self, request, object_id):
        post = self.get_object(request, object_id)

        if post is None:
            self.message_user(
                request,
                "Post not found.",
                messages.ERROR,
            )
        else:
            if post.status == Post.Status.PUBLISHED:
                post.status = Post.Status.DRAFT
            else:
                post.status = Post.Status.PUBLISHED

            post.save(update_fields=["status", "updated_at"])

            self.message_user(
                request,
                "Post status updated successfully.",
                messages.SUCCESS,
            )

        return HttpResponseRedirect(
            reverse("admin:blog_post_changelist")
        )

    @action(
        description="Publish all drafts",
        icon="publish",
    )
    def publish_all_drafts(self, request):
        updated = Post.objects.filter(
            status=Post.Status.DRAFT
        ).update(status=Post.Status.PUBLISHED)

        self.message_user(
            request,
            f"{updated} drafts published successfully.",
            messages.SUCCESS,
        )

        return HttpResponseRedirect(
            reverse("admin:blog_post_changelist")
        )

    @action(
        description="Save & publish",
        icon="check_circle",
    )
    def save_and_publish(self, request, obj):
        obj.status = Post.Status.PUBLISHED
        obj.save(update_fields=["status", "updated_at"])

        self.message_user(
            request,
            "Post saved and published successfully.",
            messages.SUCCESS,
        )

        return HttpResponseRedirect(
            reverse(
                "admin:blog_post_change",
                args=[obj.pk],
            )
        )
        
    fieldsets = (
        (
            "Content",
            {
                "classes": ("tab",),
                "fields": ("title", "slug", "body"),
            },
        ),
        (
            "Classification",
            {
                "classes": ("tab",),
                "fields": ("category", "tags", "status"),
            },
        ),
        (
            "Meta",
            {
                "classes": ("tab",),
                "fields": ("author", "created_at", "updated_at"),
            },
        ),
    )

    readonly_fields = ("created_at", "updated_at")
    warn_unsaved_form = True


COMMENT_PREVIEW_LENGTH = 60


@admin.register(Comment)
class CommentAdmin(ModelAdmin):
    list_display = (
        "post_title",
        "author",
        "short_body",
        "created_at",
    )

    search_fields = (
        "body",
        "author__email",
        "post__title",
    )

    list_filter = [
        ("post", AutocompleteSelectFilter),
        ("author", AutocompleteSelectFilter),
        ("created_at", RangeDateTimeFilter),
    ]

    list_filter_submit = True

    autocomplete_fields = (
        "post",
        "author",
    )

    list_select_related = (
        "post",
        "author",
    )

    @display(description="Post title", ordering="post__title")
    def post_title(self, obj):
        return obj.post.title

    @display(description="Comment")
    def short_body(self, obj):
        if len(obj.body) > COMMENT_PREVIEW_LENGTH:
            return obj.body[:COMMENT_PREVIEW_LENGTH] + "..."
        return obj.body


