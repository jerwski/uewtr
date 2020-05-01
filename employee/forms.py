# django core
from django import forms

# datetime widget
from tempus_dominus.widgets import DatePicker

# my models
from employee.models import Employee, EmployeeData, EmployeeHourlyRate

# bootstrap4 widget
from bootstrap4.widgets import RadioSelectButtonGroup


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
    forename = forms.CharField(max_length=100)
    surname = forms.CharField(max_length=100)
    pesel = forms.CharField(min_length=11, max_length=11)

    class Meta:
        model = Employee
        fields = ('forename', 'surname', 'pesel', 'status', 'leave')
        widgets = {'leave': forms.RadioSelect()}


class EmployeeExtendedDataForm(forms.ModelForm):
    '''class representing a form to create/change and save the extented data of employee'''
    NO_OVERTIME = 0
    WEEKLY_OVERTIME = 1
    SATURDAT_OVERTIME = 2
    RATINGS = [(NO_OVERTIME, 'Clear contract'), (WEEKLY_OVERTIME, 'Weekly overtime'), (SATURDAT_OVERTIME, 'Saturday overtime')]
    options = {'icons': icons, 'useCurrent': True,
               'buttons': {'showToday': True, 'showClear': True, 'showClose': True}}
    attrs={'prepend': 'fa fa-calendar-check', 'append': 'fa fa-calendar-check', 'input_toggle': False, 'icon_toggle': True}

    worker = forms.ModelChoiceField(widget=forms.HiddenInput(attrs={'readonly': True}), queryset=queryset)
    birthday = forms.DateField(label='Date of birthday', widget=DatePicker(options=options, attrs=attrs))
    start_contract = forms.DateField(label='Date of start contract', widget=DatePicker(options=options, attrs=attrs))
    end_contract = forms.DateField(required=False, label='Date of end contract', widget=DatePicker(options=options, attrs=attrs))
    overtime = forms.ChoiceField(label="Select the contract type...", required=True,
                                 widget=RadioSelectButtonGroup, choices=RATINGS, initial=0)
    class Meta:
        model = EmployeeData
        fields = ('worker', 'birthday', 'postal', 'city', 'street', 'house', 'flat',
                  'phone', 'workplace', 'start_contract', 'end_contract', 'overtime')
        widgets = {'city': forms.TextInput(attrs={'id':'autocpl'}),}


class EmployeeHourlyRateForm(forms.ModelForm):
    '''class representing a form to create/change and save the hourly rate data of employee'''
    worker = forms.ModelChoiceField(widget=forms.HiddenInput(attrs={'readonly': True}), queryset=queryset)
    hourly_rate = forms.FloatField(min_value=7)

    class Meta:
        model = EmployeeHourlyRate
        fields = ['worker', 'hourly_rate']