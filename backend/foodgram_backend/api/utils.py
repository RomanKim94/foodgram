from datetime import datetime

PRODUCT_IN_SHOPPING_LIST_FORMAT = (
    '{number}. {product_name}, '
    '{measure} - {amount}'
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
            'Время составления Списка: %H:%M %d.%m.%Y.'
        ),
        'Необходимо купить следующие продукты:',
        *products,
        'Для блюд:',
        *[str(recipe) for recipe in recipes],
    ])
