from django_filters import rest_framework as filters

from foodgram_backend.recipes.models import Product, Recipe


class ProductFilter(filters.FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Product
        fields = ('name',)


class RecipeFilter(filters.FilterSet):
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    tags = filters.CharFilter(method='filter_tags')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ('is_favorited', 'author', 'tags', 'is_in_shopping_cart')

    def filter_is_favorited(self, recipes, field_name, value):
        if value:
            return recipes.filter(is_favorited=True)
        return recipes.filter(is_favorited=False)

    def filter_tags(self, recipes, name, value):
        tags = self.request.query_params.getlist('tags')
        if not tags:
            return recipes
        print(tags)
        recipes.prefetch_related('tags__slug')
        return recipes.filter(tags__slug__in=tags).distinct()

    def filter_is_in_shopping_cart(self, recipes, field_name, value):
        if value:
            return recipes.filter(is_in_shopping_cart=True)
        return recipes.filter(is_in_shopping_cart=False)
