from rest_framework.response import Response
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model

from accounts.paginators import UserCustomPaginator
from accounts.serializers import (
    AvatarUpdateSerializer,
    SubscriptionSerializer, UserSerializer,
)


User = get_user_model()


class UserViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = UserCustomPaginator
    permission_classes = (AllowAny,)

    def get_current_user(self):
        return self.request.user

    def get_permissions(self):
        if self.action == 'avatar':
            return [IsAuthenticated()]
        return super().get_permissions()

    @action(
        detail=False, methods=['PUT', 'DELETE'],
        url_path='me/avatar',
        permission_classes=(IsAuthenticated,),
    )
    def avatar(self, request):
        user = self.get_current_user()
        if request.method == 'PUT':
            serializer = AvatarUpdateSerializer(user, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST,
            )
        elif request.method == 'DELETE':
            if not user.avatar:
                return Response(status=status.HTTP_404_NOT_FOUND)
            user.avatar.delete()
            user.avatar = None
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

    def is_subscribe_valid(self, another_user):
        user = self.get_current_user()
        return (
            another_user
            and user != another_user
            and not user.follows.filter(pk=another_user.pk).exists()
        )

    def is_unsubscribe_valid(self, another_user):
        user = self.get_current_user()
        return (
            another_user
            and user != another_user
            and user.follows.filter(pk=another_user.pk).exists()
        )

    @action(
        detail=True, methods=['POST', 'DELETE'],
        permission_classes=(IsAuthenticated,),
    )
    def subscribe(self, request, **kwargs):
        user = self.get_current_user()
        author = self.get_object()
        if (
            request.method == 'POST'
            and self.is_subscribe_valid(author)
        ):
            user.follows.add(author)
            serializer = UserSerializer(
                author,
                context={'request': request},
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif (
            request.method == 'DELETE'
            and self.is_unsubscribe_valid(author)
        ):
            user.follows.remove(author)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=['GET'],
        serializer_class=SubscriptionSerializer,
        permission_classes=(IsAuthenticated,),
    )
    def subscriptions(self, request):
        user = User.objects.prefetch_related('follows').get(pk=request.user.pk)
        follows = user.follows.all()
        page = self.paginate_queryset(follows)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        return Response(
            self.get_serializer(follows, many=True).data,
            status=status.HTTP_200_OK
        )
