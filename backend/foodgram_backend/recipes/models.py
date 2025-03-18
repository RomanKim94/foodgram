from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

from . import constants as const

User = get_user_model()


class BaseModel(models.Model):
    name = models.CharField(
        max_length=const.NAME_MAX_LENGTH,
        verbose_name='Название',
    )

    class Meta:
        abstract = True


class Tag(BaseModel):
    slug = models.SlugField(
        max_length=const.SLUG_MAX_LENGTH,
        unique=True,
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'


class Ingredient(BaseModel):
    measurement_unit = models.CharField(
        verbose_name='Единица измерения',
        max_length=const.MEASURE_MAX_LENGTH,
    )

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'


class IngredientInRecipe(models.Model):
    ingredient = models.ForeignKey(
        'Ingredient',
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
    )
    amount = models.IntegerField(
        verbose_name='Количество в рецепте',
        validators=(
            MinValueValidator(
                const.INGREDIENT_AMOUNT_MIN_VALUE,
                message='Убедитесь, что это значение больше либо равно'
                f'{const.INGREDIENT_AMOUNT_MIN_VALUE}.',
            ),
        )
    )

    def __str__(self):
        return f'{self.ingredient} - {self.amount}'

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'


class Recipe(BaseModel):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор',
    )
    image = models.ImageField(
        upload_to='recipes/image',
        verbose_name='Изображение',
    )
    text = models.TextField(
        verbose_name='Описание',
    )
    ingredients = models.ManyToManyField(
        'IngredientInRecipe',
        verbose_name='Ингридиенты и их количество',
        related_name='recipes',
    )
    tags = models.ManyToManyField(
        'Tag',
        verbose_name='Теги',
    )
    cooking_time = models.IntegerField(
        verbose_name='Время приготовления',
        validators=(
            MinValueValidator(const.COOKING_TIME_MIN_VALUE),
        ),
    )
    url_slug = models.SlugField(
        verbose_name='Слаг для формирования короткой ссылки',
        unique=True,
        blank=True,
        null=True,
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата создания',
        auto_now_add=True,
    )

    def __str__(self):
        return f'Название: {self.name}, Ник автора: {self.author.username}'

    class Meta:
        ordering = ('-pub_date', )
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'


class Favorite(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь'
    )
    recipes = models.ManyToManyField(
        'Recipe',
        related_name='favorites',
        verbose_name='Рецепты'
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'


class ShoppingCart(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь',
    )
    recipes = models.ManyToManyField(
        'Recipe',
        verbose_name='Рецепты',
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
