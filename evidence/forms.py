# standard library
from datetime import timedelta

# django core
from django import forms
from django.utils.timezone import now

# datetime widget
from tempus_dominus.widgets import DateTimePicker, DatePicker

# my models
from employee.models import Employee
from evidence.models import WorkEvidence, EmployeeLeave, AccountPayment

# my functions
from functions.myfunctions import previous_month_year

# my widgets
from functions.widgets import RadioSelectButtonGroup


# Create your forms here.


# queryset to validate HiddenInput fields
queryset = Employee.objects.all()
month, year = previous_month_year(now().month, now().year)
q1 = queryset.filter(status=1)
q2 = queryset.filter(employeedata__end_contract__year__gte=year, employeedata__end_contract__month__gte=month)
query = q1 | q2

# tempus-dominus datetimepiker icons
icons = {
	        'today': 'fas fa-calendar-day',
            'clear': 'fas fa-trash-alt',
            'close': 'fas fa-times-circle'
		}


# my forms
class WorkEvidenceForm(forms.ModelForm):
	options = {'icons': icons, 'format': 'YYYY-MM-DD HH:mm', 'maxDate': str(now().date() + timedelta(days=1)),
               'useCurrent': False, 'stepping': 5, 'buttons': {'showToday': True, 'showClear': True, 'showClose': True},
               'sideBySide': True}
	attrs = {'prepend': 'fas fa-user-clock', 'append': 'fas fa-calendar-check', 'input_toggle': False, 'icon_toggle': True}
	worker = forms.ModelChoiceField(widget=forms.HiddenInput(attrs={'readonly': True}), queryset=query)
	start_work = forms.DateTimeField(label='Start of work (date and time)',
									 widget=DateTimePicker(options=options, attrs=attrs))
	end_work = forms.DateTimeField(label='End of work (date and time)',
								   widget=DateTimePicker(options=options, attrs=attrs))

	class Meta:
		model = WorkEvidence
		fields = ['worker', 'start_work', 'end_work']


class EmployeeLeaveForm(forms.ModelForm):
	# attrs for RadioSelectButtonGroup
	# choices, attrs and options
	LEAVEKIND = [('unpaid_leave', 'Unpaid leave'), ('paid_leave', 'Paid leave'), ('maternity_leave', 'Maternity leave')]
	options = {'icons': icons, 'useCurrent': True, 'daysOfWeekDisabled': [0,6],
			   'buttons': {'showToday': True, 'showClear': True, 'showClose': True}}
	attrs = {'prepend': 'fas fa-calendar-check', 'append': 'fas fa-calendar-check', 'input_toggle': False, 'icon_toggle': True}
	# fields
	worker = forms.ModelChoiceField(widget=forms.HiddenInput(attrs={'readonly': True}), queryset=query)
	leave_date = forms.DateField(widget=DatePicker(options=options, attrs=attrs))
	leave_flag = forms.ChoiceField(label="Leave choice:", widget=RadioSelectButtonGroup(),
	                               required=True, choices=LEAVEKIND)

	class Meta:
		model = EmployeeLeave
		fields = ['worker', 'leave_date', 'leave_flag']


class PeriodCurrentComplexDataForm(forms.Form):
	options = {'icons': icons, 'useCurrent': True, 'format': 'MM/YYYY',
			   'buttons': {'showToday': True, 'showClear': True, 'showClose': True}}
	attrs = {'prepend': 'fas fa-calendar-check', 'input_toggle': False, 'icon_toggle': True}

	choice_date = forms.DateField(widget=DatePicker(options=options, attrs=attrs))


class PeriodMonthlyPayrollForm(forms.Form):
	options = {'icons': icons, 'useCurrent': True, 'format': 'MM/YYYY',
			   'buttons': {'showToday': True, 'showClear': True, 'showClose': True}}
	attrs = {'prepend': 'fas fa-calendar-check', 'append': 'fas fa-calendar-check', 'input_toggle': False, 'icon_toggle': True}

	choice_date = forms.DateField(label='Select a month and year...', widget=DatePicker(options=options, attrs=attrs))


class AccountPaymentForm(forms.ModelForm):
	options = {'icons': icons, 'useCurrent': True,
			   'buttons': {'showToday': True, 'showClear': True, 'showClose': True}}
	attrs = {'prepend': 'fas fa-calendar-check', 'append': 'fas fa-calendar-check', 'input_toggle': False, 'icon_toggle': True}

	worker = forms.ModelChoiceField(widget=forms.HiddenInput(attrs={'readonly': True}), queryset=query)

	account_date = forms.DateField(label='Select date of the advance payment',
								   widget=DatePicker(options=options, attrs=attrs))
	account_value = forms.FloatField(min_value=10)
	class Meta:
		model = AccountPayment
		fields = ['worker', 'account_date', 'account_value', 'notice']
		widgets = {'notice': forms.Textarea(attrs={'cols': 40, 'rows': 2})}


RATING_CHOICES=((1, "★☆☆☆☆☆☆☆☆☆"),
				(2, "★★☆☆☆☆☆☆☆☆"),
				(3, "★★★☆☆☆☆☆☆☆"),
				(4, "★★★★☆☆☆☆☆☆"),
				(5, "★★★★★☆☆☆☆☆"),
				(6, "★★★★★★☆☆☆☆"),
				(7, "★★★★★★★☆☆☆"),
				(8, "★★★★★★★★☆☆"),
				(9, "★★★★★★★★★☆"),
				(10, "★★★★★★★★★★"))