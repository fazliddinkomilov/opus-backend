from rest_framework import serializers

from .models import NotificationEvent


class NotificationEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationEvent
        fields = ["id", "channel", "event_type", "title", "body", "payload", "status", "created_at", "sent_at"]

