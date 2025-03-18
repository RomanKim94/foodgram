import base64
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
import random
from rest_framework import serializers
import string
from urllib.parse import urljoin

from accounts.serializers import UserSerializer
from recipes import constants as const
from recipes.models import Ingredient, IngredientInRecipe, Recipe, Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientsInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount')

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        ingredient = instance.ingredient
        representation['id'] = ingredient.id
        representation['name'] = ingredient.name
        representation['measurement_unit'] = ingredient.measurement_unit
        return representation

    def create(self, validated_data):
        ingredient_id = validated_data.pop('id')
        ingredient = get_object_or_404(Ingredient, pk=ingredient_id)
        validated_data['ingredient'] = ingredient
        return super().create(validated_data)


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class RecipeSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True,
    )
    author = UserSerializer(read_only=True)
    ingredients = IngredientsInRecipeSerializer(many=True)
    image = Base64ImageField(
        required=True,
        allow_null=False,
        error_messages={
            "required": "Обязательное поле."
        }
    )
    is_favorited = serializers.BooleanField(read_only=True)
    is_in_shopping_cart = serializers.BooleanField(read_only=True)

    REQUIRED_RECIPE_FIELDS = (
        'ingredients', 'tags', 'name', 'text', 'cooking_time'
    )

    class Meta:
        model = Recipe
        fields = (
            'id', 'ingredients', 'tags', 'image',
            'name', 'text', 'cooking_time', 'author',
            'is_favorited', 'is_in_shopping_cart',
        )
        extra_kwargs = {
            'ingredients': {'required': True},
            'tags': {'required': True},
            'name': {'required': True},
            'text': {'required': True},
            'cooking_time': {'required': True},
        }

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['tags'] = TagSerializer(
            instance.tags.all(), many=True,
        ).data
        representation['ingredients'] = IngredientsInRecipeSerializer(
            instance.ingredients.all(), many=True,
        ).data
        return representation

    def create(self, validated_data):
        ingredients_amount_data = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        url_slug = ''.join(random.choices(
            string.ascii_letters + string.digits,
            k=const.URL_SLUG_LENGTH,
        ))
        recipe = Recipe.objects.create(**validated_data, url_slug=url_slug)
        for ingredient_amount_data in ingredients_amount_data:
            ingredient_amount_serializer = IngredientsInRecipeSerializer(
                data=ingredient_amount_data,
            )
            ingredient_amount_serializer.is_valid(raise_exception=True)
            ingredient_amount_obj = ingredient_amount_serializer.save()
            recipe.ingredients.add(ingredient_amount_obj)
        for tag in tags:
            recipe.tags.add(tag)
        return recipe

    def validate(self, attrs):
        missing_fields = []
        for required_field in self.REQUIRED_RECIPE_FIELDS:
            if required_field not in attrs.keys():
                missing_fields.append(required_field)
        if missing_fields:
            raise serializers.ValidationError(
                {field: ["Обязательное поле."] for field in missing_fields}
            )
        return super().validate(attrs)

    def update(self, instance, validated_data):
        for field in self.Meta.fields:
            if field not in ('ingredients', 'tags'):
                setattr(
                    instance, field, validated_data.get(
                        field, getattr(instance, field)
                    )
                )
        if 'ingredients' in validated_data:
            ingredients_data = validated_data.pop('ingredients')
            instance.ingredients.clear()
            for ingredient_data in ingredients_data:
                ingredient_amount_serializer = IngredientsInRecipeSerializer(
                    data=ingredient_data,
                )
                ingredient_amount_serializer.is_valid(raise_exception=True)
                ingredient_amount_obj = ingredient_amount_serializer.save()
                instance.ingredients.add(ingredient_amount_obj)
        if 'tags' in validated_data:
            instance.tags.clear()
            for tag_id in validated_data['tags']:
                instance.tags.add(tag_id)
        instance.save()
        return instance


class RecipePreviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class ShortLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('url_slug', )

    def combine_short_link(self, base_url, url_slug):
        short_link_sign = const.SHORT_LINK_SIGN.strip('/')
        return urljoin(
            base_url,
            f'{short_link_sign}/{url_slug}/',
        )

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['short-link'] = self.combine_short_link(
            base_url=self.context.get('request').build_absolute_uri('/'),
            url_slug=representation.pop('url_slug'),
        )
        return representation
