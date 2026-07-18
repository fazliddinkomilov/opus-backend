from rest_framework import response, status, viewsets

from apps.orders.models import Order

from .models import Review
from .serializers import ReviewSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer

    def get_queryset(self):
        queryset = Review.objects.select_related("order", "author", "target")
        if self.request.user.is_staff:
            return queryset
        return (queryset.filter(author=self.request.user) | queryset.filter(target=self.request.user, is_public=True)).distinct()

    def create(self, request, *args, **kwargs):
        order = Order.objects.select_related("client", "master__user").filter(id=request.data.get("order")).first()
        if order is None:
            return response.Response({"code": "order_not_found"}, status=status.HTTP_404_NOT_FOUND)
        if order.client_id == request.user.id and order.master_id:
            target = order.master.user
            is_public = True
        elif order.master and order.master.user_id == request.user.id:
            target = order.client
            is_public = False
        else:
            return response.Response({"code": "forbidden"}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review = serializer.save(author=request.user, target=target, is_public=is_public)
        return response.Response({"review": self.get_serializer(review).data}, status=status.HTTP_201_CREATED)
