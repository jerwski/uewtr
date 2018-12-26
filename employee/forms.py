# django core
from django import forms

# datetime widget
from tempus_dominus.widgets import DatePicker

# my models
from employee.models import Employee, EmployeeData, EmployeeHourlyRate

# bootstrap4 widget
from bootstrap4.widgets import RadioSelectButtonGroup


# Create your forms here.


class EmployeeBasicDataForm(forms.ModelForm):
    '''class representing a form to create/change and save the basic data of employee'''
    forename = forms.CharField(max_length=100)
    surname = forms.CharField(max_length=100)

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
    options = {'icons': {'clear': 'fa fa-trash'}, 'useCurrent': True,
               'buttons': {'showToday': True, 'showClear': True, 'showClose': True}}
    attrs={'prepend': 'fa fa-calendar', 'append': 'fa fa-calendar', 'input_toggle': False, 'icon_toggle': True}

    worker = forms.ModelChoiceField(widget=forms.HiddenInput(attrs={'readonly': True}), queryset=Employee.objects.all())
    birthday = forms.DateField(label='Date of birthday', widget=DatePicker(options=options, attrs=attrs))
    start_contract = forms.DateField(label='Date of start contract', widget=DatePicker(options=options, attrs=attrs))
    end_contract = forms.DateField(required=False, label='Date of end contract', widget=DatePicker(options=options, attrs=attrs))
    overtime = forms.ChoiceField(label="Select the contract type...", required=True,
                                 widget=RadioSelectButtonGroup, choices=RATINGS, initial=0)


    class Meta:
        model = EmployeeData
        fields = ('worker', 'birthday', 'postal', 'city', 'street', 'house', 'flat',
                  'phone', 'workplace', 'start_contract', 'end_contract', 'overtime')
        widgets = {'city': forms.TextInput(attrs={'id':'cities'}),}


class EmployeeHourlyRateForm(forms.ModelForm):
    '''class representing a form to create/change and save the hourly rate data of employee'''
    hourly_rate = forms.DecimalField(min_value=7, max_digits=4, decimal_places=2)

    class Meta:
        model = EmployeeHourlyRate
        fields = ['hourly_rate']
