from django.conf import settings
from django.db import models


class NotificationChannel(models.TextChoices):
    PUSH = "push", "Push"
    SMS = "sms", "SMS"
    IN_APP = "in_app", "In-app"
    LOG = "log", "Log"


class NotificationStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SENT = "sent", "Sent"
    FAILED = "failed", "Failed"
    SKIPPED = "skipped", "Skipped"


class NotificationEvent(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notification_events")
    channel = models.CharField(max_length=32, choices=NotificationChannel.choices, default=NotificationChannel.IN_APP)
    event_type = models.CharField(max_length=80)
    title = models.CharField(max_length=180)
    body = models.TextField(blank=True)
    payload = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=32, choices=NotificationStatus.choices, default=NotificationStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.user} / {self.event_type} / {self.status}"

