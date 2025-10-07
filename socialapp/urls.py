from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts.template_views import (
    index_view, login_view, register_view, profile_view, explore_view,
    messages_view, notifications_view, post_detail_view, reset_password_view,
    oauth_complete_view, social_signup_redirect,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/', include('accounts.urls')),
    path('api/', include('posts.urls')),
    
    # Custom social signup redirect (must be before allauth.urls)
    path('accounts/3rdparty/signup/', social_signup_redirect, name='social-signup-redirect'),
    
    # Social authentication (Google OAuth)
    path('accounts/', include('allauth.urls')),
    
    # Frontend pages
    path('', index_view, name='index'),
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('explore/', explore_view, name='explore'),
    path('messages/', messages_view, name='messages'),
    path('notifications/', notifications_view, name='notifications'),
    path('post/<int:post_id>/', post_detail_view, name='post-detail'),
    path('profile/', profile_view, name='my-profile-page'),
    path('profile/<str:username>/', profile_view, name='profile-page'),
    path('reset-password/<str:uid>/<str:token>/', reset_password_view, name='reset-password'),
    path('oauth-complete/', oauth_complete_view, name='oauth-complete'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
