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
        
        COOKIE CLEAR SAFE: This method only creates NEW users and never
        overwrites existing ones, even after cookie clearing.
        """
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"save_user called for sociallogin: {sociallogin.user} (cookie clear safe)")
        
        user = sociallogin.user
        
        # SAFETY CHECK: If this user already has a PK, it means pre_social_login
        # found an existing user and connected it. Don't modify existing users.
        if user.pk:
            logger.info(f"User {user.pk} already exists, skipping save_user modifications")
            # Just ensure session is properly set up for existing user
            try:
                if hasattr(request, 'session') and request.session:
                    request.session['oauth_user_id'] = user.pk
                    request.session['oauth_user_email'] = user.email
                    request.session.save()
            except Exception as e:
                logger.error(f"Error setting up session for existing user: {e}")
            return user
        
        # Generate username from email or Google name (only for NEW users)
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
        
        # Set first and last name from Google data if available (only for NEW users)
        extra_data = sociallogin.account.extra_data
        if not user.first_name and extra_data.get('given_name'):
            user.first_name = extra_data['given_name']
        if not user.last_name and extra_data.get('family_name'):
            user.last_name = extra_data['family_name']
        
        # Save the NEW user
        user.save()
        logger.info(f"Created new user {user.pk} ({user.email}) after cookie clear")
        
        # Create fresh session for the new user
        if user and user.pk:
            login(request, user, backend='allauth.account.auth_backends.AuthenticationBackend')
            
        # Store user ID in fresh session for temp token generation
        if user and user.pk:
            request.session['oauth_user_id'] = user.pk
            request.session['oauth_user_email'] = user.email
            request.session.save()
            logger.info(f"Created fresh session for new user {user.pk} ({user.email})")
        
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
        
        COOKIE CLEAR SAFE: Uses multiple fallback mechanisms to ensure
        proper redirect even when cookies are cleared.
        """
        # Generate a temporary token for JWT generation with multiple fallbacks
        try:
            user_id = None
            user_email = None
            
            # Primary: Get from socialaccount user
            if socialaccount.user and socialaccount.user.id:
                user_id = socialaccount.user.id
                user_email = socialaccount.user.email
            # Fallback 1: Get from session (works after cookie clear if session recreated)
            elif request.session.get('oauth_user_id'):
                user_id = request.session.get('oauth_user_id')
                user_email = request.session.get('oauth_user_email')
            # Fallback 2: Get from authenticated user (if login worked)
            elif request.user and request.user.is_authenticated:
                user_id = request.user.id
                user_email = request.user.email
                
            if user_id:
                from django.core.signing import Signer
                signer = Signer()
                # Include email in token for additional verification
                token_data = f"{user_id}:{user_email}" if user_email else str(user_id)
                temp_token = signer.sign(token_data)
                return f'/oauth-complete?temp_token={temp_token}'
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generating connect redirect token: {e}")
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
        
        This method checks if a user with the same email already exists,
        and if so, connects the social account to that existing user
        instead of creating a new one.
        
        SAFE FOR COOKIE CLEARING: This method ensures existing users are
        never overwritten, even when cookies/sessions are cleared.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Clear any stale session data from previous logins to prevent conflicts
        try:
            if hasattr(request, 'session') and request.session:
                request.session.pop('oauth_user_id', None)
                request.session.pop('oauth_user_email', None)
        except Exception as e:
            logger.error(f"Error clearing session data: {e}")
        
        # Get the email from the social login
        email = sociallogin.user.email
        
        if email:
            try:
                # Check if a user with this email already exists
                existing_user = User.objects.get(email=email)
                
                # If user exists, connect this social account to the existing user
                if existing_user:
                    logger.info(f"Found existing user {existing_user.username} with email {email}. Connecting Google account (cookies cleared safe).")
                    
                    # CRITICAL: Connect the social account to the existing user
                    # This preserves all existing user data (username, password, etc.)
                    sociallogin.user = existing_user
                    
                    # Create fresh session for existing user
                    login(request, existing_user, backend='allauth.account.auth_backends.AuthenticationBackend')
                    
                    # Store user ID in fresh session for temp token generation
                    request.session['oauth_user_id'] = existing_user.pk
                    request.session['oauth_user_email'] = existing_user.email
                    request.session.save()
                    
                    logger.info(f"Successfully connected Google account to existing user {existing_user.username} with fresh session")
                    
            except User.DoesNotExist:
                # No existing user found, proceed with creating a new user
                logger.info(f"No existing user found with email {email}. Will create new user (safe after cookie clear).")
                
                # For new users, ensure they get proper session after creation
                # Note: sociallogin.user.pk will be None here since user isn't saved yet
                # Session setup will happen in save_user method
                pass
                
            except Exception as e:
                logger.error(f"Error in pre_social_login: {e}")
                # Clear any partial session data on error
                try:
                    if hasattr(request, 'session') and request.session:
                        request.session.pop('oauth_user_id', None)
                        request.session.pop('oauth_user_email', None)
                except Exception:
                    pass  # Ignore session errors during error handling
        
        super().pre_social_login(request, sociallogin)
    
    
    def get_login_redirect_url(self, request):
        """
        Returns the default URL to redirect to after a successful login.
        
        COOKIE CLEAR SAFE: Uses multiple fallback mechanisms to ensure
        proper redirect even when cookies are cleared.
        """
        # Generate a temporary token for JWT generation with multiple fallbacks
        try:
            user_id = None
            user_email = None
            
            # Primary: Get from authenticated user
            if request.user and request.user.is_authenticated and request.user.id:
                user_id = request.user.id
                user_email = request.user.email
            # Fallback: Get from session (works after cookie clear if session recreated)
            elif request.session.get('oauth_user_id'):
                user_id = request.session.get('oauth_user_id')
                user_email = request.session.get('oauth_user_email')
                
            if user_id:
                from django.core.signing import Signer
                signer = Signer()
                # Include email in token for additional verification
                token_data = f"{user_id}:{user_email}" if user_email else str(user_id)
                temp_token = signer.sign(token_data)
                return f'/oauth-complete?temp_token={temp_token}'
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generating login redirect token: {e}")
        return '/oauth-complete'
    
