from django import forms

from apps.accounts.constants import MIN_PASSWORD_LENGTH, ROLE_CHOICES
from core.constants import UserStatus

AUTH_INPUT_CLASS = (
    "w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-night "
    "placeholder:text-slate-400 shadow-sm outline-none transition "
    "focus:border-brand focus:ring-4 focus:ring-brand/15"
)


def _styled(fields: dict[str, forms.Field], *, auth: bool = False) -> None:
    for field in fields.values():
        existing = field.widget.attrs.get("class", "")
        classes = existing.split()
        if "field" not in classes:
            classes.append("field")
        if auth:
            classes.extend(AUTH_INPUT_CLASS.split())
        field.widget.attrs["class"] = " ".join(dict.fromkeys(classes))


class LoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={"placeholder": "you@agency.com"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"placeholder": "••••••••"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _styled(self.fields, auth=True)
        self.fields["email"].widget.attrs.update({"autocomplete": "username"})
        self.fields["password"].widget.attrs.update({"autocomplete": "current-password"})


class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={"placeholder": "you@agency.com"}))
    new_password = forms.CharField(
        min_length=MIN_PASSWORD_LENGTH,
        widget=forms.PasswordInput(attrs={"placeholder": "••••••••"}),
        help_text=f"At least {MIN_PASSWORD_LENGTH} characters.",
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "••••••••"}),
        label="Confirm password",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _styled(self.fields, auth=True)
        self.fields["email"].widget.attrs.update({"autocomplete": "username"})
        self.fields["new_password"].widget.attrs.update({"autocomplete": "new-password"})
        self.fields["confirm_password"].widget.attrs.update({"autocomplete": "new-password"})

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get("new_password")
        confirm = cleaned.get("confirm_password")
        if password and confirm and password != confirm:
            self.add_error("confirm_password", "Passwords do not match.")
        return cleaned


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
