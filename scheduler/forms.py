from typing import Any

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone

from .models import Application, Booking, SERVICE_CHOICES, Worker


class StyledAuthenticationForm(AuthenticationForm):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")


class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("first_name", "last_name", "username", "email")

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")

    def save(self, commit: bool = True) -> User:
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
        return user


class BookingForm(forms.ModelForm):
    scheduled_for = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local", "class": "form-control"}
        )
    )
    worker = forms.ModelChoiceField(
        queryset=Worker.objects.none(),
        required=False,
        empty_label="No preference",
        widget=forms.RadioSelect(attrs={"class": "visually-hidden worker-choice"}),
        label="Preferred professional",
    )
    class Meta:
        model = Booking
        fields = (
            "service_type",
            "scheduled_for",
            "address",
            "worker",
            "notes",
        )
        widgets = {
            "service_type": forms.Select(
                choices=SERVICE_CHOICES,
                attrs={"class": "form-select"},
            ),
            "address": forms.TextInput(attrs={"class": "form-control"}),
            "notes": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.fields["worker"].queryset = Worker.objects.filter(is_active=True)
        for name, field in self.fields.items():
            if name in ("worker",):
                continue
            if name not in self.Meta.widgets:
                field.widget.attrs.setdefault("class", "form-control")

    def clean_scheduled_for(self):
        scheduled_for = self.cleaned_data["scheduled_for"]
        if scheduled_for < timezone.now():
            raise forms.ValidationError("Bookings must be scheduled in the future.")
        return scheduled_for


class WorkWithUsForm(forms.Form):
    full_name = forms.CharField(max_length=120, label="Full name")
    email = forms.EmailField(label="Email")
    phone = forms.CharField(max_length=30, label="Phone", required=False)
    experience = forms.CharField(
        label="Relevant experience",
        widget=forms.Textarea(attrs={"rows": 4}),
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")

    def save(self) -> Application:
        data = self.cleaned_data
        return Application.objects.create(
            full_name=data["full_name"],
            email=data["email"],
            phone=data["phone"],
            experience=data["experience"],
        )
