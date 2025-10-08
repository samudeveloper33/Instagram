#!/usr/bin/env python3
"""
Test script for Instagram Clone functionality
Tests authentication and post creation
"""

import requests
import json
import os
from pathlib import Path

# Base URL for the API
BASE_URL = "http://127.0.0.1:8000"

def test_authentication():
    """Test authentication endpoints"""
    print("🔐 Testing Authentication...")
    
    # Test debug endpoint
    response = requests.get(f"{BASE_URL}/api/auth/debug/")
    print(f"Debug Auth Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  - Authenticated: {data.get('is_authenticated')}")
        print(f"  - User ID: {data.get('user_id')}")
        print(f"  - Username: {data.get('username')}")
        print(f"  - Has Session: {data.get('has_session')}")
    
    # Test profile endpoint (should be 401 if not authenticated)
    response = requests.get(f"{BASE_URL}/api/profile/me/")
    print(f"Profile Access: {response.status_code}")
    if response.status_code == 401:
        print("  ✅ Correctly returns 401 when not authenticated")
    elif response.status_code == 200:
        print("  ✅ User is authenticated!")
        data = response.json()
        print(f"  - Username: {data.get('username')}")
        return True
    
    return False

def test_posts_read():
    """Test reading posts (should work without authentication)"""
    print("\n📖 Testing Posts Read Access...")
    
    # Test explore endpoint (should work without auth)
    response = requests.get(f"{BASE_URL}/api/explore/")
    print(f"Explore Posts: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  ✅ Found {len(data)} posts in explore")
        return True
    else:
        print(f"  ❌ Error: {response.text}")
        return False

def test_posts_write():
    """Test creating posts (requires authentication)"""
    print("\n✍️ Testing Post Creation...")
    
    # Test creating a post without authentication
    post_data = {
        "caption": "Test post from API script! 🚀",
    }
    
    response = requests.post(f"{BASE_URL}/api/posts/", json=post_data)
    print(f"Create Post (no auth): {response.status_code}")
    
    if response.status_code == 401:
        print("  ✅ Correctly requires authentication for post creation")
        return False
    elif response.status_code == 201:
        print("  ✅ Post created successfully!")
        data = response.json()
        print(f"  - Post ID: {data.get('id')}")
        print(f"  - Caption: {data.get('caption')}")
        return True
    else:
        print(f"  ❌ Unexpected response: {response.text}")
        return False

def test_oauth_flow():
    """Test OAuth flow information"""
    print("\n🔗 OAuth Flow Information...")
    print(f"  1. Visit: {BASE_URL}/login/")
    print(f"  2. Click 'Login with Google'")
    print(f"  3. Complete Google authentication")
    print(f"  4. Get JWT token: {BASE_URL}/api/auth/get-jwt-token/")
    print(f"  5. Use JWT token in Authorization header for API calls")

def main():
    """Run all tests"""
    print("🧪 Instagram Clone API Test Suite")
    print("=" * 50)
    
    try:
        # Test if server is running
        response = requests.get(f"{BASE_URL}/")
        if response.status_code != 200:
            print("❌ Server is not running or not accessible")
            return
        print("✅ Server is running")
        
        # Run tests
        is_authenticated = test_authentication()
        test_posts_read()
        
        if is_authenticated:
            test_posts_write()
        else:
            print("\n⚠️  Not authenticated - skipping write tests")
            test_oauth_flow()
        
        print("\n" + "=" * 50)
        print("🎉 Test Suite Complete!")
        
        if not is_authenticated:
            print("\n📝 Next Steps:")
            print("1. Complete Google OAuth login in browser")
            print("2. Run this script again to test authenticated features")
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure Django is running on port 8000")
    except Exception as e:
        print(f"❌ Error running tests: {e}")

if __name__ == "__main__":
    main()
