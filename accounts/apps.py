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
        """Automatically setup OAuth - handles fresh clones and existing setups"""
        from allauth.socialaccount.models import SocialApp
        from django.contrib.sites.models import Site
        from dotenv import load_dotenv
        import os

        # Load environment variables first
        load_dotenv()
        
        # Try to get real credentials from .env
        client_id = os.getenv('GOOGLE_CLIENT_ID')
        client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        
        # Determine what credentials to use
        if client_id and client_secret:
            # Use real credentials from .env
            name = 'Google OAuth'
            use_real_credentials = True
        else:
            # Use test credentials for development
            client_id = 'test_client_id_for_development'
            client_secret = 'test_client_secret_for_development'
            name = 'Google OAuth (Auto-Test)'
            use_real_credentials = False

        # Always ensure site is configured correctly
        site, site_created = Site.objects.get_or_create(
            pk=1,
            defaults={
                'domain': 'localhost:8000',
                'name': 'Instagram Clone'
            }
        )
        
        # Update site if it exists but has wrong domain
        if not site_created and site.domain != 'localhost:8000':
            site.domain = 'localhost:8000'
            site.name = 'Instagram Clone'
            site.save()
            print(f"✅ Updated site domain to: {site.domain}")

        # Check if Google OAuth app exists
        try:
            google_app = SocialApp.objects.get(provider='google')
            
            # Check if existing app needs updating
            needs_update = False
            
            # Update if credentials changed
            if google_app.client_id != client_id or google_app.secret != client_secret:
                google_app.client_id = client_id
                google_app.secret = client_secret
                google_app.name = name
                needs_update = True
            
            # Ensure app is associated with correct site
            if site not in google_app.sites.all():
                google_app.sites.clear()
                google_app.sites.add(site)
                needs_update = True
            
            if needs_update:
                google_app.save()
                print(f"✅ Updated OAuth configuration: {name}")
            else:
                print(f"✅ OAuth already configured: {google_app.name}")
                
        except SocialApp.DoesNotExist:
            # Create new Google OAuth app
            google_app = SocialApp.objects.create(
                provider='google',
                name=name,
                client_id=client_id,
                secret=client_secret,
            )
            
            # Associate with site
            google_app.sites.add(site)
            print(f"✅ Created OAuth configuration: {name}")
        
        # Show helpful message for Git clones
        if not use_real_credentials:
            print("📝 For full OAuth functionality:")
            print("   1. Create .env file in project root")
            print("   2. Add your Google OAuth credentials:")
            print("      GOOGLE_CLIENT_ID=your_client_id")
            print("      GOOGLE_CLIENT_SECRET=your_client_secret")
            print("   3. Restart the server")
            print("   4. Get credentials from: https://console.cloud.google.com/")
