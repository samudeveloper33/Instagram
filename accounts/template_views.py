from django.shortcuts import render, redirect
from django.views.generic import TemplateView


def index_view(request):
    """Render the feed/home page"""
    return render(request, 'index.html')


def login_view(request):
    """Render the login/register page"""
    return render(request, 'login.html')


def register_view(request):
    """Render the registration page"""
    return render(request, 'register.html')


def profile_view(request, username=None):
    """Render the profile page"""
    return render(request, 'profile.html', {'username': username})


def explore_view(request):
    """Render the explore page"""
    return render(request, 'explore.html')


def messages_view(request):
    """Render the messages page"""
    return render(request, 'messages.html')


def notifications_view(request):
    """Redirect to home page - notifications now work as a side panel"""
    return redirect('/')


def post_detail_view(request, post_id):
    """Render the post detail page"""
    return render(request, 'post_detail.html', {'post_id': post_id})


def reset_password_view(request, uid, token):
    """Render the password reset confirmation page"""
    return render(request, 'reset_password.html', {'uid': uid, 'token': token})


def oauth_complete_view(request):
    """Render the OAuth completion page which swaps session for JWT tokens."""
    return render(request, 'oauth_complete.html')


def social_signup_redirect(request):
    """Redirect social signup directly to oauth complete (COOKIE CLEAR SAFE)"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Social signup redirect - User: {request.user}, Authenticated: {request.user.is_authenticated if hasattr(request.user, 'is_authenticated') else False}, Session oauth_user_id: {request.session.get('oauth_user_id')}")
    
    # Try to generate a temp token if user is authenticated (with enhanced format)
    try:
        user_id = None
        user_email = None
        
        # Primary: Get from authenticated user
        if request.user and request.user.is_authenticated and request.user.id:
            user_id = request.user.id
            user_email = request.user.email
            logger.info(f"Using authenticated user: {user_id} ({user_email})")
        # Fallback: Get from session (works after cookie clear if session recreated)
        elif request.session.get('oauth_user_id'):
            user_id = request.session.get('oauth_user_id')
            user_email = request.session.get('oauth_user_email')
            logger.info(f"Using session user: {user_id} ({user_email})")
            
        if user_id:
            from django.core.signing import Signer
            signer = Signer()
            # Use enhanced token format with email for additional security
            token_data = f"{user_id}:{user_email}" if user_email else str(user_id)
            temp_token = signer.sign(token_data)
            logger.info(f"Generated enhanced temp token for user: {user_id}")
            return redirect(f'/oauth-complete?temp_token={temp_token}')
            
    except Exception as e:
        logger.error(f"Error generating temp token: {e}")
    
    logger.warning("No temp token generated, redirecting to oauth-complete without token")
    return redirect('/oauth-complete')
