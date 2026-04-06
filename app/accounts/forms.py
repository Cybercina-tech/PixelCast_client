"""
Django forms for template-based authentication (Login & Sign-up).

Used by the Antler-themed login and signup pages.
"""
from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.core.validators import validate_email as django_validate_email

from .models import User


# CSS classes for Antler theme (Tailwind-style form-control)
INPUT_CLASSES = (
    "form-control w-full px-4 py-3 rounded-lg border border-slate-200 "
    "bg-white text-slate-900 placeholder-slate-400 "
    "focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 "
    "hover:border-slate-300 transition-colors duration-200"
)
INPUT_ERROR_CLASSES = INPUT_CLASSES + " border-red-500 focus:ring-red-500 focus:border-red-500"


class LoginForm(forms.Form):
    """Form for login: username/email + password."""

    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": INPUT_CLASSES,
                "placeholder": "Username or Email",
                "autocomplete": "username",
                "autofocus": True,
            }
        ),
        label="Username or Email",
    )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(
            attrs={
                "class": INPUT_CLASSES,
                "placeholder": "Password",
                "autocomplete": "current-password",
            }
        ),
        label="Password",
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

    def clean_username(self):
        value = self.cleaned_data.get("username")
        if value:
            value = value.strip().lower()
        return value

    def clean(self):
        cleaned = super().clean()
        username = cleaned.get("username")
        password = cleaned.get("password")
        if not username or not password:
            return cleaned
        user = None
        try:
            user_by_username = User.objects.get(username=username)
            user = authenticate(
                request=self.request, username=user_by_username.username, password=password
            )
        except User.DoesNotExist:
            try:
                user_by_email = User.objects.get(email=username)
                user = authenticate(
                    request=self.request,
                    username=user_by_email.username,
                    password=password,
                )
            except User.DoesNotExist:
                pass
        if user is None:
            raise ValidationError(
                "Invalid username/email or password. Please try again.",
                code="invalid_login",
            )
        if not user.is_active:
            raise ValidationError("This account is inactive.", code="inactive")
        cleaned["user"] = user
        return cleaned


class CustomUserCreationForm(UserCreationForm):
    """Sign-up form: username, email, password, confirm password."""

    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={
                "class": INPUT_CLASSES,
                "placeholder": "Create a password",
                "autocomplete": "new-password",
            }
        ),
        help_text="At least 8 characters; use letters and numbers.",
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(
            attrs={
                "class": INPUT_CLASSES,
                "placeholder": "Confirm your password",
                "autocomplete": "new-password",
            }
        ),
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")
        widgets = {
            "username": forms.TextInput(
                attrs={
                    "class": INPUT_CLASSES,
                    "placeholder": "Choose a username",
                    "autocomplete": "username",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": INPUT_CLASSES,
                    "placeholder": "you@example.com",
                    "autocomplete": "email",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Username"
        self.fields["email"].required = True
        self.fields["email"].label = "Email"

    def clean_username(self):
        value = self.cleaned_data.get("username")
        if value:
            value = value.strip()
            if len(value) < 3:
                raise ValidationError("Username must be at least 3 characters.")
            if User.objects.filter(username=value).exists():
                raise ValidationError("A user with this username already exists.")
        return value

    def clean_email(self):
        value = self.cleaned_data.get("email")
        if value:
            value = value.strip().lower()
            try:
                django_validate_email(value)
            except ValidationError:
                raise ValidationError("Enter a valid email address.")
            if User.objects.filter(email=value).exists():
                raise ValidationError("A user with this email already exists.")
        return value

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("The two password fields didn't match.")
        return password2
