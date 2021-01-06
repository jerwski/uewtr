# django core
from django import forms

# datetime widget
from tempus_dominus.widgets import DatePicker

# my models
from employee.models import Employee, EmployeeData, EmployeeHourlyRate

# my function
from functions.widgets import RadioSelectButtonGroup

# my validators
from validators.my_validator import check_pesel


# Create your forms here.


# queryset to validate HiddenInput fields
queryset = Employee.objects.all()

icons = {
			'today': 'fa fa-calendar-alt',
			'clear': 'fa fa-trash-alt',
			'close': 'fa fa-times'
		}

class EmployeeBasicDataForm(forms.ModelForm):
	'''class representing a form to create/change and save the basic data of employee'''
	UNPAID_LEAVE = 0
	PAID_LEAVE = 1
	LEAVE_CHOICE = ((UNPAID_LEAVE, 'Unpaid'), (PAID_LEAVE,'Paid'))
	DEACTIVE = 0
	ACTIVE = 1
	STATUS_CHOICE = ((DEACTIVE, 'Deactive'), (ACTIVE,'Active'))
	# attrs
	attrs={'class':'btn-sm btn-outline-light'}
	# fields
	forename = forms.CharField(max_length=100)
	surname = forms.CharField(max_length=100)
	pesel = forms.CharField(min_length=11, max_length=11, validators=[check_pesel])
	leave = forms.ChoiceField(label="Leave choice:", widget=RadioSelectButtonGroup(attrs=attrs),
							  required=True, choices=LEAVE_CHOICE)
	status = forms.ChoiceField(label="Status choice:", widget=RadioSelectButtonGroup(attrs=attrs),
							   required=True, choices=STATUS_CHOICE)

	class Meta:
		model = Employee
		fields = ('forename', 'surname', 'pesel', 'status', 'leave')


class EmployeeExtendedDataForm(forms.ModelForm):
	'''class representing a form to create/change and save the extented data of employee'''
	NO_OVERTIME = 0
	WEEKLY_OVERTIME = 1
	SATURDAT_OVERTIME = 2
	RATINGS = [(NO_OVERTIME, 'Clear contract'), (WEEKLY_OVERTIME, 'Weekly overtime'), (SATURDAT_OVERTIME, 'Saturday overtime')]
	# options, attrs, overclass
	options = {'icons': icons, 'useCurrent': True,
			   'buttons': {'showToday': True, 'showClear': True, 'showClose': True}}
	attrs={'prepend': 'fa fa-calendar-check', 'append': 'fa fa-calendar-check', 'input_toggle': False, 'icon_toggle': True}
	overclass={'class':'btn-sm btn-outline-light'}
	# fields
	worker = forms.ModelChoiceField(widget=forms.HiddenInput(attrs={'readonly': True}), queryset=queryset)
	birthday = forms.DateField(label='Date of birthday', widget=DatePicker(options=options, attrs=attrs))
	start_contract = forms.DateField(label='Date of start contract', widget=DatePicker(options=options, attrs=attrs))
	end_contract = forms.DateField(required=False, label='Date of end contract', widget=DatePicker(options=options, attrs=attrs))
	overtime = forms.ChoiceField(label="Select the contract type:", required=True, initial=0,
								 widget=RadioSelectButtonGroup(attrs=overclass), choices=RATINGS)
	class Meta:
		model = EmployeeData
		fields = ('worker', 'birthday', 'postal', 'city', 'street', 'house', 'flat',
				  'phone', 'workplace', 'start_contract', 'end_contract', 'overtime')
		widgets = {'city': forms.TextInput(attrs={'id':'autocpl'}),}


class EmployeeHourlyRateForm(forms.ModelForm):
	'''class representing a form to create/change and save the hourly rate data of employee'''
	# fields
	worker = forms.ModelChoiceField(widget=forms.HiddenInput(attrs={'readonly': True}), queryset=queryset)
	hourly_rate = forms.FloatField(min_value=7)

	class Meta:
		model = EmployeeHourlyRate
		fields = ['worker', 'hourly_rate']