from __future__ import annotations

import random
import time
from typing import Any

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import FormView, TemplateView
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .forms import InviteActivateForm, PhoneAuthForm, PhoneVerifyForm
from .models import User
from .serializers import InviteActivateSerializer, PhoneAuthSerializer, PhoneVerifySerializer, ProfileSerializer

# ------------------------------
# SMS Client
# ------------------------------


class SMSAeroClient:
    """
    Клиент для отправки SMS через SMS Aero.
    """

    BASE_URL: str = "https://gate.smsaero.ru/v2/sms/send"

    @staticmethod
    def send_code(phone: str, code: str) -> None:
        """
        Отправляет SMS с кодом подтверждения.

        Args:
            phone: Телефонный номер.
            code: 4-значный код подтверждения.
        """
        response = requests.get(
            SMSAeroClient.BASE_URL,
            params={
                "number": phone,
                "text": f"Код подтверждения: {code}",
                "sign": "SMS Aero",
            },
            auth=(settings.SMSAERO_LOGIN, settings.SMSAERO_API_KEY),
            timeout=10,
        )
        response.raise_for_status()


# ------------------------------
# Helper functions
# ------------------------------


def send_auth_code(phone: str, request: HttpRequest) -> None:
    """
    Генерирует код и сохраняет его в сессии, затем отправляет SMS.
    """
    code = f"{random.randint(1000, 9999)}"
    request.session["auth_phone"] = phone
    request.session["auth_code"] = code

    # имитация задержки
    time.sleep(random.uniform(1, 2))
    SMSAeroClient.send_code(phone, code)


def verify_code(phone: str, code: str, request: HttpRequest) -> User | None:
    """
    Проверяет введённый код и создаёт пользователя при необходимости.
    """
    if request.session.get("auth_phone") != phone or request.session.get("auth_code") != code:
        return None

    user, _ = User.objects.get_or_create(phone=phone)
    login(request, user)
    return user


# ------------------------------
# API Views
# ------------------------------


class PhoneAuthView(APIView):
    """
    API для начала авторизации по номеру телефона.
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs) -> Response:
        serializer = PhoneAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone: str = serializer.validated_data["phone"]
        send_auth_code(phone, request)
        return Response({"detail": "Код отправлен"}, status=status.HTTP_200_OK)


class PhoneVerifyView(APIView):
    """
    API для подтверждения SMS-кода.
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs) -> Response:
        serializer = PhoneVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone: str = serializer.validated_data["phone"]
        code: str = serializer.validated_data["code"]

        user = verify_code(phone, code, request)
        if user is None:
            return Response({"detail": "Неверный код"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": "Авторизация успешна"}, status=status.HTTP_200_OK)


class ProfileView(APIView):
    """
    API профиля пользователя.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs) -> Response:
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data)


class ActivateInviteView(APIView):
    """
    API активации инвайт-кода.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs) -> Response:
        if request.user.has_used_invite():
            return Response({"detail": "Инвайт-код уже активирован"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = InviteActivateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        inviter: User = User.objects.get(invite_code=serializer.validated_data["invite_code"])

        # --- Проверка на свой код ---
        if inviter == request.user:
            return Response(
                {"detail": "Вы не можете активировать свой собственный инвайт-код"}, status=status.HTTP_400_BAD_REQUEST
            )

        if request.user.has_used_invite():
            return Response({"detail": "Инвайт-код уже активирован"}, status=status.HTTP_400_BAD_REQUEST)

        request.user.used_invite = inviter
        request.user.save()

        return Response({"detail": "Инвайт-код активирован"}, status=status.HTTP_200_OK)


# ------------------------------
# Logout View
# ------------------------------


class LogoutView(View):
    """
    Выход пользователя из профиля.
    При POST-запросе выполняется logout и перенаправление на страницу логина.
    """

    def post(self, request, *args, **kwargs):
        logout(request)
        return redirect("users:login")


# ------------------------------
# HTML Template Views
# ------------------------------


class LoginTemplateView(FormView):
    """
    HTML-страница ввода номера телефона.
    """

    template_name: str = "users/login.html"
    form_class = PhoneAuthForm
    success_url = reverse_lazy("users:verify")

    def form_valid(self, form: PhoneAuthForm) -> HttpResponse:
        request = self.request
        phone = form.cleaned_data["phone"]
        try:
            send_auth_code(phone, request)
            messages.success(request, "Код подтверждения отправлен на ваш номер")
        except Exception:
            messages.error(request, "Ошибка отправки SMS. Попробуйте позже.")
        return super().form_valid(form)


class VerifyCodeTemplateView(FormView):
    """
    HTML-страница подтверждения SMS-кода.
    """

    template_name: str = "users/verify_code.html"
    form_class = PhoneVerifyForm
    success_url = reverse_lazy("users:profile")

    def form_valid(self, form: PhoneVerifyForm) -> HttpResponse:
        request = self.request
        phone = request.session.get("auth_phone")
        code = form.cleaned_data["code"]

        user = verify_code(phone, code, request)
        if user is None:
            messages.error(request, "Неверный код. Попробуйте снова.")
            return super().form_invalid(form)

        messages.success(request, "Авторизация прошла успешно")
        return super().form_valid(form)


class ProfileTemplateView(LoginRequiredMixin, TemplateView):
    """
    HTML-страница профиля пользователя с активацией инвайт-кода.
    """

    template_name: str = "users/profile.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["profile"] = ProfileSerializer(self.request.user).data
        context["invite_form"] = InviteActivateForm()
        return context

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        form = InviteActivateForm(request.POST)
        if form.is_valid():
            invite_code: str = form.cleaned_data["invite_code"]
            try:
                inviter = User.objects.get(invite_code=invite_code)
                if not request.user.has_used_invite() and inviter != request.user:
                    request.user.used_invite = inviter
                    request.user.save()
                    messages.success(request, "Инвайт-код успешно активирован")
                else:
                    messages.warning(request, "Вы не можете активировать этот код")
            except User.DoesNotExist:
                messages.error(request, "Инвайт-код не существует")
        else:
            messages.error(request, "Неверный формат кода")

        return redirect("users:profile")
