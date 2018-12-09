# django library
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm


# Create your forms here.


class UserCreateForm(UserCreationForm):
    '''class representing a form to create and save the data a new user'''
    first_name = forms.CharField(required=True, label='Forename')
    last_name = forms.CharField(required=True, label='Surname')
    is_staff = forms.BooleanField(widget=forms.HiddenInput(), initial=True)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'password1', 'password2', 'email', 'is_staff', 'is_superuser')

    def save(self, commit=True):
        user = super(UserCreateForm, self).save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.password1 = self.cleaned_data['password1']
        user.password2 = self.cleaned_data['password2']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user
