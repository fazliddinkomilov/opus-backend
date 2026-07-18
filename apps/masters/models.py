from django.conf import settings
from django.db import models
from django.utils import timezone


class MasterStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"
    BLOCKED = "blocked", "Blocked"


class ServiceCategory(models.Model):
    slug = models.SlugField(unique=True)
    name_ru = models.CharField(max_length=120)
    name_uz = models.CharField(max_length=120)
    icon = models.CharField(max_length=16, blank=True)
    color_hex = models.CharField(max_length=16, blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=100)

    class Meta:
        ordering = ["sort_order", "name_ru"]
        verbose_name_plural = "service categories"

    def __str__(self) -> str:
        return self.name_ru


class MasterProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="master_profile")
    status = models.CharField(max_length=32, choices=MasterStatus.choices, default=MasterStatus.PENDING)
    bio = models.TextField(blank=True)
    face_photo_url = models.URLField(blank=True)

    activity_points = models.IntegerField(default=400)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    completed_orders_count = models.PositiveIntegerField(default=0)

    is_online = models.BooleanField(default=False)
    current_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    current_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)

    approved_at = models.DateTimeField(null=True, blank=True)
    blocked_at = models.DateTimeField(null=True, blank=True)
    block_reason = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return str(self.user)

    @property
    def is_approved(self) -> bool:
        return self.status == MasterStatus.APPROVED

    def approve(self) -> None:
        self.status = MasterStatus.APPROVED
        self.approved_at = timezone.now()
        self.user.is_master_enabled = True
        self.user.save(update_fields=["is_master_enabled", "updated_at"])
        self.save(update_fields=["status", "approved_at", "updated_at"])


class MasterCategoryPrice(models.Model):
    master = models.ForeignKey(MasterProfile, on_delete=models.CASCADE, related_name="category_prices")
    category = models.ForeignKey(ServiceCategory, on_delete=models.PROTECT, related_name="master_prices")
    min_price_uzs = models.PositiveIntegerField()
    max_price_uzs = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ["master", "category"]
        ordering = ["category__sort_order"]

    def __str__(self) -> str:
        return f"{self.master} / {self.category}: {self.min_price_uzs}-{self.max_price_uzs}"

