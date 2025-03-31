from datetime import timezone

PRODUCT_IN_SHOPPING_LIST_FORMAT = (
    '{number}. {product_name}, '
    '{measure} - {amount}'
)


def generate_ingredients_file_content(ingredients, recipes):
    products = [
        PRODUCT_IN_SHOPPING_LIST_FORMAT.format(
            number=number,
            product_name=ingredient.product.name.capitalize(),
            measure=ingredient.product.measurement_unit,
            amount=ingredient.amount,
        ) for number, ingredient in enumerate(ingredients, start=1)
    ]

    return '\n'.join([
        timezone.now().strftime(
            'Время составления Списка: %H:%M %d.%m.%Y.'
        ),
        'Необходимо купить следующие продукты:',
        *products,
        'Для блюд:',
        *recipes,
    ])
