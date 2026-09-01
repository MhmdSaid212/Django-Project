from django import forms

from apps.accounts.constants import MIN_PASSWORD_LENGTH, ROLE_CHOICES
from core.constants import UserStatus


def _styled(fields: dict[str, forms.Field]) -> None:
    for field in fields.values():
        existing = field.widget.attrs.get("class", "")
        if "field" not in existing.split():
            field.widget.attrs["class"] = f"{existing} field".strip()


class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _styled(self.fields)
        self.fields["email"].widget.attrs.update({"autocomplete": "username"})
        self.fields["password"].widget.attrs.update({"autocomplete": "current-password"})


class StaffUserForm(forms.Form):
    first_name = forms.CharField(max_length=80)
    last_name = forms.CharField(max_length=80)
    email = forms.EmailField()
    phone = forms.CharField(max_length=40, required=False)
    role = forms.ChoiceField(choices=ROLE_CHOICES)
    password = forms.CharField(
        min_length=MIN_PASSWORD_LENGTH,
        widget=forms.PasswordInput,
        help_text=f"At least {MIN_PASSWORD_LENGTH} characters.",
    )
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirm password")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _styled(self.fields)
        self.fields["password"].widget.attrs.update({"autocomplete": "new-password"})
        self.fields["confirm_password"].widget.attrs.update({"autocomplete": "new-password"})

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get("password")
        confirm = cleaned.get("confirm_password")
        if password and confirm and password != confirm:
            self.add_error("confirm_password", "Passwords do not match.")
        return cleaned


class ChangeRoleForm(forms.Form):
    role = forms.ChoiceField(choices=ROLE_CHOICES)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _styled(self.fields)


class SetStatusForm(forms.Form):
    status = forms.ChoiceField(choices=[(item.value, item.value.title()) for item in UserStatus])


class ChangePasswordForm(forms.Form):
    current_password = forms.CharField(widget=forms.PasswordInput)
    new_password = forms.CharField(min_length=MIN_PASSWORD_LENGTH, widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirm new password")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _styled(self.fields)
        self.fields["current_password"].widget.attrs.update({"autocomplete": "current-password"})
        self.fields["new_password"].widget.attrs.update({"autocomplete": "new-password"})
        self.fields["confirm_password"].widget.attrs.update({"autocomplete": "new-password"})

    def clean(self):
        cleaned = super().clean()
        new_password = cleaned.get("new_password")
        confirm = cleaned.get("confirm_password")
        if new_password and confirm and new_password != confirm:
            self.add_error("confirm_password", "Passwords do not match.")
        return cleaned


class ResetPasswordForm(forms.Form):
    new_password = forms.CharField(min_length=MIN_PASSWORD_LENGTH, widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirm password")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _styled(self.fields)
        self.fields["new_password"].widget.attrs.update({"autocomplete": "new-password"})
        self.fields["confirm_password"].widget.attrs.update({"autocomplete": "new-password"})

    def clean(self):
        cleaned = super().clean()
        new_password = cleaned.get("new_password")
        confirm = cleaned.get("confirm_password")
        if new_password and confirm and new_password != confirm:
            self.add_error("confirm_password", "Passwords do not match.")
        return cleaned
