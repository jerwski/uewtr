# django library
from django import forms

# bootstrap4 widget
from bootstrap4.widgets import RadioSelectButtonGroup

# my views
from cashregister.models import Company, CashRegister

# my validators
from validators.my_validator import positive_value, from_transfer

# Create your forms here


class CompanyAddForm(forms.ModelForm):
	CLOSED = 0
	OPERATING = 1
	SUSPENDED = 2
	LIQUIDATION = 3
	STATUS_CHOICE = ((CLOSED, 'Closed'), (OPERATING, 'Operating'), (SUSPENDED,'Suspended'), (LIQUIDATION, 'Liquidation'))
	attrs={'class':'btn-sm btn-outline-light'}
	status = forms.ChoiceField(label="Select the status type...", required=True,
							   widget=RadioSelectButtonGroup(attrs=attrs), choices=STATUS_CHOICE, initial=1)

	class Meta:
		model = Company
		fields = ['company', 'nip', 'street', 'city', 'postal', 'phone', 'account', 'status']


class CashRegisterForm(forms.ModelForm):
	queryset = Company.objects.filter(status__range=[1,3])
	company = forms.ModelChoiceField(widget=forms.HiddenInput(attrs={'readonly': True}), queryset=queryset)
	symbol = forms.CharField(widget=forms.TextInput(attrs={'id': 'autosym'}))
	contents = forms.CharField(widget=forms.Textarea(attrs={'cols': 30, 'rows': 2, 'id': 'autocpl'}),
	                           label='Za co?', validators=[from_transfer])
	income = forms.FloatField(initial=f'{0:.2f}', validators=[positive_value])
	expenditure = forms.FloatField(initial=f'{0:.2f}', validators=[positive_value])

	class Meta:
		model = CashRegister
		fields = ['company', 'symbol', 'contents', 'income', 'expenditure']
