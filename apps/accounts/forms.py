from django import forms


class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].widget.attrs.update({"autocomplete": "username", "class": "field"})
        self.fields["password"].widget.attrs.update({"autocomplete": "current-password", "class": "field"})
