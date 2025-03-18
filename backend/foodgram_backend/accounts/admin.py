from django.contrib import admin

from accounts import models


@admin.register(models.User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name')
    search_fields = ('email', 'first_name')
