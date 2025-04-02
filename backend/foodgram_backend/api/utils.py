from datetime import datetime

PRODUCT_IN_SHOPPING_LIST_FORMAT = (
    '{number}. {product_name}, '
    '{measure} - {amount}'
)
RUS_MONTHS = {
    number: name for number, name in enumerate((
        'января', 'февраля', 'марта', 'апреля', 'мая',
        'июня', 'июля', 'августа', 'сентября',
        'октября', 'ноября', 'декабря',
    ), start=1)
}


def generate_ingredients_file_content(ingredients, recipes):
    products = [
        PRODUCT_IN_SHOPPING_LIST_FORMAT.format(
            number=number,
            product_name=ingredient['product_name'].capitalize(),
            measure=ingredient['unit'],
            amount=ingredient['total'],
        ) for number, ingredient in enumerate(ingredients, start=1)
    ]
    month = RUS_MONTHS[datetime.now().month]
    return '\n'.join([
        datetime.now().strftime(
            f'Дата составления списка: %d {month} %Y.\n'
            'Время составления списка: %H:%M'
        ),
        'Необходимо купить следующие продукты:',
        *products,
        'Для блюд:',
        *[recipe.__str__() for recipe in recipes],
    ])
