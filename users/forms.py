#users/forms.py
from __future__ import annotations

from django import forms


class PhoneAuthForm(forms.Form):
    """
    Форма ввода номера телефона.
    """

    phone: forms.CharField = forms.CharField(
        max_length=15,
        label="Номер телефона",
        help_text="7XXXXXXXXXX",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "7XXXXXXXXXX",
            }
        ),
    )


class PhoneVerifyForm(forms.Form):
    """
    Форма подтверждения SMS-кода.
    """

    code: forms.CharField = forms.CharField(
        max_length=4,
        label="Код подтверждения",
    )


class InviteActivateForm(forms.Form):
    """
    Форма активации инвайт-кода.
    """

    invite_code: forms.CharField = forms.CharField(
        max_length=6,
        label="Инвайт-код",
    )