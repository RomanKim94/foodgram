from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    email = models.EmailField(
        verbose_name='Адрес электронной почты',
        unique=True,
    )
    follows = models.ManyToManyField(
        to='self',
        verbose_name='Подписки',
        blank=True,
    )
    avatar = models.ImageField(
        verbose_name='Аватара',
        upload_to='user/avatar',
        blank=True,
        null=True,
        default=None,
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.first_name
