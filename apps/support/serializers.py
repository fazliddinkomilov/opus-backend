from rest_framework import serializers

from .models import SupportCase, SupportMessage


class SupportMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source="sender.full_name", read_only=True)

    class Meta:
        model = SupportMessage
        fields = ["id", "case", "sender", "sender_name", "text", "created_at"]
        read_only_fields = ["id", "sender", "sender_name", "created_at"]


class SupportCaseSerializer(serializers.ModelSerializer):
    messages = SupportMessageSerializer(many=True, read_only=True)

    class Meta:
        model = SupportCase
        fields = [
            "id",
            "user",
            "order",
            "status",
            "priority",
            "subject",
            "body",
            "assigned_to",
            "messages",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "status", "assigned_to", "messages", "created_at", "updated_at"]


class SupportMessageCreateSerializer(serializers.Serializer):
    text = serializers.CharField()

