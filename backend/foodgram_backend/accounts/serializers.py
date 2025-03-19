import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField(
        'get_avatar',
        read_only=True,
    )

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed', 'avatar', 'password',
        )
        extra_kwargs = {
            'password': {'write_only': True},
            'id': {'read_only': True},
            'avatar': {'read_only': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user.follows.filter(pk=obj.pk).exists()
        return False

    def get_avatar(self, obj):
        if obj.avatar:
            return obj.avatar.url
        return None


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class AvatarUpdateSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(
        required=True,
        allow_null=False,
        error_messages={
            "required": "Обязательное поле."
        }
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


class RecipeSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    image = serializers.ImageField()
    cooking_time = serializers.IntegerField()


class SubscriptionSerializer(UserSerializer):
    recipes = RecipeSerializer(many=True, read_only=True)
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count')

    def get_recipes_count(self, obj):
        return obj.recipes.count()
