from django import forms


class PlaceholderForm(forms.Form):
    notes = forms.CharField(required=False, widget=forms.Textarea)
