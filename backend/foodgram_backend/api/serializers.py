from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer as DjoserUserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from ..recipes.models import Ingredient, Product, Recipe, Tag

User = get_user_model()


class UserSerializer(DjoserUserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField(
        'get_avatar',
        read_only=True,
    )

    class Meta:
        model = User
        fields = (*DjoserUserSerializer.Meta.fields, 'is_subscribed', 'avatar')

    def get_is_subscribed(self, author):
        request = self.context.get('request')
        return (
            request.user.is_authenticated
            and request.user.followers.filter(author=author).exists()
        )

    def get_avatar(self, user):
        if user.avatar:
            return user.avatar.url
        return None


class AvatarUpdateSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(
        required=True,
        allow_null=False,
    )

    class Meta:
        model = User
        fields = ('avatar', )

    def update(self, instance, validated_data):
        if instance.avatar:
            instance.avatar.delete()
        instance.avatar = validated_data['avatar']
        instance.save()
        return instance


class RecipePreviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = fields


class SubscriptionSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source='recipes.count',
        read_only=True
    )

    class Meta(UserSerializer.Meta):
        fields = (*UserSerializer.Meta.fields, 'recipes', 'recipes_count')

    def get_recipes(self, author):
        recipes_limit = self.context.get(
            'request'
        ).GET.get('recipes_limit', 10**10)
        try:
            recipes_limit = int(recipes_limit)
        except (ValueError, TypeError):
            recipes_limit = 10**10
        recipes = author.recipes.all()[:recipes_limit]
        return RecipePreviewSerializer(recipes, many=True).data


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'


class IngredientWriteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()

    class Meta:
        model = Ingredient
        fields = ('id', 'amount')

    def validate(self, attrs):
        if not Product.objects.filter(id=attrs['id']).exists():
            raise serializers.ValidationError(
                'Указанного продукта не существует.'
            )
        if attrs['amount'] < 1:
            raise serializers.ValidationError(
                'Укажите значение больше 0'
            )
        return super().validate(attrs)


class IngredientReadSerializer(IngredientWriteSerializer):
    id = serializers.IntegerField(source='product.id')
    name = serializers.CharField(source='product.name')
    measurement_unit = serializers.CharField(source='product.measurement_unit')

    class Meta:
        model = Ingredient
        fields = ('id', 'amount', 'name', 'measurement_unit')


class RecipeReadSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    ingredients = IngredientReadSerializer(many=True)
    is_favorited = serializers.BooleanField(read_only=True)
    is_in_shopping_cart = serializers.BooleanField(read_only=True)
    tags = TagSerializer(many=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'ingredients', 'tags', 'image',
            'name', 'text', 'cooking_time', 'author',
            'is_favorited', 'is_in_shopping_cart',
        )
        read_only_fields = fields


class RecipeCreateUpdateSerializer(RecipeReadSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    image = Base64ImageField(
        required=True,
        allow_null=False,
    )
    ingredients = IngredientWriteSerializer(many=True)
    cooking_time = serializers.IntegerField(min_value=1)

    class Meta():
        model = Recipe
        fields = (
            'ingredients', 'tags', 'image',
            'name', 'text', 'cooking_time', 'author',
        )

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError(
                'Изображение не может быть пустым.'
            )
        return value

    def validate_field_values(self, model, ids, field_name):
        len_ids = len(ids)
        if not len_ids:
            raise serializers.ValidationError(
                {field_name: f'{model._meta.verbose_name_plural} не указаны'}
            )
        if len(set(ids)) != len_ids:
            raise serializers.ValidationError(
                {field_name: 'Указаны дублирующиеся '
                 f'{model._meta.verbose_name_plural}'}
            )

    def validate(self, attrs):
        ingredient_ids = [
            i.get('product').get('id') for i in attrs['ingredients']
        ]
        tags_ids = [i.id for i in attrs['tags']]
        self.validate_field_values(Product, ingredient_ids, 'ingredients')
        self.validate_field_values(Tag, tags_ids, 'tags')
        return super().validate(attrs)

    def set_ingredients(self, recipe, ingredients_data):
        ingredients = []
        for ingredient in ingredients_data:
            ingredients.append(Ingredient(
                product_id=ingredient['product']['id'],
                amount=ingredient['amount'],
            ))
        ingredients = Recipe.objects.bulk_create(ingredients)
        recipe.ingredients.set(ingredients)

    def update(self, instance: Recipe, validated_data):
        for field in self.Meta.fields:
            if field not in ('ingredients', 'tags'):
                setattr(
                    instance, field, validated_data.get(
                        field, getattr(instance, field)
                    )
                )
        instance.ingredients.clear()
        self.set_ingredients(
            instance,
            ingredients_data=validated_data.pop('ingredients')
        )
        instance.tags.clear()
        tags = validated_data.pop('tags')
        instance.tags.set(tags)
        return super().update(
            instance,
            validated_data,
        )

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        recipe = super().create(validated_data)
        self.set_ingredients(
            recipe,
            ingredients_data=ingredients_data,
        )
        recipe.tags.set(tags)
        return recipe
