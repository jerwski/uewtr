# standard library
import pathlib
import unicodedata
from datetime import date, timedelta, datetime

# django library
from django.conf import settings
from django.core.mail import EmailMessage

# my models
from employee.models import Employee


# Create your functions here


def diacritical_remover(text:str)->str:
    '''replace polish diacritical chars on latin and return as lowercase'''
    result = [char for char in unicodedata.normalize('NFD', text.lower()) if not unicodedata.combining(char)]

    for i in range(len(text)):
        if result[i] == 'ł':
            result[i] = 'l'
    return ''.join(result)


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


def sendPayroll(choice_date:date):
    '''send e-mail with attached payroll in pdf format'''
    try:
        file = pathlib.Path(r'templates/pdf/payroll_{}_{}.pdf'.format(choice_date.month, choice_date.year))
        subject = 'lista płac dla {}/{} r.'.format(choice_date.month, choice_date.year)
        message = 'W załączniku lista płac za {}-{}...'.format(choice_date.month, choice_date.year)
        email = EmailMessage(subject,message,settings.EMAIL_HOST_USER,['projekt@unikolor.com'])
        email.attach_file(file)
        email.send(fail_silently=True)
    except ConnectionError as err:
        print(err)


def sendLeavesData(employee_id:int):
    '''send e-mail with attached leave data in pdf format for specific employee'''
    try:
        file = pathlib.Path(r'templates/pdf/leaves_data_{}.pdf'.format(employee_id))
        employee = Employee.objects.get(pk=employee_id)
        subject = 'zestawienie urlopów dla {} ({})r.'.format(employee, date.today().year)
        message = 'W załączniku zestawienie urlopów dla {} za {}r.'.format(employee, date.today().year)
        email = EmailMessage(subject,message,settings.EMAIL_HOST_USER,['projekt@unikolor.com'])
        email.attach_file(file)
        email.send(fail_silently=True)
    except ConnectionError as err:
        print(err)


def initial_date(employee_id:int)->dict:
    '''return initial data for WorkEvidenceForm'''
    if date.today().isoweekday() == 1:
        if employee_id == 10:
            start_date = date.today() - timedelta(days=3)
            start_date = datetime(start_date.year, start_date.month,start_date.day,22,0,0)
            end_date = date.today() - timedelta(days=2)
            end_date = datetime(end_date.year, end_date.month, end_date.day,6,0,0)
        else:
            start_date = date.today() - timedelta(days=3)
            start_date = datetime(start_date.year, start_date.month,start_date.day,6,0,0)
            end_date = date.today() - timedelta(days=3)
            end_date = datetime(end_date.year, end_date.month, end_date.day,14,0,0)
    else:
        if employee_id == 10:
            start_date = date.today() - timedelta(days=1)
            start_date = datetime(start_date.year, start_date.month,start_date.day,22,0,0)
            end_date = date.today()
            end_date = datetime(end_date.year, end_date.month, end_date.day,6,0,0)
        else:
            start_date = date.today() - timedelta(days=1)
            start_date = datetime(start_date.year, start_date.month,start_date.day,6,0,0)
            end_date = date.today() - timedelta(days=1)
            end_date = datetime(end_date.year, end_date.month, end_date.day,14,0,0)

    context = {'start_work': start_date, 'end_work': end_date}

    return context


def initial_accountdate()->dict:
    '''return initial date for AccountPaymentForm'''
    account_date = date.today() - timedelta(days=int(date.today().day))
    context = {'account_date':account_date}

    return context


def initial_leave_flag(employee_id:int)->dict:
    '''return initial leave_flag for EmployeeLeaveForm'''
    data = Employee.objects.get(pk=employee_id)
    if data.leave == 1:
        initial = {'leave_flag':['paid_leave',]}
    else:
        initial = {'leave_flag':['unpaid_leave',]}

    return initial
