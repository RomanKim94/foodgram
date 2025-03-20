IP сервера: 84.201.140.180  
Доменное имя: roman-foodgram.zapto.org

# Описание
«Фудграм» — сайт, на котором пользователи будут публиковать свои рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Зарегистрированным пользователям также будет доступен сервис «Список покупок». Он позволит создавать список продуктов, которые нужно купить для приготовления выбранных блюд.  

## Стэк  
#### В проекте используются следующие технологии:  
  - Фронтенд: React
  - Бекенд: Django, Django REST Framework
  - База данных: SQLite, PostgreSQL
  а так же Nginx, Docker, docker-compose.  


## Как развернуть проект локально
1. Склонируйте репозиторий и перейдите в корневую диркуторию проекта:
```
git clone https://github.com/RomanKim94/foodgram.git
cd foodgram
```
2. Настройте переменные окружения .env:
```
DEBUG=True
SECRET_KEY=ваш-secret-key
DB_ENGINE=postgresql
DB_NAME=ваш-db-name
DB_USER=ваш-db-user
DB_PASSWORD=ваш-db-password
DB_HOST=db
DB_PORT=5432
```
Укажите необходимые значения. Для переменной DB_ENGINE установите значение либо `postgresql`, либо `sqlite`.  
3. Запустите проект в фоновом режиме:
```
docker compose -f docker-compose.production.yml up -d
```
4. Примените миграции:
```
docker compose exec foodgram-backend python manage.py migrate
```
5. Для доступа к админке потребуется суперпользователь. Создайте суперпользователя:
```
docker compose exec foodgram-backend python manage.py createsuperuser
```
Укажите логин, email (обязательно), логин (обязательно) и пароль (потребуется ввести дважды).  
После разворачивания проекта, сервис будет доступен по адресу http://localhost:80.

## Автор:
### [Ким Роман](https://github.com/RomanKim94)