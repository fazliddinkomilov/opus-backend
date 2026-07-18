from django.conf import settings
from django.db import models


class Review(models.Model):
    order = models.ForeignKey("orders.Order", on_delete=models.CASCADE, related_name="reviews")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="reviews_written")
    target = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="reviews_received")
    rating = models.PositiveSmallIntegerField()
    tags = models.JSONField(default=list, blank=True)
    text = models.TextField(blank=True)
    photo_urls = models.JSONField(default=list, blank=True)
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ["order", "author", "target"]

    def __str__(self) -> str:
        return f"{self.order_id} / {self.author} -> {self.target}: {self.rating}"

