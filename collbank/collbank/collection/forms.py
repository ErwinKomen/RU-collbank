"""
Definition of forms.
"""

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.utils.translation import gettext_lazy as _
from collbank.collection.models import *

class BootstrapAuthenticationForm(AuthenticationForm):
    """Authentication form which uses boostrap CSS."""
    username = forms.CharField(max_length=254,
                               widget=forms.TextInput({
                                   'class': 'form-control',
                                   'placeholder': 'User name'}))
    password = forms.CharField(label=_("Password"),
                               widget=forms.PasswordInput({
                                   'class': 'form-control',
                                   'placeholder':'Password'}))


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    last_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    email = forms.EmailField(max_length=254, help_text='Required. Inform a valid email address.')

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', )


class CollectionForm(forms.ModelForm):
    """Form to define [Collection]"""

    class Meta:
        model = Collection
        fields = ['identifier', 'description']
        labels = {'identifer': _('Identifier'), }
        help_texts = { 'identifer': _('Enter a short but unique identifier of this collection.'), }


class PidForm(forms.ModelForm):
    """Form for the PID list- and details view"""

    class Meta:
        model = Collection
        fields = ['id', 'identifier', 'pidname', 'url']

    def __init__(self, *args, **kwargs):
        # Start by executing the standard handling
        super(PidForm, self).__init__(*args, **kwargs)
        # Make sure to set required and optional fields
        self.fields['identifier'].required = False
        self.fields['pidname'].required = False
        self.fields['url'].required = False
