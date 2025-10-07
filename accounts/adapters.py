from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.adapter import DefaultAccountAdapter
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.shortcuts import redirect
import re


class CustomAccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        """
        Allow both manual and social account signup
        """
        return True
    
    def clean_email(self, email):
        """
        Allow multiple accounts with the same email (like Instagram)
        """
        return email


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def save_user(self, request, sociallogin, form=None):
        """
        Saves a newly signed up social login. In case of auto-signup,
        the signup form is not available.
        """
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"save_user called for sociallogin: {sociallogin.user}")
        
        user = sociallogin.user
        
        # Generate username from email or Google name
        if not user.username:
            # Try to get username from Google data
            extra_data = sociallogin.account.extra_data
            
            # First try the email prefix
            if user.email:
                base_username = user.email.split('@')[0]
            # Fallback to Google name
            elif extra_data.get('name'):
                base_username = re.sub(r'[^a-zA-Z0-9_]', '', extra_data['name'].lower())
            else:
                base_username = 'user'
            
            # Ensure username is unique
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            user.username = username
        
        # Set first and last name from Google data if available
        extra_data = sociallogin.account.extra_data
        if not user.first_name and extra_data.get('given_name'):
            user.first_name = extra_data['given_name']
        if not user.last_name and extra_data.get('family_name'):
            user.last_name = extra_data['family_name']
        
        user.save()
        
        # Explicitly log in the user to create a session
        if user and user.pk:
            login(request, user, backend='allauth.account.auth_backends.AuthenticationBackend')
            
        # Store user ID in session for temp token generation
        if user and user.pk:
            request.session['oauth_user_id'] = user.pk
            # Also store email for additional verification
            request.session['oauth_user_email'] = user.email
            request.session.save()
            logger.info(f"Stored user {user.pk} ({user.email}) in session")
        
        return user
    
    def is_auto_signup_allowed(self, request, sociallogin):
        """
        Always allow auto signup for social accounts to bypass the signup form
        """
        return True
    
    def get_connect_redirect_url(self, request, socialaccount):
        """
        Returns the default URL to redirect to after successfully
        connecting a social account.
        """
        # Generate a temporary token for JWT generation since session auth isn't working reliably
        try:
            user_id = None
            if socialaccount.user and socialaccount.user.id:
                user_id = socialaccount.user.id
            elif request.session.get('oauth_user_id'):
                user_id = request.session.get('oauth_user_id')
                
            if user_id:
                from django.core.signing import Signer
                signer = Signer()
                temp_token = signer.sign(user_id)
                return f'/oauth-complete?temp_token={temp_token}'
        except Exception:
            pass
        return '/oauth-complete'
    
    
    def get_signup_form_class(self, request, sociallogin):
        """
        Return None to skip the signup form completely
        """
        return None
    
    def populate_user(self, request, sociallogin, data):
        """
        Populates user information from social provider data
        """
        user = super().populate_user(request, sociallogin, data)
        return user
    
    def authentication_error(self, request, provider_id, error=None, exception=None, extra_context=None):
        """
        Handle authentication errors
        """
        return super().authentication_error(request, provider_id, error, exception, extra_context)
    
    def pre_social_login(self, request, sociallogin):
        """
        Invoked just after a user successfully authenticates via a
        social provider, but before the login is actually processed.
        """
        # For existing users, make sure they get logged in with session
        if sociallogin.user and sociallogin.user.pk:
            login(request, sociallogin.user, backend='allauth.account.auth_backends.AuthenticationBackend')
            # Store user ID in session for temp token generation
            request.session['oauth_user_id'] = sociallogin.user.pk
            request.session['oauth_user_email'] = sociallogin.user.email
            request.session.save()
        
        # Since we allow multiple accounts with same email, 
        # let Django Allauth handle the social login normally
        # without trying to connect to existing users
        super().pre_social_login(request, sociallogin)
    
    
    def get_login_redirect_url(self, request):
        """
        Returns the default URL to redirect to after a successful login.
        """
        # Generate a temporary token for JWT generation since session auth isn't working reliably
        try:
            user_id = None
            if request.user and request.user.is_authenticated and request.user.id:
                user_id = request.user.id
            elif request.session.get('oauth_user_id'):
                user_id = request.session.get('oauth_user_id')
                
            if user_id:
                from django.core.signing import Signer
                signer = Signer()
                temp_token = signer.sign(user_id)
                return f'/oauth-complete?temp_token={temp_token}'
        except Exception:
            pass
        return '/oauth-complete'
    
