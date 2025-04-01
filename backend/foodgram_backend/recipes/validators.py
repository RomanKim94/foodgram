from django.contrib.auth.validators import UnicodeUsernameValidator


class MyUsernameValidator(UnicodeUsernameValidator):
    regex = r'^[a-zA-Z0-9_]+$'
