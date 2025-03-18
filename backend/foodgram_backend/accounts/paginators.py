from rest_framework.pagination import PageNumberPagination


class UserCustomPaginator(PageNumberPagination):
    page_size_query_param = 'limit'
