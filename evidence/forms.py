# django core
from django import forms

# datetime widget
from tempus_dominus.widgets import DateTimePicker, DatePicker

# my models
from evidence.models import WorkEvidence, EmployeeLeave, AccountPayment

# bootstrap4 widget
from bootstrap4.widgets import RadioSelectButtonGroup


# Create your forms here.


class WorkEvidenceForm(forms.ModelForm):
    options = {'icons': {'time': 'fa fa-clock-o'}, 'format': 'YYYY-MM-DD HH:mm',
               'useCurrent': False, 'stepping': 5, 'sideBySide': True,
               'buttons': {'showToday': True, 'showClear': True, 'showClose': True}}
    attrs={'prepend': 'fa fa-clock-o', 'append': 'fa fa-calendar', 'input_toggle': False, 'icon_toggle': True}

    start_work = forms.DateTimeField(label='Start of work (date and time):',
                                     widget=DateTimePicker(options=options, attrs=attrs))
    end_work = forms.DateTimeField(label='End of work (date and time):',
                                   widget=DateTimePicker(options=options, attrs=attrs))

    class Meta:
        model = WorkEvidence
        fields = ['start_work', 'end_work']


class EmployeeLeaveForm(forms.ModelForm):
    LEAVEKIND = [('unpaid_leave', 'Unpaid leave'), ('paid_leave', 'Paid leave'), ('maternity_leave', 'Maternity leave')]
    options = {'icons': {'clear': 'fa fa-trash'}, 'useCurrent': True, 'daysOfWeekDisabled': [0,6],
               'buttons': {'showToday': True, 'showClear': True, 'showClose': True}}
    attrs = {'prepend': 'fa fa-calendar', 'append': 'fa fa-calendar', 'input_toggle': False, 'icon_toggle': True}

    leave_date = forms.DateField(label='Select a date of leave...', widget=DatePicker(options=options, attrs=attrs))
    leave_flag = forms.ChoiceField(label="Select a kind of leave...", required=True,
                                   widget=RadioSelectButtonGroup, choices=LEAVEKIND)

    class Meta:
        model = EmployeeLeave
        fields = ['leave_date', 'leave_flag']


class PeriodCurrentComplexDataForm(forms.Form):
    options = {'icons': {'clear': 'fa fa-trash'}, 'useCurrent': True, 'format': 'MM/YYYY',
               'buttons': {'showToday': True, 'showClear': True, 'showClose': True}}
    attrs = {'prepend': 'fa fa-calendar', 'input_toggle': False, 'icon_toggle': True}

    choice_date = forms.DateField(widget=DatePicker(options=options, attrs=attrs))


class PeriodMonthlyPayrollForm(forms.Form):
    options = {'icons': {'clear': 'fa fa-trash'}, 'useCurrent': True, 'format': 'MM/YYYY',
               'buttons': {'showToday': True, 'showClear': True, 'showClose': True}}
    attrs = {'prepend': 'fa fa-calendar', 'append': 'fa fa-calendar', 'input_toggle': False, 'icon_toggle': True}

    choice_date = forms.DateField(label='Select a month on year...', widget=DatePicker(options=options, attrs=attrs))


class AccountPaymentForm(forms.ModelForm):
    options = {'icons': {'clear': 'fa fa-trash'}, 'useCurrent': True,
               'buttons': {'showToday': True, 'showClear': True, 'showClose': True}}
    attrs = {'prepend': 'fa fa-calendar', 'append': 'fa fa-calendar', 'input_toggle': False, 'icon_toggle': True}

    account_date = forms.DateField(label='Select date of the advance payment...',
                                   widget=DatePicker(options=options, attrs=attrs))

    account_value = forms.DecimalField(decimal_places=2, min_value=10.00, label='Enter the value of the advance payment...')

    class Meta:
        model = AccountPayment
        fields = ['account_date', 'account_value', 'notice']
        widgets = {'notice': forms.Textarea(attrs={'cols': 40, 'rows': 2})}
