from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

urlpatterns = [
    # Authentication
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/get-jwt-token/', views.get_jwt_token, name='get-jwt-token'),
    path('auth/debug/', views.debug_auth_status, name='debug-auth-status'),
    
    # Profile
    path('profile/me/', views.MyProfileView.as_view(), name='my-profile'),
    path('profile/<str:username>/', views.ProfileDetailView.as_view(), name='profile-detail'),
    path('profile/<str:username>/follow/', views.follow_user, name='follow-user'),
    path('profile/<str:username>/remove-follower/', views.remove_follower, name='remove-follower'),
    path('profile/<str:username>/followers/', views.get_followers, name='get-followers'),
    path('profile/<str:username>/following/', views.get_following, name='get-following'),
    
    # Search
    path('search/', views.search_users, name='search-users'),
    path('suggestions/', views.get_suggestions, name='get-suggestions'),
    
    # Notifications
    path('notifications/', views.NotificationListView.as_view(), name='notifications'),
    path('notifications/read/', views.mark_notifications_read, name='mark-notifications-read'),
    
    # Password Reset
    path('password-reset/', views.password_reset_request, name='password-reset-request'),
    path('password-reset-direct/', views.password_reset_direct, name='password-reset-direct'),
    path('password-reset-confirm/', views.password_reset_confirm, name='password-reset-confirm'),
    
    # Conversations & Messages
    path('conversations/', views.ConversationListView.as_view(), name='conversations'),
    path('conversations/create/', views.create_conversation, name='create-conversation'),
    path('conversations/<int:pk>/', views.ConversationDetailView.as_view(), name='conversation-detail'),
    path('conversations/<int:conversation_id>/messages/', views.MessageListView.as_view(), name='messages'),
]
