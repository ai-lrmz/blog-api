from django.contrib import admin
from django.urls import path
from apps.auths.views import RegisterView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from apps.blog.views import (
    CategoryListCreateView,
    CommentDetailView,
    CommentListCreateView,
    PostDetailView,
    PostListCreateView,
    TagListCreateView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/register/", RegisterView.as_view(), name="register"),
    path("api/posts/", PostListCreateView.as_view(), name="post-list-create"),
    path("api/posts/<int:pk>/", PostDetailView.as_view(), name="post-detail"),
    path("api/categories/", CategoryListCreateView.as_view(), name="category-list-create"),
    path("api/tags/", TagListCreateView.as_view(), name="tag-list-create"),
    path("api/comments/", CommentListCreateView.as_view(), name="comment-list-create"),
    path("api/comments/<int:pk>/", CommentDetailView.as_view(), name="comment-detail"),
]