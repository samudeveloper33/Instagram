from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        """Auto-setup OAuth when Django starts"""
        try:
            self.setup_oauth_if_needed()
        except Exception:
            # Ignore errors during startup (like during migrations)
            pass

    def setup_oauth_if_needed(self):
        """Automatically setup OAuth if not already configured"""
        from allauth.socialaccount.models import SocialApp
        from django.contrib.sites.models import Site
        from dotenv import load_dotenv
        import os

        # Check if Google OAuth app already exists
        try:
            SocialApp.objects.get(provider='google')
            return  # Already configured
        except SocialApp.DoesNotExist:
            pass

        # Load environment variables
        load_dotenv()
        
        # Try to get real credentials first
        client_id = os.getenv('GOOGLE_CLIENT_ID')
        client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        
        if client_id and client_secret:
            # Use real credentials
            name = 'Google OAuth'
        else:
            # Use test credentials
            client_id = 'test_client_id_for_development'
            client_secret = 'test_client_secret_for_development'
            name = 'Google OAuth (Auto-Test)'

        # Get or create the default site
        site, created = Site.objects.get_or_create(
            pk=1,
            defaults={
                'domain': 'localhost:8000',
                'name': 'Instagram Clone'
            }
        )

        # Create Google OAuth app
        google_app = SocialApp.objects.create(
            provider='google',
            name=name,
            client_id=client_id,
            secret=client_secret,
        )

        # Associate with site
        google_app.sites.add(site)
        
        print(f"✅ Auto-configured OAuth: {name}")
