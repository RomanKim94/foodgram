from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer as DjoserUserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import Ingredient, Product, Recipe, Tag

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

    def get_is_subscribed(self, user):
        request = self.context.get('request')
        return bool(
            request
            and request.user.is_authenticated
            and request.user.follows.filter(follow=user).exists()
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
        extra_kwargs = {field: {'read_only': True} for field in fields}


class SubscriptionSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source='recipes.count',
        read_only=True
    )

    class Meta(UserSerializer.Meta):
        fields = (*UserSerializer.Meta.fields, 'recipes', 'recipes_count')

    def get_recipes(self, user):
        recipes_limit = self.context.get(
            'request'
        ).query_params.get('recipes_limit')
        try:
            recipes_limit = int(recipes_limit)
        except (ValueError, TypeError):
            recipes_limit = None
        recipes = user.recipes.all()[:recipes_limit]
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
    id = serializers.IntegerField(source='product.id')

    class Meta:
        model = Ingredient
        fields = ('id', 'amount',)


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
    image = Base64ImageField()
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


class RecipeCreateUpdateSerializer(RecipeReadSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    image = Base64ImageField(
        required=True,
        allow_null=False,
        error_messages={
            "required": "Обязательное поле."
        },
    )
    ingredients = IngredientWriteSerializer(many=True)

    REQUIRED_RECIPE_FIELDS = (
        'ingredients', 'tags', 'name', 'text', 'cooking_time',
    )

    class Meta(RecipeReadSerializer.Meta):
        fields = (
            'ingredients', 'tags', 'image',
            'name', 'text', 'cooking_time', 'author',
        )

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError(
                "Изображение не может быть пустым."
            )
        return value

    def validate_field_values(self, model, ids, field_name):
        len_ids = len(ids)
        if len_ids == 0:
            raise serializers.ValidationError(
                {field_name: f'{model._meta.verbose_name_plural} не указаны'}
            )
        if len(set(ids)) != len_ids:
            raise serializers.ValidationError(
                {field_name: 'Указаны дублирующиеся '
                 f'{model._meta.verbose_name_plural}'}
            )
        exist_objects_count = model.objects.filter(
            id__in=ids
        ).count()
        if len_ids != exist_objects_count:
            raise serializers.ValidationError(
                {field_name: 'Указан несуществующий '
                 f'{model._meta.verbose_name_plural}'}
            )

    def validate(self, attrs):
        missing_fields = []
        for required_field in self.REQUIRED_RECIPE_FIELDS:
            if required_field not in attrs.keys():
                missing_fields.append(required_field)
        if missing_fields:
            raise serializers.ValidationError(
                {field: ["Обязательное поле."] for field in missing_fields}
            )
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
            ingredients.append(
                Ingredient.objects.get_or_create(
                    product=Product.objects.get(
                        id=ingredient['product']['id']
                    ),
                    amount=ingredient['amount'],
                )[0].pk
            )
        recipe.ingredients.set(ingredients)

    def update(self, instance: Recipe, validated_data):
        for field in self.Meta.fields:
            if field not in ('ingredients', 'tags'):
                setattr(
                    instance, field, validated_data.get(
                        field, getattr(instance, field)
                    )
                )
        if 'ingredients' in validated_data:
            instance.ingredients.clear()
            self.set_ingredients(
                instance,
                ingredients_data=validated_data.pop('ingredients')
            )
        if 'tags' in validated_data:
            instance.tags.clear()
            tags = validated_data.pop('tags')
            instance.tags.set(tags)
        instance = super().update(
            instance,
            validated_data,
        )
        return instance

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        recipe = super().create(validated_data)
        self.set_ingredients(
            recipe,
            ingredients_data=ingredients_data,
        )
        for tag in tags:
            recipe.tags.set(tags)
        return recipe
