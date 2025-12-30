from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


@receiver(post_save, sender=User)
def set_staff_since_date(sender, instance, created, **kwargs):
    """Set staff_since date when user becomes active staff."""
    if instance.is_active_staff and not instance.staff_since:
        instance.staff_since = timezone.now()
        # Use update to avoid recursive signal
        User.objects.filter(pk=instance.pk).update(staff_since=instance.staff_since)
