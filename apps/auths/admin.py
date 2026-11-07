from django import forms
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import (
    AdminPasswordChangeForm,
    UserChangeForm,
)
from django.db.models import Count
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import BooleanRadioFilter
from unfold.decorators import action, display

from .models import User


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = "__all__"


class CustomUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput,
    )
    password2 = forms.CharField(
        label="Password confirmation",
        widget=forms.PasswordInput,
    )

    class Meta:
        model = User
        fields = (
            "email",
            "first_name",
            "last_name",
        )

    def clean(self):
        cleaned_data = super().clean()

        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                "Passwords do not match."
            )

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(
            self.cleaned_data["password1"]
        )

        if commit:
            user.save()

        return user


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    change_password_form = AdminPasswordChangeForm

    list_display = (
        "user_header",
        "active_label",
        "staff_label",
        "posts_count",
    )

    list_display_links = ("user_header",)

    list_filter = [
        ("is_active", BooleanRadioFilter),
        ("is_staff", BooleanRadioFilter),
    ]

    list_filter_submit = True

    search_fields = (
        "email",
        "first_name",
        "last_name",
    )

    ordering = ("email",)

    readonly_fields = ("last_login",)

    actions = [
        "activate_users",
        "deactivate_users",
    ]

    fieldsets = (
        (
            "Personal info",
            {
                "classes": ("tab",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "password",
                ),
            },
        ),
        (
            "Permissions",
            {
                "classes": ("tab",),
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (
            "Important dates",
            {
                "classes": ("tab",),
                "fields": (
                    "last_login",
                ),
            },
        ),
    )

    add_fieldsets = (
        (
            "Create user",
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)

        return queryset.annotate(
            _posts_count=Count("posts")
        )

    @display(
        description="User",
        header=True,
    )
    def user_header(self, obj):
        full_name = (
            f"{obj.first_name} {obj.last_name}"
        ).strip()

        return (
            full_name or obj.email,
            obj.email,
        )

    @display(
        description="Active",
        label={
            True: "success",
            False: "danger",
        },
    )
    def active_label(self, obj):
        return (
            obj.
is_active,
            "Active" if obj.is_active else "Inactive",
        )

    @display(
        description="Staff",
        label={
            True: "info",
            False: "warning",
        },
    )
    def staff_label(self, obj):
        return (
            obj.is_staff,
            "Staff" if obj.is_staff else "Regular",
        )

    @display(
        description="Posts",
        ordering="_posts_count",
    )
    def posts_count(self, obj):
        return obj._posts_count

    @action(description="Activate selected users")
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)

        self.message_user(
            request,
            f"{updated} users activated successfully.",
            messages.SUCCESS,
        )

    @action(description="Deactivate selected users")
    def deactivate_users(self, request, queryset):
        updated = queryset.exclude(
            pk=request.user.pk
        ).update(is_active=False)

        self.message_user(
            request,
            f"{updated} users deactivated successfully.",
            messages.SUCCESS,
        )
