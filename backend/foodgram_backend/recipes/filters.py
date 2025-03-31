from django.contrib import admin
from django.db.models import Max, Min


class BaseListFilter(admin.SimpleListFilter):
    variants = None
    filter_field = None

    def lookups(self, request, model_admin):
        return self.variants

    def queryset(self, request, queryset):
        if self.value() == 'no':
            return queryset.filter(**{f'{self.filter_field}': True})
        elif self.value() == 'yes':
            return queryset.filter(
                **{f'{self.filter_field}': False}
            ).distinct()
        return queryset


class RecipesExistListFilter(BaseListFilter):
    title = 'Рецепты'
    parameter_name = 'has_recipes'
    variants = [
        ('no', 'Не публиковал'),
        ('yes', 'Публиковал'),
    ]
    filter_field = 'recipes__isnull'


class FollowsExistListFilter(BaseListFilter):
    title = 'Подписки'
    parameter_name = 'has_follows'
    variants = [
        ('no', 'Нет'),
        ('yes', 'Есть'),
    ]
    filter_field = 'follows__isnull'


class FollowersExistListFilter(BaseListFilter):
    title = 'Подписчики'
    parameter_name = 'has_followers'
    variants = [
        ('no', 'Нет'),
        ('yes', 'Есть'),
    ]
    filter_field = 'followers__isnull'


class IsProductInRecipesFilter(BaseListFilter):
    title = 'Есть в рецептах'
    parameter_name = 'is_in_recipes'
    variants = [
        ('no', 'Нет'),
        ('yes', 'Есть')
    ]
    filter_field = 'ingredients__recipes__isnull'


class CookingTimeFilter(admin.SimpleListFilter):
    title = 'Время готовки'
    parameter_name = 'cooking_duration'

    def set_cooking_duration_limits(self, recipes):
        if not recipes:
            return None
        stats = recipes.aggregate(
            min_time=Min('cooking_time'),
            max_time=Max('cooking_time'),
        )
        time_range = stats["max_time"] - stats["min_time"]
        small_duration_limit = stats["min_time"] + time_range // 3
        medium_duration_limit = stats["max_time"] - time_range // 3
        self.limits_values = {
            'fast': (None, small_duration_limit),
            'medium': (small_duration_limit, medium_duration_limit),
            'slow': (medium_duration_limit, None)
        }

    def filter_by_range(self, recipes, keyword):
        minimal, maximum = self.limits_values.get(keyword, (None, None))
        filter_dict = {}
        if minimal:
            filter_dict['cooking_time__gte'] = minimal
        if maximum:
            filter_dict['cooking_time__lt'] = maximum
        return recipes.filter(**filter_dict)

    def lookups(self, request, model_admin):
        recipes = model_admin.get_queryset(request)
        if not recipes.count():
            return None
        self.set_cooking_duration_limits(recipes)
        counts = {}
        counts['fast'] = self.filter_by_range(recipes, 'fast').count()
        counts['medium'] = self.filter_by_range(recipes, 'medium').count()
        counts['slow'] = self.filter_by_range(recipes, 'slow').count()
        result = []
        for k, v in counts.items():
            if v:
                minimal, maximum = self.limits_values[k]
                result.append(
                    (k, (
                        f'От {minimal} минут ' if minimal else ''
                        f'До {maximum} минут' if maximum else ''
                    ))
                )
        return result

    def queryset(self, request, recipes):
        if not self.value():
            return recipes
        return self.filter_by_range(recipes, self.value())
