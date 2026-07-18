from rest_framework import serializers

from apps.billing.models import MasterWallet

from .models import MasterCategoryPrice, MasterProfile, ServiceCategory


class ServiceCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceCategory
        fields = ["id", "slug", "name_ru", "name_uz", "icon", "color_hex", "is_active", "sort_order"]


class MasterCategoryPriceSerializer(serializers.ModelSerializer):
    category = ServiceCategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=ServiceCategory.objects.filter(is_active=True),
        source="category",
        write_only=True,
    )

    class Meta:
        model = MasterCategoryPrice
        fields = ["id", "category", "category_id", "min_price_uzs", "max_price_uzs", "is_active"]

    def validate(self, attrs):
        if attrs["min_price_uzs"] > attrs["max_price_uzs"]:
            raise serializers.ValidationError({"price": "min_price_must_be_less_or_equal_max_price"})
        return attrs


class MasterWalletInlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = MasterWallet
        fields = ["balance_uzs", "package_orders_remaining", "free_orders_remaining"]


class MasterProfileSerializer(serializers.ModelSerializer):
    user_phone = serializers.CharField(source="user.phone", read_only=True)
    user_full_name = serializers.CharField(source="user.full_name", read_only=True)
    category_prices = MasterCategoryPriceSerializer(many=True, required=False)
    wallet = MasterWalletInlineSerializer(read_only=True)

    class Meta:
        model = MasterProfile
        fields = [
            "id",
            "user_phone",
            "user_full_name",
            "status",
            "bio",
            "face_photo_url",
            "activity_points",
            "rating",
            "completed_orders_count",
            "is_online",
            "current_latitude",
            "current_longitude",
            "last_seen_at",
            "wallet",
            "category_prices",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "status",
            "activity_points",
            "rating",
            "completed_orders_count",
            "is_online",
            "last_seen_at",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        category_prices = validated_data.pop("category_prices", [])
        validated_data.pop("user", None)
        profile, _ = MasterProfile.objects.update_or_create(
            user=self.context["request"].user,
            defaults=validated_data,
        )
        MasterWallet.objects.get_or_create(master=profile)
        for item in category_prices:
            MasterCategoryPrice.objects.update_or_create(
                master=profile,
                category=item["category"],
                defaults={
                    "min_price_uzs": item["min_price_uzs"],
                    "max_price_uzs": item["max_price_uzs"],
                    "is_active": item.get("is_active", True),
                },
            )
        return profile

    def update(self, instance, validated_data):
        category_prices = validated_data.pop("category_prices", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if category_prices is not None:
            for item in category_prices:
                MasterCategoryPrice.objects.update_or_create(
                    master=instance,
                    category=item["category"],
                    defaults={
                        "min_price_uzs": item["min_price_uzs"],
                        "max_price_uzs": item["max_price_uzs"],
                        "is_active": item.get("is_active", True),
                    },
                )
        return instance


class MasterLocationSerializer(serializers.Serializer):
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6)


class MasterAnalyticsScheduleItemSerializer(serializers.Serializer):
    order_id = serializers.UUIDField()
    category = serializers.CharField()
    scheduled_at = serializers.DateTimeField(allow_null=True)
    status = serializers.CharField()
    amount_uzs = serializers.IntegerField()
    address = serializers.CharField()


class MasterAnalyticsSerializer(serializers.Serializer):
    earned_today_uzs = serializers.IntegerField()
    earned_yesterday_uzs = serializers.IntegerField()
    orders_today = serializers.IntegerField()
    acceptance_rate_percent = serializers.IntegerField()
    rating_avg = serializers.DecimalField(max_digits=3, decimal_places=2)
    total_orders = serializers.IntegerField()
    schedule_today = MasterAnalyticsScheduleItemSerializer(many=True)
