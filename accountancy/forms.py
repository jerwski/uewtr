# django library
from django import forms

# my views
from cashregister.models import Company
from accountancy.models import Customer, Product, AccountancyDocument, AccountancyProducts

# bootstrap4 widget
from bootstrap4.widgets import RadioSelectButtonGroup


# datetime widget
from tempus_dominus.widgets import DatePicker


# Create your forms here


class NewProductAddForm(forms.ModelForm):
	ZW = 0
	VAT5 = 5
	VAT8 = 8
	VAT23 = 23
	VAT = ((VAT5,'5%'), (VAT8, '8%'), (VAT23, '23%'), (ZW, 'Zwolniony'))

	SZTUK = 0
	KOMPLET = 1
	TYSIĄC = 2
	ARKUSZ = 3
	LITR = 4
	ROLA = 5
	UNITS = ((SZTUK, 'szt.'), (KOMPLET, 'kpl.'), (TYSIĄC, 'tys.'), (ARKUSZ, 'ark.'), (LITR, 'ltr.'), (ROLA, 'rola'))
	
	vat = forms.ChoiceField(label='Stawka VAT', required=True, widget=forms.Select, choices=VAT, initial=VAT23)
	unit = forms.ChoiceField(widget=forms.Select(), choices=UNITS, initial=1)

	class Meta:
		model = Product
		fields = ['name', 'unit', 'netto', 'vat']


class CustomerAddForm(forms.ModelForm):
	CLOSED = 0
	OPERATING = 1
	SUSPENDED = 2
	LIQUIDATION = 3
	STATUS_CHOICE = ((CLOSED, 'Closed'), (OPERATING, 'Operating'), (SUSPENDED,'Suspended'), (LIQUIDATION, 'Liquidation'))

	status = forms.ChoiceField(label="Select the status type...", required=True, widget=RadioSelectButtonGroup, choices=STATUS_CHOICE, initial=1)

	class Meta:
		model = Customer
		fields = ['customer', 'nip', 'street', 'city', 'postal', 'phone', 'email', 'status']


class AccountancyDocumentForm(forms.ModelForm):
	ODBIORCA = 0
	CB774GU = 1
	KURIER = 2
	CONVEYANCE = ((ODBIORCA, 'Odbiorca'), (CB774GU, 'CB 774GU'), (KURIER, 'Kurier'))

	options = {'icons'  : {'clear': 'fa fa-trash'}, 'useCurrent': True,
	           'buttons': {'showToday': True, 'showClear': True, 'showClose': True}}
	attrs = {'append': 'fa fa-calendar', 'input_toggle': False, 'icon_toggle': True}

	qs_company = Company.objects.filter(status__range=[1, 3])
	qs_customer = Customer.objects.filter(status__range=[1, 3])
	company = forms.ModelChoiceField(widget=forms.HiddenInput(attrs={'readonly': True}), queryset=qs_company)
	customer = forms.ModelChoiceField(widget=forms.HiddenInput(attrs={'readonly': True}), queryset=qs_customer)
	number = forms.IntegerField(widget=forms.NumberInput(attrs={'readonly': True}))
	conveyance = forms.ChoiceField(widget=forms.Select(), choices=CONVEYANCE, initial=1, label='Środek transportu')
	date_of_shipment = forms.DateField(widget=DatePicker(options=options, attrs=attrs), label='Data wysyłki')

	class Meta:
		model = AccountancyDocument
		fields = ['company', 'customer', 'number', 'conveyance', 'waybill', 'date_of_shipment', 'invoice', 'order']
