from .models import NotificationChannel, NotificationEvent


def create_in_app_notification(user, event_type: str, title: str, body: str = "", payload: dict | None = None):
    return NotificationEvent.objects.create(
        user=user,
        channel=NotificationChannel.IN_APP,
        event_type=event_type,
        title=title,
        body=body,
        payload=payload or {},
    )

