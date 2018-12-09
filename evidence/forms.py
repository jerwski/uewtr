# standart library
from datetime import date, timedelta

# django core
from django import forms

# datetime widget
from datetimewidget.widgets import DateTimeWidget, DateWidget

# my models
from evidence.models import WorkEvidence, EmployeeLeave, AccountPayment


# Create your forms here.


LEAVEKIND = [('unpaid_leave', 'Unpaid leave'), ('paid_leave', 'Paid leave'), ('maternity_leave', 'Maternity leave')]

dateOptions = {'format': 'yyyy-mm-dd', 'autoclose': 'true', 'showMeridian': 'false', 'weekStart': 1, 'todayBtn': 'true'}

dateTimeOptions = {'format': 'yyyy-mm-dd hh:ii','autoclose': 'true','showMeridian': 'false', 'weekStart': 1, 'todayBtn': 'true'}

if date.today().isoweekday() == 1:
    leave_date = date.today() - timedelta(days=3)
else:
    leave_date = date.today() - timedelta(days=1)


class WorkEvidenceForm(forms.ModelForm):
    start_work = forms.DateTimeField(widget=DateTimeWidget(options=dateTimeOptions, bootstrap_version=3), label="Date and time of start job:")
    end_work = forms.DateTimeField(widget=DateTimeWidget(options=dateTimeOptions, bootstrap_version=3), label="Date and time of end job:")

    class Meta:
        model = WorkEvidence
        fields = ['start_work', 'end_work']


class EmployeeLeaveForm(forms.ModelForm):
    leave_date = forms.DateField(widget=DateWidget(options=dateOptions, bootstrap_version=3), initial=leave_date)
    leave_flag = forms.ChoiceField(widget=forms.RadioSelect, choices=LEAVEKIND, label='Choice a kind of leave:')

    class Meta:
        model = EmployeeLeave
        fields = ['leave_date', 'leave_flag']


class ChoiceDateForm(forms.Form):
    choice_date = forms.DateField(widget=DateWidget(options=dateOptions, bootstrap_version=3), initial=date.today())


class AccountPaymentForm(forms.ModelForm):
    account_date = forms.DateField(widget=DateWidget(options=dateOptions, bootstrap_version=3), initial=leave_date, label='Check date of the advance payment')
    account_value = forms.DecimalField(decimal_places=2, min_value=10.00, label='Enter the value of the advance payment')

    class Meta:
        model = AccountPayment
        fields = ['account_date', 'account_value', 'notice']
        widgets = {'notice': forms.Textarea(attrs={'cols': 40, 'rows': 2})}
