from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile, Notification, Conversation, Message, Post, Comment, Story, StoryView, SavedPost


class UserSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'profile', 'is_following')
    
    def get_profile(self, obj):
        if hasattr(obj, 'profile'):
            return {
                'avatar': obj.profile.avatar.url if obj.profile.avatar else None,
                'bio': obj.profile.bio
            }
        return None
    
    def get_is_following(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.profile in request.user.profile.following.all()
        return False


class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    user = serializers.SerializerMethodField()
    posts_count = serializers.IntegerField(read_only=True)
    followers_count = serializers.IntegerField(read_only=True)
    following_count = serializers.IntegerField(read_only=True)
    is_following = serializers.SerializerMethodField()
    
    class Meta:
        model = Profile
        fields = ('id', 'user', 'username', 'email', 'avatar', 'bio', 'website',
                  'posts_count', 'followers_count', 'following_count', 'is_following',
                  'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')
    
    def get_user(self, obj):
        """Return user data"""
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'email': obj.user.email
        }
    
    def get_is_following(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj in request.user.profile.following.all()
        return False
    


class NotificationSerializer(serializers.ModelSerializer):
    actor_username = serializers.CharField(source='actor.username', read_only=True)
    actor_avatar = serializers.ImageField(source='actor.profile.avatar', read_only=True)
    target_image = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = ('id', 'actor', 'actor_username', 'actor_avatar', 'verb', 
                  'target_type', 'target_id', 'target_image', 'is_read', 'created_at')
        read_only_fields = ('actor', 'verb', 'target_type', 'target_id', 'created_at')
    
    def get_target_image(self, obj):
        """Get the image URL for the notification target"""
        try:
            if obj.target_type == 'post' and obj.target_id:
                post = Post.objects.get(id=obj.target_id)
                if post.image:
                    return post.image.url
            elif obj.verb == 'follow':
                # For follow notifications, return actor's avatar
                if hasattr(obj.actor, 'profile') and obj.actor.profile.avatar:
                    return obj.actor.profile.avatar.url
        except Exception:
            pass
        return None


class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    timestamp = serializers.DateTimeField(source='created_at', read_only=True)
    
    class Meta:
        model = Message
        fields = ('id', 'conversation', 'sender', 'text', 'is_read', 'timestamp', 'created_at')
        read_only_fields = ('sender', 'conversation', 'created_at', 'timestamp')


class ConversationSerializer(serializers.ModelSerializer):
    participants = serializers.SerializerMethodField()
    last_message = MessageSerializer(read_only=True)
    other_user = serializers.SerializerMethodField()
    current_user_id = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = ('id', 'participants', 'last_message', 'other_user', 'current_user_id', 'unread_count', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')
    
    def get_participants(self, obj):
        request = self.context.get('request')
        return UserSerializer(obj.participants.all(), many=True, context={'request': request}).data
    
    def get_other_user(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            participants = obj.participants.exclude(id=request.user.id)
            if participants.exists():
                return UserSerializer(participants.first(), context={'request': request}).data
        return None
    
    def get_current_user_id(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user.id
        return None
    
    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.unread_count(request.user)
        return 0


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={'input_type': 'password'}, min_length=8)
    password2 = serializers.CharField(write_only=True, style={'input_type': 'password'}, min_length=8)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2', 'first_name', 'last_name')
    
    def validate_username(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("Username must be at least 3 characters long")
        
        # Check if username already exists (must be unique)
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists")
        
        return value
    
    def validate_email(self, value):
        # Allow multiple accounts with the same email (like real Instagram)
        return value
    
    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError("Passwords don't match")
        if len(data['password']) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long")
        return data
    
    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user


# Posts Serializers (merged from posts app)
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
