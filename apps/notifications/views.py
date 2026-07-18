from rest_framework import viewsets

from .models import NotificationEvent
from .serializers import NotificationEventSerializer


class NotificationEventViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationEventSerializer

    def get_queryset(self):
        queryset = NotificationEvent.objects.select_related("user")
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(user=self.request.user)

