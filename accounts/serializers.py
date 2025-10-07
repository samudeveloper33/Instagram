from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile, Notification, Conversation, Message


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
                from posts.models import Post
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
