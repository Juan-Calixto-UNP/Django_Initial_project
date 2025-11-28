from django_db.models.signals import post_save
from django.dispatch import receiver
from .models import PersonaPDP

@receiver(post_save, sender=PersonaPDP)
def sync_personapdp_to_sharepoint(sender, instance, created, **kwargs):
    if created:
        # Logic to create a new item in SharePoint
        sharepoint_id = create_sharepoint_item(instance)
        instance.sharepoint_id = sharepoint_id
        instance.save()
    else:
        # Logic to update the existing item in SharePoint
        if instance.sharepoint_id:
            update_sharepoint_item(instance.sharepoint_id, instance)

