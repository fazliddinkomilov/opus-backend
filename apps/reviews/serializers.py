from rest_framework import serializers

from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.full_name", read_only=True)
    target_name = serializers.CharField(source="target.full_name", read_only=True)

    class Meta:
        model = Review
        fields = [
            "id",
            "order",
            "author",
            "author_name",
            "target",
            "target_name",
            "rating",
            "tags",
            "text",
            "photo_urls",
            "is_public",
            "created_at",
        ]
        read_only_fields = ["id", "author", "author_name", "target", "target_name", "is_public", "created_at"]

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("rating_must_be_between_1_and_5")
        return value
