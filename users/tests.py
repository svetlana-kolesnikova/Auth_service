# users/tests.py
from __future__ import annotations
from typing import Any
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from .models import User

User = get_user_model()


class UserAuthTests(TestCase):
    """
    Тесты для приложения users:
    авторизация по телефону, SMS-код, профиль и инвайты.
    """

    def setUp(self) -> None:
        """Создание тестового клиента и пользователя."""
        self.client: Client = Client()
        self.test_phone: str = "79991234567"
        self.user: User = User.objects.create(phone=self.test_phone)

    @patch("users.views.SMSAeroClient.send_code")
    def test_phone_auth_api(self, mock_send_code: Any) -> None:
        """
        Проверка API отправки SMS-кода.
        """
        url: str = reverse("users:api_phone_auth")
        response = self.client.post(url, data={"phone": self.test_phone})
        self.assertEqual(response.status_code, 200)
        self.assertIn("detail", response.json())
        self.assertTrue(mock_send_code.called)
        session = self.client.session
        self.assertEqual(session["auth_phone"], self.test_phone)
        self.assertEqual(len(session["auth_code"]), 4)

    def test_phone_verify_api_success(self) -> None:
        """
        Проверка успешного подтверждения SMS-кода через API.
        """
        session = self.client.session
        session["auth_phone"] = self.test_phone
        session["auth_code"] = "1234"
        session.save()

        url: str = reverse("users:api_phone_verify")
        response = self.client.post(url, data={"phone": self.test_phone, "code": "1234"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("detail", response.json())
        self.assertEqual(response.json()["detail"], "Авторизация успешна")

    def test_phone_verify_api_fail(self) -> None:
        """
        Проверка ошибки при неверном коде SMS.
        """
        session = self.client.session
        session["auth_phone"] = self.test_phone
        session["auth_code"] = "1234"
        session.save()

        url: str = reverse("users:api_phone_verify")
        response = self.client.post(url, data={"phone": self.test_phone, "code": "0000"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("detail", response.json())

    def test_profile_api_authenticated(self) -> None:
        """
        Проверка получения данных профиля через API.
        """
        self.client.force_login(self.user)
        url: str = reverse("users:api_profile")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("phone", response.json())
        self.assertEqual(response.json()["phone"], self.test_phone)

    def test_invite_activation_api(self) -> None:
        """
        Проверка активации инвайт-кода через API.
        """
        inviter: User = User.objects.create(phone="79990001122")
        self.client.force_login(self.user)
        url: str = reverse("users:api_invite")
        response = self.client.post(url, data={"invite_code": inviter.invite_code})
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.used_invite, inviter)

    def test_invite_activation_api_already_used(self) -> None:
        """
        Проверка попытки повторной активации инвайт-кода.
        """
        inviter: User = User.objects.create(phone="79990001122")
        self.user.used_invite = inviter
        self.user.save()
        self.client.force_login(self.user)
        url: str = reverse("users:api_invite")
        response = self.client.post(url, data={"invite_code": inviter.invite_code})
        self.assertEqual(response.status_code, 400)

    @patch("users.views.SMSAeroClient.send_code")
    def test_login_template_view(self, mock_send_code: Any) -> None:
        """
        Проверка HTML-страницы ввода телефона и отправки кода.
        """
        url: str = reverse("users:login")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Вход по номеру телефона")

        response = self.client.post(url, data={"phone": self.test_phone})
        self.assertEqual(response.status_code, 302)  # редирект на verify
        self.assertTrue(mock_send_code.called)

    def test_verify_template_view_success(self) -> None:
        """
        Проверка HTML-страницы подтверждения кода.
        """
        session = self.client.session
        session["auth_phone"] = self.test_phone
        session["auth_code"] = "1234"
        session.save()

        url: str = reverse("users:verify")
        response = self.client.post(url, data={"code": "1234"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.id)

    def test_profile_template_invite_activation(self) -> None:
        """
        Проверка активации инвайт-кода через форму профиля.
        """
        inviter: User = User.objects.create(phone="79990001122")
        self.client.force_login(self.user)

        url: str = reverse("users:profile")
        response = self.client.post(url, data={"invite_code": inviter.invite_code})
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.used_invite, inviter)

    def test_has_used_invite_method(self) -> None:
        """
        Проверка метода has_used_invite().
        """
        self.assertFalse(self.user.has_used_invite())
        inviter: User = User.objects.create(phone="79990001122")
        self.user.used_invite = inviter
        self.user.save()
        self.assertTrue(self.user.has_used_invite())
