# django core
from django import forms

# datetime widget
from datetimewidget.widgets import DateWidget

# my models
from employee.models import Employee, EmployeeData, EmployeeHourlyRate


# Create your forms here.


dateOptions = {'format': 'yyyy-mm-dd', 'autoclose': 'true', 'showMeridian': 'false', 'weekStart': 1, 'todayBtn': 'true'}


class EmployeeBasicDataForm(forms.ModelForm):
    '''class representing a form to create/change and save the basic data of employee'''
    forename = forms.CharField(max_length=100)
    surname = forms.CharField(max_length=100)

    class Meta:
        model = Employee
        fields = ('forename', 'surname', 'pesel', 'status', 'leave')
        widgets = {'leave': forms.RadioSelect(attrs={'class':"form-check-input"})}


class EmployeeExtendedDataForm(forms.ModelForm):
    '''class representing a form to create/change and save the extented data of employee'''
    name = forms.ModelChoiceField(widget=forms.HiddenInput(attrs={'readonly': True}), queryset=Employee.objects.all())

    class Meta:
        model = EmployeeData
        fields = ('name', 'birthday', 'postal', 'city', 'street', 'house', 'flat',
                  'phone', 'workplace', 'start_contract', 'end_contract', 'overtime')
        widgets = {'birthday': DateWidget(options=dateOptions, bootstrap_version=3),
                   'start_contract': DateWidget(options=dateOptions, bootstrap_version=3),
                   'end_contract': DateWidget(options=dateOptions, bootstrap_version=3),
                   'overtime': forms.RadioSelect(attrs={'class':"form-check-input"})}


class EmployeeHourlyRateForm(forms.ModelForm):
    '''class representing a form to create/change and save the hourly rate data of employee'''
    hourly_rate = forms.DecimalField(min_value=7, max_digits=4, decimal_places=2)

    class Meta:
        model = EmployeeHourlyRate
        fields = ['hourly_rate']
