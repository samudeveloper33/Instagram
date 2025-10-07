from django.urls import path
from . import views

urlpatterns = [
    # Posts
    path('posts/', views.PostListCreateView.as_view(), name='post-list-create'),
    path('posts/<int:pk>/', views.PostDetailView.as_view(), name='post-detail'),
    path('posts/<int:pk>/like/', views.toggle_like, name='toggle-like'),
    path('posts/<int:pk>/save/', views.toggle_save, name='toggle-save'),
    path('posts/<int:post_id>/comments/', views.CommentListCreateView.as_view(), name='post-comments'),
    path('posts/user/<str:username>/', views.user_posts, name='user-posts'),
    
    # Feed & Explore
    path('feed/', views.feed_view, name='feed'),
    path('explore/', views.explore_view, name='explore'),
    
    # Stories
    path('stories/', views.StoryListCreateView.as_view(), name='story-list-create'),
    path('stories/<int:pk>/', views.StoryDetailView.as_view(), name='story-detail'),
]
