#!/usr/bin/env python3
"""
Check the exact redirect URI being used
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialapp.settings')
django.setup()

from django.contrib.sites.models import Site
from allauth.socialaccount.providers.google.provider import GoogleProvider
from allauth.socialaccount import providers

def check_redirect_uri():
    """Check what redirect URI is being generated"""
    print("🔍 Checking Redirect URI Configuration")
    print("=" * 50)
    
    # Get current site
    try:
        site = Site.objects.get(pk=1)
        print(f"📍 Current Site:")
        print(f"  - ID: {site.id}")
        print(f"  - Domain: {site.domain}")
        print(f"  - Name: {site.name}")
    except Site.DoesNotExist:
        print("❌ No site found with ID 1")
        return
    
    # Check what redirect URI would be generated
    provider = GoogleProvider(None)
    
    print(f"\n🔗 Expected Redirect URI:")
    print(f"  - http://{site.domain}/accounts/google/login/callback/")
    print(f"  - https://{site.domain}/accounts/google/login/callback/")
    
    print(f"\n✅ Your Google Console should have these redirect URIs:")
    print(f"  - http://127.0.0.1:8000/accounts/google/login/callback/")
    print(f"  - http://localhost:8000/accounts/google/login/callback/")
    print(f"  - https://127.0.0.1:8000/accounts/google/login/callback/")
    print(f"  - https://localhost:8000/accounts/google/login/callback/")
    
    print(f"\n🔧 If you're getting 400 errors, check that ALL these URIs are added to your Google Console")

if __name__ == "__main__":
    check_redirect_uri()
