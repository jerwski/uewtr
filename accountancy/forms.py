# django library
from django import forms

# my views
from accountancy.models import Customer, Products, ReleaseOutside, ReleaseOutsideProduct

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


class ReleasedOutsideForm(forms.Form):
	options = {'icons'  : {'clear': 'fa fa-trash'}, 'useCurrent': True,
	           'buttons': {'showToday': True, 'showClear': True, 'showClose': True}}
	attrs = {'prepend': 'fa fa-calendar', 'append': 'fa fa-calendar', 'input_toggle': False, 'icon_toggle': True}

	date_of_shipment = forms.DateField(widget=DatePicker(options=options, attrs=attrs))

	class Meta:
		model = ReleaseOutside
		fields = ['company', 'customer', 'number', 'conveyance', 'waybill', 'date_of_shipment', 'invoice', 'order']
