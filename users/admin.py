from django.contrib import admin

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    "Админка для модели User"
    list_display = ("id", "phone", "invite_code", "used_invite", "is_staff")
    search_fields = ("phone", "invite_code")
