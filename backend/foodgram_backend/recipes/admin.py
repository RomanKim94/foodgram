from django.contrib.admin import (
    ModelAdmin, StackedInline, display, register, site
)
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
        return (
            f'<img src="{user.avatar.url}" width="50" '
            'height="50" style="object-fit: cover;" />'
        ) if user.avatar else ''

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
    list_display = ('product', 'amount', 'recipe')


class IngredientInline(StackedInline):
    model = Ingredient
    extra = 1


@register(Recipe)
class RecipeAdmin(ModelAdmin):
    list_display = (
        'id', 'name', 'author', 'cooking_time',
        'recipe_tags', 'ingredients', 'recipe_image',
    )
    readonly_fields = ('favorited_count', )
    search_fields = ('name', 'author__first_name')
    list_filter = (CookingTimeFilter, 'tags', 'author')
    list_display_links = ('name', )
    inlines = [IngredientInline]

    @display(description='В избранном')
    def favorited_count(self, recipe):
        return recipe.favorites.count()

    @display(description='Продукты')
    @mark_safe
    def ingredients(self, recipe):
        return '<br />'.join(
            f'{ingredient.product.name}, '
            f'{ingredient.product.measurement_unit} - '
            f'{ingredient.amount}'
            for ingredient in recipe.ingredients.all(
            )
        )

    @display(description='Теги')
    @mark_safe
    def recipe_tags(self, recipe):
        return '<br />'.join(
            tag.name
            for tag in recipe.tags.all()
        )

    @display(description='Картинка')
    @mark_safe
    def recipe_image(self, recipe):
        return (
            f'<img src="{recipe.image.url}" width="50" '
            'height="50" style="object-fit: cover;" />'
        ) if recipe.image else ''


@register(Favorite, ShoppingCart)
class FavoriteAdmin(ModelAdmin):
    list_display = ('user', 'recipe')
    list_display_links = ('user', )
