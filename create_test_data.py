#!/usr/bin/env python3
"""
Create test data for Instagram Clone
Creates a test user and posts for demonstration
"""

import os
import django
from pathlib import Path

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialapp.settings')
django.setup()

from django.contrib.auth.models import User
from posts.models import Post
from accounts.models import Profile

def create_test_user():
    """Create a test user"""
    print("👤 Creating test user...")
    
    # Create or get test user
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
    )
    
    if created:
        user.set_password('testpass123')
        user.save()
        print("  ✅ Created new test user: testuser")
    else:
        print("  ✅ Test user already exists: testuser")
    
    # Create or get profile
    profile, created = Profile.objects.get_or_create(user=user)
    if created:
        print("  ✅ Created profile for test user")
    
    return user

def create_test_posts(user, count=3):
    """Create test posts"""
    print(f"📝 Creating {count} test posts...")
    
    captions = [
        "Welcome to my Instagram clone! 🚀 This is my first post.",
        "Beautiful sunset today 🌅 #nature #photography",
        "Testing the post functionality 📱 Everything works great!"
    ]
    
    posts_created = 0
    for i in range(count):
        caption = captions[i] if i < len(captions) else f"Test post #{i+1}"
        
        # Check if post with this caption already exists
        if not Post.objects.filter(author=user, caption=caption).exists():
            post = Post.objects.create(
                author=user,
                caption=caption
            )
            print(f"  ✅ Created post {i+1}: {caption[:50]}...")
            posts_created += 1
        else:
            print(f"  ⚠️  Post {i+1} already exists")
    
    return posts_created

def display_stats():
    """Display current database stats"""
    print("\n📊 Database Statistics:")
    print(f"  - Users: {User.objects.count()}")
    print(f"  - Profiles: {Profile.objects.count()}")
    print(f"  - Posts: {Post.objects.count()}")
    
    # Show recent posts
    recent_posts = Post.objects.select_related('author').order_by('-created_at')[:5]
    if recent_posts:
        print(f"\n📋 Recent Posts:")
        for post in recent_posts:
            print(f"  - {post.author.username}: {post.caption[:50]}...")

def main():
    """Create test data"""
    print("🧪 Creating Test Data for Instagram Clone")
    print("=" * 50)
    
    try:
        # Create test user
        user = create_test_user()
        
        # Create test posts
        posts_created = create_test_posts(user)
        
        # Display stats
        display_stats()
        
        print("\n" + "=" * 50)
        print("🎉 Test Data Creation Complete!")
        
        if posts_created > 0:
            print(f"\n✅ Created {posts_created} new posts")
            print("📝 You can now:")
            print("  1. Visit /api/explore/ to see posts")
            print("  2. Login with Google OAuth to interact with posts")
            print("  3. Test the API endpoints with authentication")
        
    except Exception as e:
        print(f"❌ Error creating test data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
