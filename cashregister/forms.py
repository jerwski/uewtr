# django library
from django import forms

# my views
from cashregister.models import Company


# Create your forms here


class CompanyAddForm(forms.ModelForm):

    class Meta:
        model = Company
        fields = ['company', 'nip', 'street', 'city', 'zip', 'phone', 'email']
