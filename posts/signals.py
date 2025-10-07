from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver
from .models import Post, Comment
from accounts.models import Notification


@receiver(m2m_changed, sender=Post.likes.through)
def create_like_notification(sender, instance, action, pk_set, **kwargs):
    """Create notification when someone likes a post"""
    if action == 'post_add':
        for user_id in pk_set:
            from django.contrib.auth.models import User
            liker = User.objects.get(pk=user_id)
            if liker != instance.author:
                Notification.objects.create(
                    recipient=instance.author,
                    actor=liker,
                    verb='like',
                    target_type='post',
                    target_id=instance.id
                )


@receiver(post_save, sender=Comment)
def create_comment_notification(sender, instance, created, **kwargs):
    """Create notification when someone comments on a post"""
    if created and instance.author != instance.post.author:
        Notification.objects.create(
            recipient=instance.post.author,
            actor=instance.author,
            verb='comment',
            target_type='post',
            target_id=instance.post.id
        )
