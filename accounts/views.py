from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.db.models import Q
from .models import Profile, Notification, Conversation, Message, Post, Comment, Story, StoryView, SavedPost
from .serializers import (
    ProfileSerializer, UserSerializer, NotificationSerializer,
    ConversationSerializer, MessageSerializer, UserRegistrationSerializer,
    PostSerializer, PostCreateSerializer, CommentSerializer,
    StorySerializer, StoryViewSerializer
)


@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(generics.CreateAPIView):
    """User registration endpoint"""
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    authentication_classes = []  # Remove session authentication for this view


class MyProfileView(generics.RetrieveUpdateAPIView):
    """Get and update current user's profile"""
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        # Create profile if it doesn't exist (for OAuth users)
        profile, created = Profile.objects.get_or_create(user=self.request.user)
        return profile
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class ProfileDetailView(generics.RetrieveAPIView):
    """Get any user's profile by username"""
    serializer_class = ProfileSerializer
    permission_classes = [AllowAny]
    lookup_field = 'user__username'
    lookup_url_kwarg = 'username'
    
    def get_queryset(self):
        return Profile.objects.select_related('user').prefetch_related('following', 'followers')
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def follow_user(request, username):
    """Toggle follow/unfollow a user"""
    import logging
    logger = logging.getLogger(__name__)
    
    # Detailed logging for debugging
    logger.error(f"=== FOLLOW REQUEST DEBUG ===")
    logger.error(f"User authenticated: {request.user.is_authenticated}")
    logger.error(f"Current user: {request.user.username if request.user.is_authenticated else 'Anonymous'}")
    logger.error(f"Target username: {username}")
    logger.error(f"Request method: {request.method}")
    logger.error(f"Request headers: {dict(request.headers)}")
    logger.error(f"Request body: {request.body}")
    logger.error(f"=== END DEBUG ===")
    
    # Check authentication first
    if not request.user.is_authenticated:
        logger.error("User not authenticated!")
        return Response(
            {'error': 'Authentication required'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    try:
        target_user = get_object_or_404(User, username=username)
        logger.error(f"Target user found: {target_user.username}")
        
        if target_user == request.user:
            logger.error("User trying to follow themselves")
            return Response(
                {'error': 'You cannot follow yourself'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Ensure both users have profiles
        try:
            profile = request.user.profile
        except Profile.DoesNotExist:
            Profile.objects.create(user=request.user)
            profile = request.user.profile
            
        try:
            target_profile = target_user.profile
        except Profile.DoesNotExist:
            Profile.objects.create(user=target_user)
            target_profile = target_user.profile
        
        logger.error(f"Profile check - Current user profile: {profile.id}, Target profile: {target_profile.id}")
        
        if target_profile in profile.following.all():
            logger.error("User is already following target - unfollowing")
            profile.following.remove(target_profile)
            # Delete follow notification when unfollowing
            Notification.objects.filter(
                recipient=target_user,
                actor=request.user,
                verb='follow'
            ).delete()
            logger.error("Successfully unfollowed")
            return Response({'status': 'unfollowed'}, status=status.HTTP_200_OK)
        else:
            logger.error("User is not following target - following")
            profile.following.add(target_profile)
            # Create follow notification
            Notification.objects.create(
                recipient=target_user,
                actor=request.user,
                verb='follow'
            )
            logger.error("Successfully followed")
            return Response({'status': 'followed'}, status=status.HTTP_200_OK)
            
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in follow_user: {str(e)}, user: {request.user.username}, target: {username}")
        return Response(
            {'error': f'Failed to follow user: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def remove_follower(request, username):
    """Remove a follower from your followers list"""
    follower_user = get_object_or_404(User, username=username)
    
    if follower_user == request.user:
        return Response(
            {'error': 'Invalid operation'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Remove the follower by removing yourself from their following list
    follower_profile = follower_user.profile
    current_profile = request.user.profile
    
    if current_profile in follower_profile.following.all():
        follower_profile.following.remove(current_profile)
        # Delete follow notification
        Notification.objects.filter(
            recipient=request.user,
            actor=follower_user,
            verb='follow'
        ).delete()
        return Response({'status': 'removed'}, status=status.HTTP_200_OK)
    else:
        return Response(
            {'error': 'User is not following you'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def get_followers(request, username):
    """Get list of followers for a user"""
    target_user = get_object_or_404(User, username=username)
    target_profile = target_user.profile
    
    # Get all profiles that are following this user
    followers = target_profile.followers.all()
    
    # Get the User objects from these profiles
    follower_users = [follower.user for follower in followers]
    
    # Serialize with is_following field for current user
    serializer = UserSerializer(follower_users, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_following(request, username):
    """Get list of users that this user is following"""
    target_user = get_object_or_404(User, username=username)
    target_profile = target_user.profile
    
    # Get all profiles that this user is following
    following = target_profile.following.all()
    
    # Get the User objects from these profiles
    following_users = [followed.user for followed in following]
    
    # Serialize with is_following field for current user
    serializer = UserSerializer(following_users, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_users(request):
    """Search users by username"""
    query = request.GET.get('q', '')
    if query:
        users = User.objects.filter(username__icontains=query)[:20]
        serializer = UserSerializer(users, many=True, context={'request': request})
        return Response(serializer.data)
    return Response([])


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_suggestions(request):
    """Get user suggestions for people you might want to follow"""
    current_user = request.user
    current_profile = current_user.profile
    
    # Get users that the current user is already following
    following_profiles = current_profile.following.all()
    following_user_ids = [profile.user.id for profile in following_profiles]
    
    # Exclude current user and users already followed
    exclude_ids = following_user_ids + [current_user.id]
    
    # Get users followed by people you follow (friends of friends)
    suggested_profiles = Profile.objects.filter(
        followers__in=following_profiles
    ).exclude(user__id__in=exclude_ids).distinct()[:10]
    
    # If not enough suggestions, get random users
    if suggested_profiles.count() < 5:
        additional_users = User.objects.exclude(
            id__in=exclude_ids
        ).order_by('?')[:10]
        
        # Combine both suggestion lists
        all_suggestions = list(suggested_profiles.values_list('user', flat=True)) + list(additional_users.values_list('id', flat=True))
        # Remove duplicates and limit
        unique_ids = list(dict.fromkeys(all_suggestions))[:10]
        users = User.objects.filter(id__in=unique_ids)
    else:
        users = [profile.user for profile in suggested_profiles]
    
    serializer = UserSerializer(users, many=True, context={'request': request})
    return Response(serializer.data)


class NotificationListView(generics.ListAPIView):
    """List all notifications for current user"""
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def mark_notifications_read(request):
    """Mark all notifications as read"""
    Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).update(is_read=True)
    return Response({'status': 'success'})


class ConversationListView(generics.ListAPIView):
    """List all conversations for current user"""
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Conversation.objects.filter(participants=self.request.user)
    
    def get_serializer_context(self):
        return {'request': self.request}


class ConversationDetailView(generics.RetrieveAPIView):
    """Get conversation details"""
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Conversation.objects.filter(participants=self.request.user)
    
    def get_serializer_context(self):
        return {'request': self.request}


class MessageListView(generics.ListCreateAPIView):
    """List messages in a conversation and create new messages"""
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        conversation_id = self.kwargs.get('conversation_id')
        return Message.objects.filter(conversation_id=conversation_id)
    
    def list(self, request, *args, **kwargs):
        """Override list to mark messages as read when fetched"""
        response = super().list(request, *args, **kwargs)
        
        # Mark all unread messages in this conversation as read
        conversation_id = self.kwargs.get('conversation_id')
        Message.objects.filter(
            conversation_id=conversation_id,
            is_read=False
        ).exclude(sender=request.user).update(is_read=True)
        
        return response
    
    def perform_create(self, serializer):
        conversation_id = self.kwargs.get('conversation_id')
        conversation = get_object_or_404(Conversation, id=conversation_id)
        
        # Check if user is participant
        if self.request.user not in conversation.participants.all():
            return Response(
                {'error': 'You are not a participant in this conversation'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer.save(
            sender=self.request.user,
            conversation=conversation
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_conversation(request):
    """Create a new conversation with a user"""
    username = request.data.get('username')
    if not username:
        return Response(
            {'error': 'Username is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    other_user = get_object_or_404(User, username=username)
    
    if other_user == request.user:
        return Response(
            {'error': 'You cannot create a conversation with yourself'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if conversation already exists
    existing = Conversation.objects.filter(
        participants=request.user
    ).filter(participants=other_user).first()
    
    if existing:
        serializer = ConversationSerializer(existing, context={'request': request})
        return Response(serializer.data)
    
    # Create new conversation
    conversation = Conversation.objects.create()
    conversation.participants.add(request.user, other_user)
    
    serializer = ConversationSerializer(conversation, context={'request': request})
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@csrf_exempt
@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def password_reset_request(request):
    """Validate username for password reset"""
    username = request.data.get('username')
    
    if not username:
        return Response(
            {'error': 'Username is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user = User.objects.get(username=username)
        return Response({
            'message': 'Username found',
            'username': username,
            'show_password_fields': True
        }, status=status.HTTP_200_OK)
    
    except User.DoesNotExist:
        return Response(
            {'error': 'Username not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@csrf_exempt
@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def password_reset_direct(request):
    """Reset password directly with username and new password"""
    username = request.data.get('username')
    new_password = request.data.get('new_password')
    confirm_password = request.data.get('confirm_password')
    
    if not all([username, new_password, confirm_password]):
        return Response(
            {'error': 'Username, new password, and confirm password are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if new_password != confirm_password:
        return Response(
            {'error': 'Passwords do not match'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if len(new_password) < 8:
        return Response(
            {'error': 'Password must be at least 8 characters long'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user = User.objects.get(username=username)
        user.set_password(new_password)
        user.save()
        
        return Response({
            'message': 'Password reset successful! You can now login with your new password.'
        }, status=status.HTTP_200_OK)
    
    except User.DoesNotExist:
        return Response(
            {'error': 'Username not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@csrf_exempt
@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def password_reset_confirm(request):
    """Confirm password reset with token"""
    uidb64 = request.data.get('uid')
    token = request.data.get('token')
    new_password = request.data.get('new_password')
    
    if not all([uidb64, token, new_password]):
        return Response(
            {'error': 'Missing required fields'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Decode user ID
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        
        # Verify token
        if not default_token_generator.check_token(user, token):
            return Response(
                {'error': 'Invalid or expired token'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Set new password
        user.set_password(new_password)
        user.save()
        
        return Response({'message': 'Password reset successful'}, status=status.HTTP_200_OK)
    
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return Response(
            {'error': 'Invalid reset link'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def get_jwt_token(request):
    """Get JWT token for currently authenticated user (for OAuth users).
    
    This endpoint works with session authentication after OAuth login.
    If the user is not authenticated via session, it will return an error.
    """
    from rest_framework_simplejwt.tokens import RefreshToken
    from django.contrib.auth import authenticate
    import logging
    
    logger = logging.getLogger(__name__)
    logger.info(f"JWT token request - User authenticated: {request.user.is_authenticated}, User: {request.user}, Session key: {request.session.session_key}")
    
    # Check if user is authenticated via session
    if request.user and request.user.is_authenticated:
        refresh = RefreshToken.for_user(request.user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': request.user.id,
                'username': request.user.username,
                'email': request.user.email,
            }
        })
    
    # If not authenticated via session, check if there's a temporary auth token
    temp_token = request.GET.get('temp_token') or request.data.get('temp_token')
    if temp_token:
        # Verify temporary token and get user (COOKIE CLEAR SAFE)
        try:
            from django.core.signing import Signer
            signer = Signer()
            token_data = signer.unsign(temp_token)
            
            # Handle enhanced token format: "user_id:email" or just "user_id"
            if ':' in str(token_data):
                user_id, user_email = str(token_data).split(':', 1)
                # Verify both ID and email for security after cookie clear
                user = User.objects.filter(id=user_id, email=user_email).first()
                logger.info(f"Enhanced token verification: user_id={user_id}, email={user_email}, found={bool(user)}")
            else:
                # Legacy token format (just user_id)
                user_id = token_data
                user = User.objects.get(id=user_id)
                logger.info(f"Legacy token verification: user_id={user_id}, found={bool(user)}")
            
            if user:
                refresh = RefreshToken.for_user(user)
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                    }
                })
        except Exception as e:
            logger.error(f"Temp token verification failed: {e}")
            pass
    
    # Last resort: try to find user by session-stored email and ID
    # This handles the case where OAuth just completed but session isn't working
    try:
        from django.contrib.auth.models import User
        
        oauth_user_id = request.session.get('oauth_user_id')
        oauth_user_email = request.session.get('oauth_user_email')
        
        if oauth_user_id and oauth_user_email:
            # Find user by both ID and email for security
            user = User.objects.filter(id=oauth_user_id, email=oauth_user_email).first()
            if user:
                logger.info(f"Using session-stored user as fallback: {user.id} - {user.email}")
                
                refresh = RefreshToken.for_user(user)
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                    }
                })
    except Exception as e:
        logger.error(f"Session-based user lookup failed: {e}")
    
    return Response(
        {'error': 'User not authenticated. Please login again.'}, 
        status=status.HTTP_401_UNAUTHORIZED
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def logout_view(request):
    """Logout endpoint that clears both session and tokens"""
    from django.contrib.auth import logout
    import logging
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logout request - User: {request.user}, Session key: {request.session.session_key}")
    
    # Clear Django session
    logout(request)
    
    # Clear any OAuth-related session data
    request.session.flush()
    
    logger.info("User logged out successfully")
    return Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def debug_auth_status(request):
    """Debug endpoint to check authentication status"""
    return Response({
        'is_authenticated': request.user.is_authenticated,
        'user_id': request.user.id if request.user.is_authenticated else None,
        'username': request.user.username if request.user.is_authenticated else None,
        'session_key': request.session.session_key,
        'has_session': bool(request.session.session_key),
    })


# Posts Views (merged from posts app)
class PostListCreateView(generics.ListCreateAPIView):
    """List all posts and create new posts"""
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PostCreateSerializer
        return PostSerializer
    
    def get_queryset(self):
        return Post.objects.select_related('author').prefetch_related('likes', 'comments')
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get post details, update caption, and delete post (owner only)"""
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        return Post.objects.select_related('author').prefetch_related('likes', 'comments', 'comments__author')
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def update(self, request, *args, **kwargs):
        post = self.get_object()
        if post.author != request.user:
            return Response(
                {'error': 'You can only edit your own posts'},
                status=status.HTTP_403_FORBIDDEN
            )
        # Only allow updating the caption
        if 'caption' in request.data:
            post.caption = request.data['caption']
            post.save()
            serializer = self.get_serializer(post)
            return Response(serializer.data)
        return Response({'error': 'No caption provided'}, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, *args, **kwargs):
        post = self.get_object()
        if post.author != request.user:
            return Response(
                {'error': 'You can only delete your own posts'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().delete(request, *args, **kwargs)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_like(request, pk):
    """Toggle like on a post"""
    post = get_object_or_404(Post, pk=pk)
    
    if request.user in post.likes.all():
        post.likes.remove(request.user)
        return Response({'status': 'unliked'}, status=status.HTTP_200_OK)
    else:
        post.likes.add(request.user)
        return Response({'status': 'liked'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_save(request, pk):
    """Toggle save on a post"""
    post = get_object_or_404(Post, pk=pk)
    
    # Check if already saved
    saved = SavedPost.objects.filter(user=request.user, post=post).first()
    
    if saved:
        saved.delete()
        return Response({'status': 'unsaved'}, status=status.HTTP_200_OK)
    else:
        SavedPost.objects.create(user=request.user, post=post)
        return Response({'status': 'saved'}, status=status.HTTP_200_OK)


class CommentListCreateView(generics.ListCreateAPIView):
    """List comments for a post and create new comments"""
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        post_id = self.kwargs.get('post_id')
        return Comment.objects.filter(post_id=post_id)
    
    def perform_create(self, serializer):
        post_id = self.kwargs.get('post_id')
        post = get_object_or_404(Post, id=post_id)
        serializer.save(author=self.request.user, post=post)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def feed_view(request):
    """Get feed with posts from followed users"""
    user = request.user
    following_profiles = user.profile.following.all()
    following_users = [profile.user for profile in following_profiles]
    
    # Get posts from followed users
    posts = Post.objects.filter(
        author__in=following_users
    ).select_related('author').prefetch_related('likes', 'comments').order_by('-created_at')
    
    # Paginate manually or use DRF pagination
    page = int(request.GET.get('page', 1))
    page_size = 10
    start = (page - 1) * page_size
    end = start + page_size
    
    paginated_posts = posts[start:end]
    serializer = PostSerializer(
        paginated_posts,
        many=True,
        context={'request': request}
    )
    
    return Response({
        'results': serializer.data,
        'count': posts.count(),
        'page': page
    })


@api_view(['GET'])
@permission_classes([IsAuthenticatedOrReadOnly])
def explore_view(request):
    """Get random/recommended posts for explore page"""
    posts = Post.objects.select_related('author').prefetch_related('likes', 'comments', 'comments__author').order_by('-created_at')[:20]
    serializer = PostSerializer(posts, many=True, context={'request': request})
    return Response(serializer.data)


class StoryListCreateView(generics.ListCreateAPIView):
    """List active stories and create new stories"""
    serializer_class = StorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Get active stories from user, following, and followers
        user = self.request.user
        
        # Get users you follow
        following_profiles = user.profile.following.all()
        following_users = [profile.user for profile in following_profiles]
        
        # Get users who follow you
        follower_profiles = user.profile.followers.all()
        follower_users = [profile.user for profile in follower_profiles]
        
        # Combine both lists
        all_users = set(following_users + follower_users + [user])
        
        return Story.objects.filter(
            user__in=all_users,
            expires_at__gt=timezone.now()
        ).select_related('user', 'user__profile').order_by('-created_at')
    
    def get_serializer_context(self):
        """Pass request context to serializer"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class StoryDetailView(generics.RetrieveDestroyAPIView):
    """Get story details and delete story (owner only)"""
    queryset = Story.objects.all()
    serializer_class = StorySerializer
    permission_classes = [IsAuthenticated]
    
    def retrieve(self, request, *args, **kwargs):
        story = self.get_object()
        
        # Mark as viewed if not owner
        if story.user != request.user:
            StoryView.objects.get_or_create(
                story=story,
                viewer=request.user
            )
        
        serializer = self.get_serializer(story)
        return Response(serializer.data)
    
    def delete(self, request, *args, **kwargs):
        story = self.get_object()
        if story.user != request.user:
            return Response(
                {'error': 'You can only delete your own stories'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().delete(request, *args, **kwargs)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_posts(request, username):
    """Get all posts for a specific user"""
    user = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author=user).order_by('-created_at')
    serializer = PostSerializer(posts, many=True, context={'request': request})
    return Response(serializer.data)
