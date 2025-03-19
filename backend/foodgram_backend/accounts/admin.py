from django.contrib import admin

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name')
    search_fields = ('email', 'first_name')

    def save_model(self, request, obj, form, change):
        password = form.cleaned_data['password']
        if password:
            obj.set_password(password)
        super().save_model(request, obj, form, change)
