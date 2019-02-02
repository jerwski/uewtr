# matplotlib library
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


# Pillow library
from PIL import Image

# standard library
import calendar
from io import BytesIO
from pathlib import Path
from collections import defaultdict
from datetime import date, datetime, timedelta

# django library
from django.db.models import Q
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import get_template
from django.db.models import Sum, Case, When, Value, IntegerField

# my models
from employee.models import Employee, EmployeeData, EmployeeHourlyRate
from evidence.models import WorkEvidence, EmployeeLeave, AccountPayment

# my functions
from functions.payment import total_payment, workingdays
from employee.templatetags.utility_tags import money_format


# Create your functions here


def sendemail(subject:str, message:str, sender:int, recipient:list, attachment:str):
    email = EmailMessage(subject, message, sender, recipient)
    email.attach_file(attachment)
    email.send(fail_silently=True)


def sendPayroll(month:int, year:int):
    '''send e-mail with attached payroll in pdf format'''
    try:
        subject = f'payrol for {month}/{year} r.'
        message = f'Payroll in attachment {month}-{year}...'
        sender, recipient = settings.EMAIL_HOST_USER, ['projekt@unikolor.com']
        attachment = Path(f'templates/pdf/payroll_{month}_{year}.pdf')
        sendemail(subject, message, sender, recipient, attachment)
    except:
        raise ConnectionError


def sendLeavesData(employee_id:int):
    '''send e-mail with attached leave data in pdf format for specific employee'''
    try:
        employee = Employee.objects.get(pk=employee_id)
        subject = f'list of leave for {employee} ({date.today().year})r.'
        message = f'List of leave in attachment {employee} za {date.today().year}r.'
        sender, recipient = settings.EMAIL_HOST_USER,['projekt@unikolor.com']
        attachment = Path(f'templates/pdf/leaves_data_{employee_id}.pdf')
        sendemail(subject, message, sender, recipient, attachment)
    except:
        raise ConnectionError


def initial_worktime_form(work_hours:int)->dict:
    '''return initial data for WorkEvidenceForm'''
    hours = dict(zip([12,14,16,18,6],[6,6,6,6,22]))

    if date.today().isoweekday() == 1:
        if work_hours == 1:
            start_date = date.today() - timedelta(days=2)
            end_date = date.today() - timedelta(days=2)
        elif work_hours == 6:
            start_date = date.today() - timedelta(days=3)
            end_date = date.today() - timedelta(days=2)
        else:
            start_date = date.today() - timedelta(days=3)
            end_date = date.today() - timedelta(days=3)
    else:
        if work_hours == 6:
            start_date = date.today() - timedelta(days=1)
            end_date = date.today()
        else:
            start_date = date.today() - timedelta(days=1)
            end_date = date.today() - timedelta(days=1)

    start_date = datetime(start_date.year, start_date.month, start_date.day, hours[work_hours], 0)
    end_date = datetime(end_date.year, end_date.month, end_date.day, work_hours, 0)

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
    leave_date = date.today() - timedelta(days=1)
    initial= {'leave_date': leave_date}
    if data.leave == 1:
        initial.__setitem__('leave_flag', ['paid_leave',])
    else:
        initial.__setitem__('leave_flag', ['unpaid_leave',])

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


def data_chart(employee_id:int, year:int)->tuple:
    '''return data for Annual chart income for passed employee_id'''
    _, *month_name = list(calendar.month_name)
    brutto_income=[total_payment(employee_id,year,month)['brutto'] for month in range(1,13)]
    total_income = sum(brutto_income)
    income = dict(zip(reversed(month_name),reversed(brutto_income)))
    return income, total_income


def plot_chart(employee_id:int, year:int):
    worker = Employee.objects.get(pk=employee_id)
    income, total_income = data_chart(employee_id, year)
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(list(income.keys()), list(income.values()), color='green', label='Income')
    ax.grid(True, linestyle='-.', color='grey')
    fig.legend()
    labels = ax.get_xticklabels()
    plt.setp(labels, rotation=45, horizontalalignment='right')
    ax.set(xlabel='Value [PLN]', ylabel='Months', title=f'Incomes in {year} year for {worker} (total {total_income:,.2f} PLN)')
    for k, v in income.items():
        if 0<v<300:
            ax.set_xlim(0, max(list(income.values()))*1.25)
            plt.text(v+len(str(v)), k, money_format(v), ha='left', va='center', fontsize=10, fontweight='bold')
        elif v!=0:
            plt.text(v-len(str(v)), k, money_format(v), ha='right', va='center', fontsize=10, fontweight='bold')
    imgdata = BytesIO()
    fig.savefig(imgdata, format='png')
    imgdata.seek(0)  # rewind the data
    chart = Image.open(imgdata)
    chart.show()


def payrollhtml2pdf(month:int, year:int)->bool:
    '''convert html file (evidence/monthly_payroll_pdf.html) to pdf file'''
    heads = ['Imię i Nazwisko', 'Brutto', 'Podstawa', 'Urlop', 'Nadgodziny', 'Sobota', 'Niedziela', 'Zaliczka', 'Do wypłaty', 'Data i podpis']
    total_work_hours = len(list(workingdays(year, month))) * 8
    employees = Employee.objects.all()
    # building complex query for actual list of employee
    day = calendar.monthrange(year, month)[1]
    query = Q(employeedata__end_contract__lt=date(year,month,1))|Q(employeedata__start_contract__gt=date(year,month,day))
    employees = employees.exclude(query).order_by('surname')
    if employees.exists():
        # create data for payroll as associative arrays for all employees
        payroll = {employee: total_payment(employee.id, year, month) for employee in employees}
        # create defaultdict with summary payment
        amountpay = defaultdict(float)
        for item in payroll.values():
            if item['accountpay'] != item['brutto']:
                for k,v in item.items():
                    amountpay[k] += v

        context = {'heads': heads, 'payroll': payroll, 'amountpay': dict(amountpay),
                   'year': year, 'month': month, 'total_work_hours': total_work_hours}

        template = get_template('evidence/monthly_payroll_pdf.html')
        html = template.render(context)
        return html
    else:
        return False


def leavehtml2pdf(employee_id:int, year:int):
    '''convert html annuall leave time for each employee in current year to pdf'''
    month_name = list(calendar.month_name)[1:]
    worker = Employee.objects.get(pk=employee_id)
    employee = EmployeeLeave.objects.filter(worker=worker, leave_date__year=year)
    if employee.exists():
        employee = employee.order_by('leave_date')
        # create leaves data as associative arrays for selected employee
        leave_data = [item.leave_date for item in employee]
        context = {'leave_data': leave_data, 'month_name': month_name, 'worker': worker, 'year': year}
        template = get_template(r'evidence/leaves_data.html')
        html = template.render(context)
        return html
    else:
        return False


def tree(directory):
    '''listing whole tree for passed directory'''
    print(f'+ {directory}')
    for path in sorted(directory.rglob('*')):
        depth = len(path.relative_to(directory).parts)
        spacer = '    ' * depth
        print(f'{spacer}+ {path.name}')


def remgarbage(*paths):
    '''removes attachment pdf file'''
    for path in paths:
        for file in Path.iterdir(path):
            if file.match('leaves_data_*.pdf')|file.match('payroll_*.pdf'):
                file.unlink()
