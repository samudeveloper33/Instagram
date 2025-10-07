from rest_framework import serializers
from .models import Post, Comment, Story, StoryView, SavedPost
from accounts.serializers import UserSerializer


class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    author_username = serializers.CharField(source='author.username', read_only=True)
    author_avatar = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = ('id', 'post', 'author', 'author_username', 'author_avatar', 
                  'text', 'created_at')
        read_only_fields = ('post', 'author', 'created_at')
    
    def get_author_avatar(self, obj):
        """Safely get author avatar URL"""
        try:
            if hasattr(obj.author, 'profile') and obj.author.profile.avatar:
                return obj.author.profile.avatar.url
        except:
            pass
        return None


class PostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    author_username = serializers.CharField(source='author.username', read_only=True)
    author_avatar = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()
    comments = CommentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Post
        fields = ('id', 'author', 'author_username', 'author_avatar', 'image', 'video',
                  'caption', 'likes_count', 'comments_count', 'is_liked', 'is_saved',
                  'comments', 'created_at', 'updated_at')
        read_only_fields = ('author', 'created_at', 'updated_at')
    
    def get_author_avatar(self, obj):
        """Safely get author avatar URL"""
        try:
            if hasattr(obj.author, 'profile') and obj.author.profile.avatar:
                return obj.author.profile.avatar.url
        except:
            pass
        return None
    
    def get_likes_count(self, obj):
        return obj.likes.count()
    
    def get_comments_count(self, obj):
        return obj.comments.count()
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user in obj.likes.all()
        return False
    
    def get_is_saved(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return SavedPost.objects.filter(user=request.user, post=obj).exists()
        return False


class PostCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ('image', 'video', 'caption')
    
    def validate(self, data):
        """Ensure either image or video is provided, but not both"""
        image = data.get('image')
        video = data.get('video')
        
        if not image and not video:
            raise serializers.ValidationError("Either image or video is required")
        
        if image and video:
            raise serializers.ValidationError("Cannot upload both image and video")
        
        return data


class StorySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    user_avatar = serializers.SerializerMethodField()
    is_active = serializers.BooleanField(read_only=True)
    is_viewed = serializers.SerializerMethodField()
    views_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Story
        fields = ('id', 'user', 'username', 'user_avatar', 'image', 'video',
                  'is_active', 'is_viewed', 'views_count', 'created_at', 'expires_at')
        read_only_fields = ('user', 'created_at', 'expires_at')
    
    def get_user_avatar(self, obj):
        """Safely get user avatar URL"""
        try:
            if hasattr(obj.user, 'profile') and obj.user.profile.avatar:
                return obj.user.profile.avatar.url
        except:
            pass
        return None
    
    def get_is_viewed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return StoryView.objects.filter(story=obj, viewer=request.user).exists()
        return False
    
    def get_views_count(self, obj):
        """Get the number of views for this story"""
        return obj.views.count()


class StoryViewSerializer(serializers.ModelSerializer):
    viewer = UserSerializer(read_only=True)
    
    class Meta:
        model = StoryView
        fields = ('id', 'story', 'viewer', 'viewed_at')
        read_only_fields = ('viewer', 'viewed_at')
