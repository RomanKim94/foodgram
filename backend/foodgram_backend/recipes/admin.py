from django.contrib.admin import ModelAdmin, display, register, site
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.utils.safestring import mark_safe

from .filters import (CookingTimeFilter, FollowersExistListFilter,
                      FollowsExistListFilter, IsProductInRecipesFilter,
                      RecipesExistListFilter)
from .models import (Favorite, Ingredient, Product, Recipe, ShoppingCart, Tag,
                     User)

site.unregister(Group)


class RecipeCountMixin:

    @display(description='Рецептов')
    def recipes_count(self, obj):
        return obj.recipes.count()


@register(User)
class RecipeUserAdmin(RecipeCountMixin, UserAdmin):
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
        return ''

    @display(description='Подписчиков')
    def followers_count(self, author):
        return author.authors.count()

    @display(description='Подписок')
    def follows_count(self, follower):
        return follower.followers.count()


@register(Tag)
class TagAdmin(RecipeCountMixin, ModelAdmin):
    list_display = ('name', 'slug', 'recipes_count')
    search_fields = ('name', 'slug')
    filter_field = 'tags'


@register(Product)
class ProductAdmin(RecipeCountMixin, ModelAdmin):
    list_display = ('name', 'measurement_unit', 'recipes_count')
    search_fields = ('name', 'measurement_unit')
    filter_field = 'measurement_unit'
    list_filter = (IsProductInRecipesFilter, )


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
        return '<p>' + ''.join(
            f'{ingredient.product.name}, '
            f'{ingredient.product.measurement_unit} - '
            f'{ingredient.amount}<br />'
            for ingredient in recipe.ingredients.all(
            ).select_related('product')
        ) + '</p>'

    @display(description='Теги')
    @mark_safe
    def recipe_tags(self, recipe):
        return '<p>' + ''.join(
            f'<li>{tag.name}</li>'
            for tag in recipe.tags.all()
        ) + '</p>'

    @display(description='Картинка')
    @mark_safe
    def recipe_image(self, recipe):
        if recipe.image:
            return (
                f'<img src="{recipe.image.url}" width="50" '
                'height="50" style="object-fit: cover;" />'
            )
        return ''


@register(Favorite, ShoppingCart)
class FavoriteAdmin(ModelAdmin):
    list_display = ('user', 'recipe')
    list_display_links = ('user', )
