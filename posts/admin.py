from django.contrib import admin
from .models import Post, Comment, Story, StoryView, SavedPost


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('author', 'caption', 'likes_count', 'comments_count', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('author__username', 'caption')
    filter_horizontal = ('likes',)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'post', 'text', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('author__username', 'text')


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'expires_at', 'is_active')
    list_filter = ('created_at',)
    search_fields = ('user__username',)


@admin.register(StoryView)
class StoryViewAdmin(admin.ModelAdmin):
    list_display = ('story', 'viewer', 'viewed_at')
    list_filter = ('viewed_at',)
    search_fields = ('viewer__username',)


@admin.register(SavedPost)
class SavedPostAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'saved_at')
    list_filter = ('saved_at',)
    search_fields = ('user__username', 'post__id')
