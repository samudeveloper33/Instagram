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
    """Redirect social signup directly to oauth complete"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Social signup redirect - User: {request.user}, Authenticated: {request.user.is_authenticated if hasattr(request.user, 'is_authenticated') else False}, Session oauth_user_id: {request.session.get('oauth_user_id')}")
    
    # Try to generate a temp token if user is authenticated
    try:
        if request.user and request.user.is_authenticated and request.user.id:
            from django.core.signing import Signer
            signer = Signer()
            temp_token = signer.sign(request.user.id)
            logger.info(f"Generated temp token for authenticated user: {request.user.id}")
            return redirect(f'/oauth-complete?temp_token={temp_token}')
        elif request.session.get('oauth_user_id'):
            from django.core.signing import Signer
            signer = Signer()
            temp_token = signer.sign(request.session.get('oauth_user_id'))
            logger.info(f"Generated temp token for session user: {request.session.get('oauth_user_id')}")
            return redirect(f'/oauth-complete?temp_token={temp_token}')
    except Exception as e:
        logger.error(f"Error generating temp token: {e}")
    
    logger.warning("No temp token generated, redirecting to oauth-complete without token")
    return redirect('/oauth-complete')
