from distutils.util import strtobool
from io import BytesIO

from django.db.models import (
    BooleanField, Exists, OuterRef, Q, Value, prefetch_related_objects
)
from django.http import FileResponse
from django.shortcuts import get_object_or_404

from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response

from .models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from .permissions import IsAuthor
from .serializers import (
    IngredientSerializer, RecipePreviewSerializer, RecipeSerializer,
    ShortLinkSerializer, TagSerializer
)


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    pagination_class = None

    def get_queryset(self):
        queryset = super().get_queryset()
        searched_name = self.request.query_params.get('name', None)
        if searched_name:
            queryset = queryset.filter(name__istartswith=searched_name)
        return queryset


class TagViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class RecipeViewSet(
    viewsets.ModelViewSet
):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthor)

    def filter_queryset(self, queryset):
        for parameter, value in self.request.query_params.items():
            if parameter in ('is_favorited', 'is_in_shopping_cart'):
                queryset = queryset.filter(**{parameter: strtobool(value)})
            if parameter == 'author':
                queryset = queryset.filter(author__id=value)
            if parameter == 'tags':
                tags = self.request.query_params.getlist(parameter)
                tag_conditions = Q()
                for tag in tags:
                    tag_conditions |= Q(tags__slug=tag)
                queryset = queryset.filter(tag_conditions).distinct()

        return super().filter_queryset(queryset)

    def annotate_queryset(self, queryset):
        if self.request.user.is_authenticated:
            return queryset.annotate(
                is_favorited=Exists(
                    Favorite.objects.filter(
                        user=self.request.user,
                        recipes=OuterRef('pk'),
                    )
                ),
                is_in_shopping_cart=Exists(
                    ShoppingCart.objects.filter(
                        user=self.request.user,
                        recipes=OuterRef('pk'),
                    )
                ),
            )
        return queryset.annotate(
            is_favorited=Value(False, output_field=BooleanField()),
            is_in_shopping_cart=Value(False, output_field=BooleanField()),
        )

    def get_queryset(self):
        return self.annotate_queryset(super().get_queryset())

    def perform_create(self, serializer):
        serializer.save(
            author=self.request.user,
        )

    def retrieve(self, request, *args, **kwargs):
        if 'pk' in kwargs:
            return super().retrieve(request, *args, **kwargs)
        elif 'url_slug' in kwargs:
            instance = get_object_or_404(Recipe, url_slug=kwargs['url_slug'])
            prefetch_related_objects([instance], 'ingredients', 'tags')
            serializer = self.get_serializer(instance)
            return Response(serializer.data)

    @action(
        detail=True,
        methods=['GET'],
        url_path='get-link',
        serializer_class=ShortLinkSerializer,
    )
    def get_link(self, request, *args, **kwargs):
        recipe = self.get_object()
        serializer = self.get_serializer(recipe)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def add_recipe_to_collection(self, collection_model, recipe):
        collection_obj, _ = collection_model.objects.get_or_create(
            user=self.request.user,
        )
        if not collection_obj.recipes.filter(pk=recipe.pk).exists():
            collection_obj.recipes.add(recipe)
            serializer = self.get_serializer(recipe)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

    def delete_recipe_from_collection(self, collection_model, recipe):
        collection_obj = get_object_or_404(
            collection_model,
            user=self.request.user,
        )
        if collection_obj.recipes.filter(pk=recipe.pk).exists():
            collection_obj.recipes.remove(recipe)
            return Response(status=status.HTTP_204_NO_CONTENT)

    def manage_recipe_collection(self, collection_model):
        recipe = self.get_object()
        if self.request.method == 'POST':
            response = self.add_recipe_to_collection(
                collection_model=collection_model,
                recipe=recipe,
            )
        elif self.request.method == 'DELETE':
            response = self.delete_recipe_from_collection(
                collection_model=collection_model,
                recipe=recipe,
            )
        return response or Response(status=status.HTTP_400_BAD_REQUEST)

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

    def get_combined_ingredients(self, shopping_cart):
        prefetch_related_objects(
            [shopping_cart],
            'recipes__ingredients__ingredient',
        )
        combined_ingredients = dict()
        for recipe in shopping_cart.recipes.all():
            for recipe_ingredient in recipe.ingredients.all():
                key = (
                    recipe_ingredient.ingredient.name,
                    recipe_ingredient.ingredient.measurement_unit,
                )
                combined_ingredients[key] = (
                    combined_ingredients.get(key, 0)
                    + recipe_ingredient.amount
                )
        return [
            (
                name, unit, amount
            ) for (name, unit), amount in combined_ingredients.items()
        ]

    def generate_ingredients_file_content(self, combined_ingredients):
        file_content = ''
        for name, measurement_unit, amount in combined_ingredients:
            file_content += f'{name} - {amount} {measurement_unit}\n'
        return file_content

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request, *args, **kwargs):
        file_content = self.generate_ingredients_file_content(
            self.get_combined_ingredients(
                shopping_cart=self.request.user.shopping_cart
            )
        )
        binary_file = file_content.encode('utf-8')
        return FileResponse(
            BytesIO(binary_file),
            as_attachment=True,
            filename='shopping_cart.txt',
        )
