#!/usr/bin/env python3
"""
Debug OAuth configuration
"""

import os
import django
from pathlib import Path

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialapp.settings')
django.setup()

from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site
from dotenv import load_dotenv

def debug_oauth():
    """Debug current OAuth configuration"""
    print("🔍 Debugging OAuth Configuration")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    print("📋 Environment Variables:")
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
    
    if client_id:
        print(f"  ✅ GOOGLE_CLIENT_ID: {client_id[:20]}...")
    else:
        print("  ❌ GOOGLE_CLIENT_ID: Not found")
    
    if client_secret:
        print(f"  ✅ GOOGLE_CLIENT_SECRET: {client_secret[:20]}...")
    else:
        print("  ❌ GOOGLE_CLIENT_SECRET: Not found")
    
    print("\n🗄️ Database Configuration:")
    
    # Check Sites
    sites = Site.objects.all()
    print(f"  Sites ({sites.count()}):")
    for site in sites:
        print(f"    - ID: {site.id}, Domain: {site.domain}, Name: {site.name}")
    
    # Check SocialApps
    social_apps = SocialApp.objects.all()
    print(f"\n  Social Apps ({social_apps.count()}):")
    for app in social_apps:
        print(f"    - Provider: {app.provider}")
        print(f"    - Name: {app.name}")
        print(f"    - Client ID: {app.client_id}")
        print(f"    - Secret: {app.secret[:20]}...")
        print(f"    - Sites: {[site.domain for site in app.sites.all()]}")
        print()
    
    print("🔧 Recommended Configuration:")
    print("  Domain should be: localhost:8000 or 127.0.0.1:8000")
    print("  Client ID should match your Google Console")
    print("  Redirect URIs in Google Console should include:")
    print("    - http://127.0.0.1:8000/accounts/google/login/callback/")
    print("    - http://localhost:8000/accounts/google/login/callback/")

def fix_oauth_config():
    """Fix OAuth configuration"""
    print("\n🔧 Fixing OAuth Configuration...")
    
    load_dotenv()
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        print("❌ Missing environment variables")
        return
    
    # Delete existing configurations
    SocialApp.objects.filter(provider='google').delete()
    print("  🗑️ Cleared existing Google OAuth apps")
    
    # Ensure correct site configuration
    site, created = Site.objects.get_or_create(
        pk=1,
        defaults={
            'domain': '127.0.0.1:8000',
            'name': 'Instagram Clone'
        }
    )
    
    if not created:
        site.domain = '127.0.0.1:8000'
        site.name = 'Instagram Clone'
        site.save()
    
    print(f"  ✅ Site configured: {site.domain}")
    
    # Create new Google OAuth app
    google_app = SocialApp.objects.create(
        provider='google',
        name='Google OAuth (Fixed)',
        client_id=client_id,
        secret=client_secret,
    )
    
    # Associate with site
    google_app.sites.add(site)
    
    print(f"  ✅ Created Google OAuth app with real credentials")
    print(f"  ✅ Associated with site: {site.domain}")

if __name__ == "__main__":
    debug_oauth()
    
    print("\n" + "=" * 50)
    response = input("Do you want to fix the OAuth configuration? (y/n): ")
    if response.lower() == 'y':
        fix_oauth_config()
        print("\n✅ OAuth configuration fixed!")
        print("🔄 Please restart your Django server for changes to take effect")
    else:
        print("Configuration not changed.")
