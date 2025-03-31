from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import MinValueValidator
from django.db import models

from .constants import INGREDIENT_AMOUNT_MIN_VALUE, COOKING_TIME_MIN_VALUE


class User(AbstractUser):

    username = models.CharField(
        verbose_name='Никнейм',
        max_length=150,
        unique=True,
        validators=[UnicodeUsernameValidator],
    )
    email = models.EmailField(
        verbose_name='Адрес электронной почты',
        unique=True,
        max_length=254,
    )
    avatar = models.ImageField(
        verbose_name='Аватара',
        upload_to='user/avatar',
        blank=True,
        null=True,
        default=None,
    )
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=150,
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=150,
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def __str__(self):
        return self.username

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class Follow(models.Model):
    follower = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='followers',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='authors',
        verbose_name='Пользователь на которого подписались',
    )


class Tag(models.Model):
    name = models.CharField(
        max_length=32,
        verbose_name='Название',
        unique=True,
    )
    slug = models.SlugField(
        max_length=32,
        verbose_name='Слаг',
        unique=True,
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)


class Product(models.Model):
    name = models.CharField(
        max_length=128,
        verbose_name='Название',
    )
    measurement_unit = models.CharField(
        verbose_name='Единица измерения',
        max_length=64,
    )

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'
        ordering = ('name',)
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='product_unique_constraint'
            )
        ]


class Ingredient(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        verbose_name='Продукт',
    )
    amount = models.IntegerField(
        verbose_name='Количество',
        validators=(
            MinValueValidator(INGREDIENT_AMOUNT_MIN_VALUE),
        )
    )
    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    def __str__(self):
        return f'{self.product} - {self.amount}'

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        default_related_name = 'ingredients'
        ordering = ('product__name',)


class Recipe(models.Model):
    name = models.CharField(
        max_length=256,
        verbose_name='Название',
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        verbose_name='Автор',
    )
    image = models.ImageField(
        upload_to='recipes/image',
        verbose_name='Изображение',
        default='',
    )
    text = models.TextField(
        verbose_name='Описание',
    )
    products = models.ManyToManyField(
        Product,
        verbose_name='Ингридиенты и их количество',
        through=Ingredient
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
    )
    cooking_time = models.IntegerField(
        verbose_name='Время приготовления в минутах',
        validators=(
            MinValueValidator(COOKING_TIME_MIN_VALUE),
        ),
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
        default_related_name = 'recipes'


class CollectionBaseModel(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    def __str__(self):
        return (
            f'Рецепт: {self.recipe}.'
            f'В коллекции "{self._meta.verbose_name}"'
            f'у пользователя: {self.user}.'
        )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='%(class)s_unique_constraint'
            )
        ]
        abstract = True
        default_related_name = '%(class)ss'


class Favorite(CollectionBaseModel):

    class Meta(CollectionBaseModel.Meta):
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'


class ShoppingCart(CollectionBaseModel):

    class Meta(CollectionBaseModel.Meta):
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
