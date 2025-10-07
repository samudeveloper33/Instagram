from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q
from .models import Post, Comment, Story, StoryView, SavedPost
from .serializers import (
    PostSerializer, PostCreateSerializer, CommentSerializer,
    StorySerializer, StoryViewSerializer
)


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
    from django.contrib.auth.models import User
    user = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author=user).order_by('-created_at')
    serializer = PostSerializer(posts, many=True, context={'request': request})
    return Response(serializer.data)
