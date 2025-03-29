from django.contrib import admin
from django.db.models import Count, Q
from django_filters import rest_framework as filters
from recipes.models import Product, Recipe

from .constants import (MEDIUM_COOKING_DURATION_LIMIT,
                        SMALL_COOKING_DURATION_LIMIT)


class RecipesExistListFilter(admin.SimpleListFilter):
    title = 'Рецепты'
    parameter_name = 'has_recipes'

    def lookups(self, request, model_admin):
        return [
            ('no', 'Не публиковал'),
            ('yes', 'Публиковал'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'no':
            return queryset.filter(recipes__isnull=True)
        elif self.value() == 'yes':
            return queryset.filter(recipes__isnull=False).distinct()
        return queryset


class FollowsExistListFilter(admin.SimpleListFilter):
    title = 'Подписки'
    parameter_name = 'has_follows'

    def lookups(self, request, model_admin):
        return [
            ('no', 'Нет'),
            ('yes', 'Есть'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'no':
            return queryset.filter(follows__isnull=True)
        elif self.value() == 'yes':
            return queryset.filter(follows__isnull=False).distinct()
        return queryset


class FollowersExistListFilter(admin.SimpleListFilter):
    title = 'Подписчики'
    parameter_name = 'has_followers'

    def lookups(self, request, model_admin):
        return [
            ('no', 'Нет'),
            ('yes', 'Есть'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'no':
            return queryset.filter(followers__isnull=True)
        elif self.value() == 'yes':
            return queryset.filter(followers__isnull=False).distinct()
        return queryset


class IsProductInRecipesFilter(admin.SimpleListFilter):
    title = 'Есть в рецептах'
    parameter_name = 'is_in_recipes'

    def lookups(self, request, model_admin):
        return [
            ('no', 'Нет'),
            ('yes', 'Есть')
        ]

    def queryset(self, request, queryset):
        if self.value() == 'no':
            return queryset.filter(
                ingredients__recipes__isnull=False
            )
        if self.value() == 'yes':
            return queryset.filter(
                ingredients__recipes__isnull=True
            ).distinct()
        return queryset


class CookingTimeFilter(admin.SimpleListFilter):
    title = 'Время готовки'
    parameter_name = 'cooking_duration'

    def lookups(self, request, model_admin):
        queryset = model_admin.get_queryset(request)
        counts = queryset.aggregate(
            fast=Count(
                'id',
                filter=Q(cooking_time__lte=SMALL_COOKING_DURATION_LIMIT),
            ),
            medium=Count('id', filter=Q(
                cooking_time__gt=SMALL_COOKING_DURATION_LIMIT,
                cooking_time__lte=MEDIUM_COOKING_DURATION_LIMIT,
            )),
            slow=Count(
                'id',
                filter=Q(cooking_time__gt=MEDIUM_COOKING_DURATION_LIMIT),
            ),
        )

        return [
            ('fast', (
                f'Не больше {SMALL_COOKING_DURATION_LIMIT}минут '
                f'({counts["fast"]})'
            )),
            ('medium', (
                f'Не больше {MEDIUM_COOKING_DURATION_LIMIT} минут '
                f'({counts["medium"]})'
            )),
            ('slow', (
                f'Больше {MEDIUM_COOKING_DURATION_LIMIT} минут '
                f'({counts["slow"]})'
            )),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'fast':
            return queryset.objects.filter(
                cooking_time__lte=SMALL_COOKING_DURATION_LIMIT
            )
        elif self.value() == 'medium':
            return queryset.objects.filter(
                cooking_time__gt=SMALL_COOKING_DURATION_LIMIT,
                cooking_time__lte=MEDIUM_COOKING_DURATION_LIMIT,
            )
        elif self.value() == 'slow':
            return queryset.objects.filter(
                cooking_time__gt=MEDIUM_COOKING_DURATION_LIMIT,
            )
        return queryset


class ProductFilter(filters.FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Product
        fields = ('name',)


class RecipeFilter(filters.FilterSet):
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    tags = tags = filters.CharFilter(method='filter_tags')
    is_in_shopping_cart = filters.BooleanFilter(method='filter_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ('is_favorited', 'author', 'tags', 'is_in_shopping_cart')

    def filter_is_favorited(self, queryset, field_name, value):
        if value:
            return queryset.filter(is_favorited=True)
        else:
            return queryset.filter(is_favorited=False)

    def filter_tags(self, queryset, name, value):
        tags = self.request.query_params.getlist('tags')
        if tags:
            q_objects = Q()
            for tag_slug in tags:
                q_objects |= Q(tags__slug=tag_slug)
            return queryset.filter(q_objects).distinct()
        return queryset
    
    def filter_is_in_shopping_cart(self, queryset, field_name, value):
        if value:
            return queryset.filter(is_in_shopping_cart=True)
        else:
            return queryset.filter(is_in_shopping_cart=False)
