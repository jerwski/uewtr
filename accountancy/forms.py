# django library
from django import forms

# my views
from accountancy.models import Customer

# bootstrap4 widget
from bootstrap4.widgets import RadioSelectButtonGroup

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
