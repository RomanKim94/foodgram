from django.contrib import admin

from recipes import models


@admin.register(models.Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')


@admin.register(models.Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name', )


@admin.register(models.IngredientInRecipe)
class IngredientInRecipeAdmin(admin.ModelAdmin):
    list_display = ('ingredient_name', 'amount')

    def ingredient_name(self, obj):
        return obj.ingredient.name

    ingredient_name.short_description = 'Название ингредиента'


@admin.register(models.Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author')
    readonly_fields = ('favorited_count', )
    search_fields = ('name', 'author__first_name')
    list_filter = ('tags', )
    list_display_links = ('name', )

    def favorited_count(self, obj):
        return obj.favorites.count()

    favorited_count.short_description = 'Количество добавлений в избранное'


@admin.register(models.Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user',)
    list_display_links = ('user', )


@admin.register(models.ShoppingCart)
class ShoppingCartAdmin(FavoriteAdmin):
    pass
