from __future__ import annotations

from typing import Optional

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.crypto import get_random_string


class UserManager(BaseUserManager):
    """
    Менеджер пользователей для кастомной модели User.
    """

    use_in_migrations = True

    def _create_user(self, phone: str, password: str | None, **extra_fields):
        """Внутренний метод создания пользователя."""
        if not phone:
            raise ValueError("The given phone number must be set")

        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, phone: str, password: str | None = None, **extra_fields):
        """Создаёт обычного пользователя."""
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(phone, password, **extra_fields)

    def create_superuser(self, phone: str, password: str, **extra_fields):
        """Создаёт суперпользователя."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(phone, password, **extra_fields)


class User(AbstractUser):
    """
    Кастомная модель пользователя.

    Авторизация по номеру телефона.
    Поддержка реферальной системы через инвайт-коды.
    """

    username = None
    email = None

    phone = models.CharField(max_length=15, unique=True, verbose_name="Номер телефона", help_text="7XXXXXXXXXX")

    invite_code = models.CharField(
        max_length=6,
        unique=True,
        editable=False,
        verbose_name="Инвайт-код",
    )

    used_invite: Optional["User"] = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="invited_users",
        verbose_name="Использованный инвайт-код",
    )

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS: list[str] = []

    objects = UserManager()

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self) -> str:
        """Возвращает строковое представление пользователя."""
        return f"{self.phone} ({self.invite_code})"

    def save(self, *args, **kwargs) -> None:
        """
        При первом сохранении генерирует уникальный инвайт-код.
        """
        if not self.invite_code:
            while True:
                code = get_random_string(
                    length=6,
                    allowed_chars="0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ",
                )
                if not User.objects.filter(invite_code=code).exists():
                    self.invite_code = code
                    break
        super().save(*args, **kwargs)

    def has_used_invite(self) -> bool:
        """Проверяет, активировал ли пользователь инвайт-код."""
        return self.used_invite is not None
