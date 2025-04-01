from datetime import datetime
import locale

PRODUCT_IN_SHOPPING_LIST_FORMAT = (
    '{number}. {product_name}, '
    '{measure} - {amount}'
)

try:
    locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'Russian_Russia.1251')
    except locale.Error:
        print(
            "Не удалось установить русскую локаль. "
            "Проверьте доступные локали в системе."
        )


def generate_ingredients_file_content(ingredients, recipes):
    products = [
        PRODUCT_IN_SHOPPING_LIST_FORMAT.format(
            number=number,
            product_name=ingredient['product_name'].capitalize(),
            measure=ingredient['unit'],
            amount=ingredient['total'],
        ) for number, ingredient in enumerate(ingredients, start=1)
    ]

    return '\n'.join([
        datetime.now().strftime(
            'Дата составления списка: %d %B %Y.\n'
            'Время составления списка: %H:%M'
        ),
        'Необходимо купить следующие продукты:',
        *products,
        'Для блюд:',
        *[recipe.name for recipe in recipes],
    ])
