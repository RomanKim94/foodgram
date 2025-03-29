from io import BytesIO

from django.contrib.auth import get_user_model
from django.db.models import (BooleanField, Exists, F, OuterRef, Prefetch, Sum,
                              Value)
from django.http import FileResponse
from django.urls import reverse
from django.utils import timezone
from django_filters import rest_framework as filterset
from djoser import views
from recipes.models import (Favorite, Follow, Ingredient, Product, Recipe,
                            ShoppingCart, Tag)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from .filters import ProductFilter, RecipeFilter
from .paginators import UserPaginator
from .permissions import IsAuthorOrReadOnly
from .serializers import (AvatarUpdateSerializer, ProductSerializer,
                          RecipeCreateUpdateSerializer,
                          RecipePreviewSerializer, RecipeReadSerializer,
                          SubscriptionSerializer, TagSerializer,
                          UserSerializer)

User = get_user_model()


class UserViewSet(views.UserViewSet):
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
        user = request.user
        author = self.get_object()
        if request.method == 'POST':
            if not (
                isinstance(author, User)
                and user != author
                and not user.follows.filter(follow=author).exists()
            ):
                return Response(status=status.HTTP_400_BAD_REQUEST)
            follow = Follow.objects.create(user=user, follow=author)
            follow.save()
            serializer = SubscriptionSerializer(
                author,
                context={'request': request},
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            if not (
                isinstance(author, User)
                and user != author
                and user.follows.filter(follow=author).exists()
            ):
                return Response(status=status.HTTP_400_BAD_REQUEST)
            Follow.objects.filter(user=user, follow=author).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['GET'],
        serializer_class=SubscriptionSerializer,
        permission_classes=(IsAuthenticated,),
    )
    def subscriptions(self, request):
        follows = User.objects.filter(followers__user=request.user)
        page = self.paginate_queryset(follows)
        serializer = self.get_serializer(
            page,
            many=True,
            context={'request': request},
        )
        return self.get_paginated_response(serializer.data)


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = (AllowAny,)
    pagination_class = None
    filter_backends = (filterset.DjangoFilterBackend,)
    filterset_class = ProductFilter

    def get_queryset(self):
        queryset = super().get_queryset()
        searched_name = self.request.query_params.get('name', None)
        if searched_name:
            queryset = queryset.filter(name__istartswith=searched_name)
        return queryset


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
        else:
            return self.serializer_class

    def annotate_queryset(self, queryset):
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

    def get_queryset(self):
        return self.annotate_queryset(super().get_queryset())

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        recipe = serializer.save(
            author=self.request.user,
        )
        return Response(
            RecipeReadSerializer(self.annotate_queryset(
                Recipe.objects.filter(id=recipe.id)
            ).first()).data,
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        return Response(
            RecipeReadSerializer(self.annotate_queryset(
                Recipe.objects.filter(id=instance.id)
            ).first()).data,
        )

    def get_object(self):
        if 'recipe_id' in self.kwargs:
            self.kwargs['pk'] = self.kwargs['recipe_id']
        return super().get_object()

    @action(
        detail=True,
        methods=['GET'],
        url_path='get-link',
    )
    def get_link(self, request, *args, **kwargs):
        return Response(
            {
                'short-link': request.build_absolute_uri(
                    reverse(
                        'short_link',
                        kwargs={'recipe_id': kwargs['pk']},
                    )
                )
            },
            status=status.HTTP_200_OK,
        )

    def add_recipe_to_collection(self, collection_model, recipe):
        collection_obj, created = collection_model.objects.get_or_create(
            user=self.request.user,
            recipe=recipe,
        )
        if not created:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        collection_obj.save()
        serializer = self.get_serializer(recipe)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    def delete_recipe_from_collection(self, collection_model, recipe):
        collection_object = collection_model.objects.filter(
            user=self.request.user, recipe=recipe,
        ).first()
        if not collection_object:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        collection_object.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def manage_recipe_collection(self, collection_model):
        recipe = self.get_object()
        if self.request.method == 'POST':
            return self.add_recipe_to_collection(
                collection_model=collection_model,
                recipe=recipe,
            )
        elif self.request.method == 'DELETE':
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

        # Формируем список рецептов
        recipes_list = [
            f'{cart.recipe.name} (Автор: {cart.recipe.author.username})'
            for cart in shopping_carts
        ]

        # Получаем ID всех рецептов в корзине
        recipe_ids = shopping_carts.values_list('recipe_id', flat=True)

        # Суммируем продукты
        ingredients_summary = (
            Ingredient.objects
            .filter(recipes__in=recipe_ids)
            .values(
                product_name=F('product__name'),
                unit=F('product__measurement_unit')
            )
            .annotate(total=Sum('amount'))
        )

        # Форматируем результат
        products_dict = {
            (item['product_name'], item['unit']): item['total']
            for item in ingredients_summary
        }
        return (products_dict, recipes_list)

    def generate_ingredients_file_content(self, ingredients, recipes):
        create_time = timezone.now().strftime(
            'Время составления Списка: %H:%M %d.%m.%Y.'
        )
        products = []
        for number, product in enumerate(sorted(
            ingredients.keys(),
            key=lambda product: product[0].lower(),
        )):
            amount = ingredients[product]
            products.append(
                f'{number+1}. '
                f'{product[0].capitalize()}, '
                f'{product[1]} - '
                f'{amount}.'
            )

        return '\n'.join([
            create_time,
            'Необходимо купить следующие продукты:',
            '\n'.join(products),
            'Для блюд:',
            '\n'.join(recipes) + '.',
        ]).encode('utf-8')

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request, *args, **kwargs):
        products, recipes = self.get_combined_ingredients(
            user_id=self.request.user.pk
        )
        file_content = self.generate_ingredients_file_content(
            products, recipes
        )
        return FileResponse(
            BytesIO(file_content),
            as_attachment=True,
            filename='shopping_cart.txt',
            content_type='text/plain; charset=utf-8',
        )
