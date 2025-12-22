# users/admin.py
from django.contrib import admin
from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "phone", "invite_code", "used_invite", "is_staff")
    search_fields = ("phone", "invite_code")
