# Generated by Django 4.2.20 on 2025-03-15 01:52

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0006_auto_20250313_2121'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ingredientinrecipe',
            name='amount',
            field=models.IntegerField(validators=[django.core.validators.MinValueValidator(0, message='Убедитесь, что это значение больше либо равно0.')], verbose_name='Количество в рецепте'),
        ),
    ]
