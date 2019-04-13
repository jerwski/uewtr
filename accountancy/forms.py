# django library
from django import forms

# my views
from cashregister.models import Company
from accountancy.models import Customer, Products, AccountancyDocument, AccountancyProducts

# bootstrap4 widget
from bootstrap4.widgets import RadioSelectButtonGroup


# datetime widget
from tempus_dominus.widgets import DatePicker

# my validators
from validators.my_validator import from_transfer, positive_value


# Create your forms here


class CustomerAddForm(forms.ModelForm):
	CLOSED = 0
	OPERATING = 1
	SUSPENDED = 2
	LIQUIDATION = 3
	STATUS_CHOICE = ((CLOSED, 'Closed'), (OPERATING, 'Operating'), (SUSPENDED,'Suspended'), (LIQUIDATION, 'Liquidation'))

	status = forms.ChoiceField(label="Select the status type...", required=True,
							   widget=RadioSelectButtonGroup, choices=STATUS_CHOICE, initial=1)

	class Meta:
		model = Customer
		fields = ['customer', 'nip', 'street', 'city', 'postal', 'phone', 'email', 'status']


class AccountancyDocumentForm(forms.ModelForm):
	KLIENTA = 0
	CB774GU = 1
	KURIER = 2
	CONVEYANCE = ((KLIENTA, 'Klienta'), (CB774GU, 'CB 774GU'), (KURIER, 'Kurier'))


	options = {'icons'  : {'clear': 'fa fa-trash'}, 'useCurrent': True,
	           'buttons': {'showToday': True, 'showClear': True, 'showClose': True}}
	attrs = {'prepend': 'fa fa-calendar', 'append': 'fa fa-calendar', 'input_toggle': False, 'icon_toggle': True}

	queryset = Company.objects.filter(status__range=[1, 3])
	company = forms.ModelChoiceField(widget=forms.HiddenInput(attrs={'readonly': True}), queryset=queryset)
	conveyance = forms.ChoiceField(widget=forms.Select(), choices=CONVEYANCE, initial=1)
	date_of_shipment = forms.DateField(widget=DatePicker(options=options, attrs=attrs))

	class Meta:
		model = AccountancyDocument
		fields = ['company', 'customer', 'number', 'conveyance', 'waybill', 'date_of_shipment', 'invoice', 'order']


class AccountancyDocumentProductsForm(forms.ModelForm):
	SZTUK = 0
	KOMPLET = 1
	TYSIĄC = 2
	ARKUSZ = 3
	LITR = 4
	UNITS = ((SZTUK, 'szt.'), (KOMPLET, 'kpl.'), (TYSIĄC, 'tys.'), (ARKUSZ, 'ark.'), (LITR, 'ltr.'))
	queryset = AccountancyDocument.objects.all()
	document = forms.ModelChoiceField(widget=forms.HiddenInput(attrs={'readonly': True}), queryset=queryset)
	unit = forms.ChoiceField(widget=forms.Select(), choices=UNITS, initial=1)

	class Meta:
		model = AccountancyProducts
		fields = ['document', 'product', 'quanity', 'unit']
