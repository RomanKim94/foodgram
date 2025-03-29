from django.contrib.admin import ModelAdmin, display, register, site
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.utils.safestring import mark_safe
from recipes.models import (Favorite, Ingredient, Product, Recipe,
                            ShoppingCart, Tag, User)

from .filters import (CookingTimeFilter, FollowersExistListFilter,
                      FollowsExistListFilter, IsProductInRecipesFilter,
                      RecipesExistListFilter)

site.unregister(Group)


@register(User)
class RecipeUserAdmin(UserAdmin):
    list_display = (
        'id',
        'email',
        'avatar_image',
        'username',
        'full_name',
        'recipes_count',
        'followers_count',
        'follows_count',
    )
    search_fields = ('email', 'first_name')
    list_filter = (
        RecipesExistListFilter,
        FollowersExistListFilter,
        FollowsExistListFilter,
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'username',
                'first_name',
                'last_name',
                'password1',
                'password2',
            ),
        }),
    )

    @display(description='ФИО')
    def full_name(self, user):
        return f'{user.first_name} {user.last_name}'.strip()

    @display(description='Аватар')
    @mark_safe
    def avatar_image(self, user):
        if user.avatar:
            return (
                f'<img src="{user.avatar.url}" width="50" '
                'height="50" style="object-fit: cover;" />'
            )
        return 'Нет'

    @display(description='Количество рецептов')
    def recipes_count(self, user):
        return user.recipes.count()

    @display(description='Количество подписчиков')
    def followers_count(self, user):
        return user.followers.count()

    @display(description='Количество подписок')
    def follows_count(self, user):
        return user.follows.count()


class RecipeCountMixin:

    @display(description='Количество рецептов')
    def recipe_count(self, obj):
        return obj.recipes.count()


@register(Tag)
class TagAdmin(RecipeCountMixin, ModelAdmin):
    list_display = ('name', 'slug', 'recipe_count')
    search_fields = ('name', 'slug')
    filter_field = 'tags'


@register(Product)
class ProductAdmin(ModelAdmin):
    list_display = ('name', 'measurement_unit', 'recipe_count')
    search_fields = ('name', 'measurement_unit')
    filter_field = 'measurement_unit'
    list_filter = (IsProductInRecipesFilter, )

    @display(description='Количество рецептов')
    def recipe_count(self, product):
        return Recipe.objects.filter(
            ingredients__product=product
        ).distinct().count()


@register(Ingredient)
class IngredientAdmin(ModelAdmin):
    list_display = ('ingredient_name', 'amount')

    @display(description='Название')
    def ingredient_name(self, ingredient):
        return ingredient.product.name


@register(Recipe)
class RecipeAdmin(ModelAdmin):
    list_display = (
        'id', 'name', 'author', 'cooking_time',
        'recipe_tags', 'products', 'recipe_image',
    )
    readonly_fields = ('favorited_count', )
    search_fields = ('name', 'author__first_name')
    list_filter = (CookingTimeFilter, 'tags', 'author')
    list_display_links = ('name', )

    @display(description='Количество добавлений в избранное')
    def favorited_count(self, recipe):
        return recipe.favorites.count()

    @display(description='Продукты')
    @mark_safe
    def products(self, recipe):
        products = ''.join(
            f'<li>{ingredient.product.name}</li>'
            for ingredient in recipe.ingredients.all(
            ).select_related('product')
        )
        return f'<ul>{products}</ul>'

    @display(description='Теги')
    @mark_safe
    def recipe_tags(self, recipe):
        tags = ''.join(
            f'<li>{tag.name}</li>'
            for tag in recipe.tags.all()
        )
        return f'<ul>{tags}</ul>'

    @display(description='Картинка')
    @mark_safe
    def recipe_image(self, recipe):
        if recipe.image:
            return (
                f'<img src="{recipe.image.url}" width="50" '
                'height="50" style="object-fit: cover;" />'
            )
        return 'Нет'


@register(Favorite, ShoppingCart)
class FavoriteAdmin(ModelAdmin):
    list_display = ('user',)
    list_display_links = ('user', )
