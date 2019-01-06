# standard library
import pathlib
from datetime import date, datetime, timedelta

# django library
from django.conf import settings
from django.core.mail import EmailMessage
from django.db.models import Sum, Case, When, Value, IntegerField

# my models
from employee.models import Employee, EmployeeData, EmployeeHourlyRate
from evidence.models import WorkEvidence, EmployeeLeave, AccountPayment


# Create your functions here


def holiday(year:int)->dict:
    '''return dictionary key=holiday name, value=date of holiday for current year'''
    year = int(year)
    a = year%19
    b = int(year/100)
    c = year%100
    d = int(b/4)
    e = b%4
    f = int((b + 8)/25)
    g = int((b - f + 1)/3)
    h = (19*a + b - d - g + 15)%30
    i = int(c/4)
    k = c%4
    l = (32 + 2*e + 2*i - h - k)%7
    m = int((a + 11*h + 22*l)/451)
    p = (h + l - 7*m + 114)%31
    day = int(p + 1)
    month = int((h + l - 7*m + 114)/31)

    holidays = {'New Year':  date(year, 1, 1),
                'Epiphany': date(year, 1, 6),
                'Easter': date(year,month,day),
                'Easter Monday': date(year,month,day)+timedelta(days=1),
                'Labour Day': date(year,5,1),
                'Feast of the constitution third of May': date(year,5,3),
                'Descent of the Holy Spirit': date(year,month,day)+timedelta(days=49),
                "God's Body": date(year,month,day)+timedelta(days=60),
                'Assumption of the Blessed Virgin Mary': date(year,8,15),
                'All Saints Day': date(year,11,1),
                'Independence Day': date(year,11,11),
                'Christmas-first day': date(year,12,25),
                'Christmas-second day': date(year,12,26)}

    return holidays


def sendPayroll(month:int, year:int):
    '''send e-mail with attached payroll in pdf format'''
    try:
        file = pathlib.Path(f'templates/pdf/payroll_{month}_{year}.pdf')
        subject = f'payrol for {month}/{year} r.'
        message = f'Payroll in attachment {month}-{year}...'
        email = EmailMessage(subject,message,settings.EMAIL_HOST_USER,['projekt@unikolor.com'])
        email.attach_file(file)
        email.send(fail_silently=True)
    except ConnectionError as err:
        print(err)


def sendLeavesData(employee_id:int):
    '''send e-mail with attached leave data in pdf format for specific employee'''
    try:
        file = pathlib.Path(f'templates/pdf/leaves_data_{employee_id}.pdf')
        employee = Employee.objects.get(pk=employee_id)
        subject = f'list of leave for {employee} ({date.today().year})r.'
        message = f'List of leave in attachment {employee} za {date.today().year}r.'
        email = EmailMessage(subject,message,settings.EMAIL_HOST_USER,['projekt@unikolor.com'])
        email.attach_file(file)
        email.send(fail_silently=True)
    except ConnectionError as err:
        print(err)


def initial_worktime_form(employee_id:int)->dict:
    '''return initial data for WorkEvidenceForm'''
    if date.today().isoweekday() == 1:
        if employee_id == 10:
            start_date = date.today() - timedelta(days=3)
            start_date = datetime(start_date.year, start_date.month,start_date.day,22,0)
            end_date = date.today() - timedelta(days=2)
            end_date = datetime(end_date.year, end_date.month, end_date.day,6,0)
        else:
            start_date = date.today() - timedelta(days=3)
            start_date = datetime(start_date.year, start_date.month,start_date.day,6,0)
            end_date = date.today() - timedelta(days=3)
            end_date = datetime(end_date.year, end_date.month, end_date.day,14,0)
    else:
        if employee_id == 10:
            start_date = date.today() - timedelta(days=1)
            start_date = datetime(start_date.year, start_date.month,start_date.day,22,0)
            end_date = date.today()
            end_date = datetime(end_date.year, end_date.month, end_date.day,6,0)
        else:
            start_date = date.today() - timedelta(days=1)
            start_date = datetime(start_date.year, start_date.month,start_date.day,6,0)
            end_date = date.today() - timedelta(days=1)
            end_date = datetime(end_date.year, end_date.month, end_date.day,14,0)

    context = {'start_work': start_date, 'end_work': end_date}

    return context


def initial_accountdate_form()->dict:
    '''return initial date for AccountPaymentForm'''
    account_date = date.today() - timedelta(days=int(date.today().day))
    context = {'account_date':account_date}

    return context


def initial_leave_form(employee_id:int)->dict:
    '''return initial leave_flag for EmployeeLeaveForm'''
    data = Employee.objects.get(pk=employee_id)
    if data.leave == 1:
        initial = {'leave_flag':['paid_leave',]}
    else:
        initial = {'leave_flag':['unpaid_leave',]}

    return initial


def erase_records(employee_id:int)->dict:
    context = dict()
    worker = Employee.objects.get(pk=employee_id)
    opt1, opt2 = {'worker': worker, 'then': Value(1)}, {'default': Value(0), 'output_field': IntegerField()}
    db = {EmployeeData._meta.verbose_name: EmployeeData,
          WorkEvidence._meta.verbose_name: WorkEvidence,
          EmployeeLeave._meta.verbose_name: EmployeeLeave,
          AccountPayment._meta.verbose_name: AccountPayment,
          EmployeeHourlyRate._meta.verbose_name: EmployeeHourlyRate,}

    for model_name, model in db.items():
        records = model.objects.aggregate(rec=Sum(Case(When(**opt1),**opt2)))
        context.__setitem__(model_name, records['rec'])

    return context


# function for listing whole tree for passed directory
def tree(directory):
    print(f'+ {directory}')
    for path in sorted(directory.rglob('*')):
        depth = len(path.relative_to(directory).parts)
        spacer = '    ' * depth
        print(f'{spacer}+ {path.name}')
