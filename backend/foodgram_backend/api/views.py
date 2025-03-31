from django.contrib.auth import get_user_model
from django.db.models import (BooleanField, Exists, F, OuterRef, Prefetch, Sum,
                              Value)
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django_filters import rest_framework as filterset
from djoser import views
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from ..recipes.models import (Favorite, Follow, Ingredient, Product, Recipe,
                              ShoppingCart, Tag)
from .filters import ProductFilter, RecipeFilter
from .paginators import UserPaginator
from .permissions import IsAuthorOrReadOnly
from .serializers import (AvatarUpdateSerializer, ProductSerializer,
                          RecipeCreateUpdateSerializer,
                          RecipePreviewSerializer, RecipeReadSerializer,
                          SubscriptionSerializer, TagSerializer,
                          UserSerializer)
from .utils import generate_ingredients_file_content

User = get_user_model()


class AccountViewSet(views.UserViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = UserPaginator

    def get_permissions(self):
        if self.action == 'me':
            return (IsAuthenticated(),)
        return super().get_permissions()

    @action(
        detail=False, methods=['PUT', 'DELETE'],
        url_path='me/avatar',
        permission_classes=(IsAuthenticated,),
    )
    def avatar(self, request):
        user = request.user
        if request.method == 'PUT':
            serializer = AvatarUpdateSerializer(user, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        if not user.avatar:
            return Response(status=status.HTTP_404_NOT_FOUND)
        user.avatar.delete()
        user.avatar = None
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True, methods=['POST', 'DELETE'],
        permission_classes=(IsAuthenticated,),
    )
    def subscribe(self, request, **kwargs):
        follower = request.user
        author = self.get_object()
        if not (
            isinstance(author, User)
            and follower != author
            and not follower.followers.filter(author=author).exists()
        ):
            raise ValidationError('Указан невалидный пользователь')
        if request.method == 'POST':
            follow = Follow.objects.create(follower=follower, follow=author)
            follow.save()
            serializer = SubscriptionSerializer(
                author,
                context={'request': request},
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        get_object_or_404(Follow, follower=follower, author=author).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['GET'],
        serializer_class=SubscriptionSerializer,
        permission_classes=(IsAuthenticated,),
    )
    def subscriptions(self, request):
        page = self.paginate_queryset(
            User.objects.filter(followers__follower=request.user)
        )
        return self.get_paginated_response(self.get_serializer(
            page,
            many=True,
            context={'request': request},
        ).data)


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = (AllowAny,)
    pagination_class = None
    filter_backends = (filterset.DjangoFilterBackend,)
    filterset_class = ProductFilter


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class RecipeViewSet(
    viewsets.ModelViewSet
):
    queryset = Recipe.objects.all()
    serializer_class = RecipeCreateUpdateSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)
    filter_backends = (filterset.DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeReadSerializer
        return self.serializer_class

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_authenticated:
            return queryset.annotate(
                is_favorited=Exists(
                    Favorite.objects.filter(
                        user=self.request.user,
                        recipe=OuterRef('pk'),
                    )
                ),
                is_in_shopping_cart=Exists(
                    ShoppingCart.objects.filter(
                        user=self.request.user,
                        recipe=OuterRef('pk'),
                    )
                ),
            )
        return queryset.annotate(
            is_favorited=Value(False, output_field=BooleanField()),
            is_in_shopping_cart=Value(False, output_field=BooleanField()),
        )

    def perform_create(self, serializer):
        serializer.save(
            author=self.request.user,
        )

    @action(
        detail=True,
        methods=['GET'],
        url_path='get-link',
    )
    def get_link(self, request, recipe_id):
        get_object_or_404(Recipe, pk=recipe_id)
        return Response(
            {
                'short-link': request.build_absolute_uri(
                    reverse(
                        'recipes:short_link',
                        args=[recipe_id],
                    )
                )
            },
            status=status.HTTP_200_OK,
        )

    def add_recipe_to_collection(self, collection_model, recipe):
        _, created = collection_model.objects.get_or_create(
            user=self.request.user,
            recipe=recipe,
        )
        if not created:
            raise ValidationError('Указан невалидный рецепт')
        return Response(
            self.get_serializer(recipe).data,
            status=status.HTTP_201_CREATED
        )

    def delete_recipe_from_collection(self, collection_model, recipe):
        get_object_or_404(
            collection_model, user=self.request.user, recipe=recipe
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def manage_recipe_collection(self, collection_model):
        recipe = self.get_object()
        if self.request.method == 'POST':
            return self.add_recipe_to_collection(
                collection_model=collection_model,
                recipe=recipe,
            )
        if self.request.method == 'DELETE':
            return self.delete_recipe_from_collection(
                collection_model=collection_model,
                recipe=recipe,
            )

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        serializer_class=RecipePreviewSerializer,
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, *args, **kwargs):
        return self.manage_recipe_collection(Favorite)

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        serializer_class=RecipePreviewSerializer,
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, *args, **kwargs):
        return self.manage_recipe_collection(ShoppingCart)

    def get_combined_ingredients(self, user_id):
        shopping_carts = (
            ShoppingCart.objects
            .filter(user_id=user_id)
            .select_related('recipe', 'recipe__author')
            .prefetch_related(
                Prefetch(
                    'recipe__ingredients',
                    queryset=Ingredient.objects.select_related('product')
                )
            )
        )
        recipe_ids = shopping_carts.values_list('recipe_id', flat=True)
        ingredients_summary = sorted(
            Ingredient.objects
            .filter(recipes__in=recipe_ids)
            .values(
                product_name=F('product__name'),
                unit=F('product__measurement_unit')
            )
            .annotate(total=Sum('amount')),
            key=lambda product: product['product_name'],
        )
        products_dict = {
            (item['product_name'], item['unit']): item['total']
            for item in ingredients_summary
        }
        return (
            products_dict, [
                f'{cart.recipe.name} (Автор: {cart.recipe.author.username})'
                for cart in shopping_carts
            ]
        )

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request, *args, **kwargs):
        products, recipes = self.get_combined_ingredients(
            user_id=self.request.user.pk
        )
        return FileResponse(
            generate_ingredients_file_content(
                products, recipes
            ),
            as_attachment=True,
            filename='shopping_cart.txt',
            content_type='text/plain; charset=utf-8',
        )
