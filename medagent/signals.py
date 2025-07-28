"""
Signal handlers for the MedAgent app.

These handlers sanitize messages upon saving if they originate from the owner
and contain profanity. This centralizes profanity filtering so that even
programmatic saves are checked.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from medagent.models import ChatMessage
from medagent.tools import ProfanityCheckTool

@receiver(post_save, sender=ChatMessage)
def sanitize_on_save(sender, instance, created, **kwargs):
    if created and instance.role == "owner":
        if ProfanityCheckTool()._run(instance.content) == "True":
            instance.content = "[پیام حاوی کلمات نامناسب بود]"
            instance.save(update_fields=["content"])
