# django library
from django import forms

# bootstrap4 widget
from bootstrap4.widgets import RadioSelectButtonGroup

# my views
from cashregister.models import Company, CashRegister


# Create your forms here


class CompanyAddForm(forms.ModelForm):
    CLOSED = 0
    OPERATING = 1
    SUSPENDED = 2
    LIQUIDATION = 3
    STATUS_CHOICE = ((CLOSED, 'Closed'), (OPERATING, 'Operating'), (SUSPENDED,'Suspended'), (LIQUIDATION, 'Liquidation'))

    status = forms.ChoiceField(label="Select the status type...", required=True,
                               widget=RadioSelectButtonGroup, choices=STATUS_CHOICE, initial=1)

    class Meta:
        model = Company
        fields = ['company', 'nip', 'street', 'city', 'postal', 'phone', 'account', 'status']


class CashRegisterForm(forms.ModelForm):
    queryset = Company.objects.filter(status__range=[1,3])
    company = forms.ModelChoiceField(widget=forms.HiddenInput(attrs={'readonly': True}), queryset=queryset)

    class Meta:
        model = CashRegister
        fields = ['company', 'symbol', 'contents', 'income', 'expenditure']
