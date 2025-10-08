from django.contrib import admin
from .models import Profile, Notification, Conversation, Message, UserNote, MessageRequest, Post, Comment, Story, StoryView, SavedPost


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'posts_count', 'followers_count', 'following_count', 'created_at')
    search_fields = ('user__username', 'bio')
    list_filter = ('created_at',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'actor', 'verb', 'is_read', 'created_at')
    list_filter = ('verb', 'is_read', 'created_at')
    search_fields = ('recipient__username', 'actor__username')


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at', 'updated_at')
    filter_horizontal = ('participants',)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'conversation', 'text', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('sender__username', 'text')


@admin.register(UserNote)
class UserNoteAdmin(admin.ModelAdmin):
    list_display = ('user', 'text', 'updated_at')
    search_fields = ('user__username', 'text')


@admin.register(MessageRequest)
class MessageRequestAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'conversation', 'is_accepted', 'is_declined', 'created_at')
    list_filter = ('is_accepted', 'is_declined', 'created_at')
    search_fields = ('recipient__username',)


# Posts Admin (merged from posts app)
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
