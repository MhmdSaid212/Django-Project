"""Django forms for HTML pages. Keep MongoDB out of forms — validate input only."""
from django import forms


class PlaceholderForm(forms.Form):
    """Replace with real fields. Do not turn this into a ModelForm."""

    notes = forms.CharField(required=False, widget=forms.Textarea)
