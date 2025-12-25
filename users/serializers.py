# users/serializers.py
from __future__ import annotations

from typing import Any

from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class PhoneAuthSerializer(serializers.Serializer):
    """
    Сериализатор для начала авторизации по номеру телефона.
    """

    phone: serializers.CharField = serializers.CharField(max_length=15)

    def validate_phone(self, value: str) -> str:
        """Проверяет корректность номера телефона"""
        if not value.isdigit():
            raise serializers.ValidationError("Номер телефона должен содержать только цифры.")
        return value


class PhoneVerifySerializer(serializers.Serializer):
    """
    Сериализатор для подтверждения SMS-кода.
    """

    phone: serializers.CharField = serializers.CharField(max_length=15)
    code: serializers.CharField = serializers.CharField(max_length=4)


class InviteActivateSerializer(serializers.Serializer):
    """
    Сериализатор для активации инвайт-кода.
    """

    invite_code: serializers.CharField = serializers.CharField(max_length=6)

    def validate_invite_code(self, value: str) -> str:
        """
        Проверяет существование инвайт-кода.
        """
        if not User.objects.filter(invite_code=value).exists():
            raise serializers.ValidationError("Инвайт-код не существует.")
        return value


class ProfileSerializer(serializers.ModelSerializer):
    """
    Сериализатор профиля пользователя.
    """

    invited_users: serializers.SerializerMethodField = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "phone",
            "invite_code",
            "used_invite",
            "invited_users",
        )

    def get_invited_users(self, obj: User) -> list[str]:
        """
        Возвращает список номеров телефонов пользователей,
        активировавших инвайт-код текущего пользователя.
        """
        return [user.phone for user in obj.invited_users.all()]
