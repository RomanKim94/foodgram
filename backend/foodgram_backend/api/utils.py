from datetime import timezone

PRODUCT_IN_SHOPPING_LIST_FORMAT = (
    '{number}. {product_name}, '
    '{measure} - {amount}'
)


def generate_ingredients_file_content(ingredients, recipes):
    products = [
        PRODUCT_IN_SHOPPING_LIST_FORMAT
        .format(
            number=number,
            product_name=product[0].capitalize(),
            measure=product[1],
            amount=ingredients[product],
        ) for number, product in enumerate(ingredients.keys(), start=1)
    ]

    return '\n'.join([
        timezone.now().strftime(
            'Время составления Списка: %H:%M %d.%m.%Y.'
        ),
        'Необходимо купить следующие продукты:',
        '\n'.join(products),
        'Для блюд:',
        '\n'.join(recipes) + '.',
    ])
