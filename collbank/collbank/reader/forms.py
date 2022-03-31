"""
Definition of forms.
"""

from django import forms
from django.contrib.auth.models import User
from django.forms.widgets import *
from collbank.reader.models import SourceInfo



class UploadFileForm(forms.Form):
    """This is for uploading just one file"""

    file_source = forms.FileField(label="Specify which file should be loaded")


class UploadFilesForm(forms.Form):
    """This is for uploading multiple files"""

    files_field = forms.FileField(label="Specify which file(s) should be loaded",
                                  widget=forms.ClearableFileInput(attrs={'multiple': True}))


class SourceInfoForm(forms.ModelForm):
    """A form to show sourceinfo"""

    class Meta:
        ATTRS_FOR_FORMS = {'class': 'form-control'};

        model = SourceInfo
        fields = ['code', 'user', 'created', 'file', 'url']
        widgets={'code':    forms.TextInput(attrs={'style': 'width: 100%;', 'class': 'searching'}),
                 'created': forms.TextInput(attrs={'style': 'width: 100%;'}),
                 'url':     forms.TextInput(attrs={'style': 'width: 100%;', 'class': 'searching'}),
                 'file':    forms.FileInput(attrs={'style': 'width: 100%;'})
                 }

    def __init__(self, *args, **kwargs):
        # Start by executing the standard handling
        super(SourceInfoForm, self).__init__(*args, **kwargs)
        # Some fields are not required
        self.fields['code'].required = False
        self.fields['user'].required = False
        self.fields['created'].required = False
        self.fields['file'].required = False
        self.fields['url'].required = False

        # Get the instance
        if 'instance' in kwargs:
            instance = kwargs['instance']
            self.fields['user'].initial = instance.user
            self.fields['user'].queryset = User.objects.filter(id=instance.user.id)


