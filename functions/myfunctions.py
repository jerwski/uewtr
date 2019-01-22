# matplotlib library
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# standard library
import os
import calendar
from pathlib import Path
from collections import defaultdict
from datetime import date, datetime, timedelta

# pdfkit library
import pdfkit

# django library
from django.db.models import Q
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.db.models import Sum, Case, When, Value, IntegerField

# my models
from employee.models import Employee, EmployeeData, EmployeeHourlyRate
from evidence.models import WorkEvidence, EmployeeLeave, AccountPayment

# my functions
from functions.payment import total_payment, workingdays
from employee.templatetags.utility_tags import money_format


# Create your functions here


def sendPayroll(month:int, year:int):
    '''send e-mail with attached payroll in pdf format'''
    try:
        file = Path(f'templates/pdf/payroll_{month}_{year}.pdf')
        subject = f'payrol for {month}/{year} r.'
        message = f'Payroll in attachment {month}-{year}...'
        email = EmailMessage(subject,message,settings.EMAIL_HOST_USER,['projekt@unikolor.com'])
        email.attach_file(file)
        email.send(fail_silently=True)
    except:
        raise ConnectionError


def sendLeavesData(employee_id:int):
    '''send e-mail with attached leave data in pdf format for specific employee'''
    try:
        file = Path(f'templates/pdf/leaves_data_{employee_id}.pdf')
        employee = Employee.objects.get(pk=employee_id)
        subject = f'list of leave for {employee} ({date.today().year})r.'
        message = f'List of leave in attachment {employee} za {date.today().year}r.'
        email = EmailMessage(subject,message,settings.EMAIL_HOST_USER,['projekt@unikolor.com'])
        email.attach_file(file)
        email.send(fail_silently=True)
    except:
        raise ConnectionError


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


def data_chart(employee_id:int, year:int)->dict:
    '''return data for Annual chart income for passed employee_id'''
    _, *month_name = list(calendar.month_name)
    brutto_income=[total_payment(employee_id,year,month)['brutto'] for month in range(1,13)]
    incomes = dict(zip(reversed(month_name),reversed(brutto_income)))
    return incomes


def plot_chart(employee_id:int, year:int):
    worker = Employee.objects.get(pk=employee_id)
    incomes = data_chart(employee_id, year)
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.barh(list(incomes.keys()), list(incomes.values()), color='green', label='Income')
    ax.grid(True, linestyle='-.', color='grey')
    fig.legend()
    labels = ax.get_xticklabels()
    plt.setp(labels, rotation=45, horizontalalignment='right')
    ax.set(xlabel='Value [PLN]', ylabel='Months', title=f'Incomes in {year} year for {worker}')
    for k, v in incomes.items():
        if 0<v<300:
            ax.set_xlim(0, max(list(incomes.values()))*1.25)
            plt.text(v+len(str(v)), k, money_format(v), ha='left', va='center', fontsize=10, fontweight='bold')
        elif v!=0:
            plt.text(v-len(str(v)), k, money_format(v), ha='right', va='center', fontsize=10, fontweight='bold')
    image = Path.cwd().joinpath(f'templates/pdf/income.png')
    plt.savefig(image, transparent=False, dpi=144, bbox_inches="tight")
    plt.close(fig)
    try:
        os.popen(f'explorer.exe "file:///{image}"')
    except:
        raise FileNotFoundError


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

        html = render_to_string('evidence/monthly_payroll_pdf.html', context)
        # create pdf file and save on templates/pdf/payroll_{}_{}.pdf.format(choice_date.month, choice_date.year)
        options = {'page-size': 'A4', 'margin-top': '0.2in', 'margin-right': '0.1in',
                   'margin-bottom': '0.1in', 'margin-left': '0.1in', 'encoding': "UTF-8",
                   'orientation': 'landscape','no-outline': None, 'quiet': '', }
        # create pdf file
        pdfkit.from_string(html, f'templates/pdf/payroll_{month}_{year}.pdf', options=options)
        return True
    else:
        return False


def leavehtml2pdf(employee_id:int, year:int):
    '''convert html annuall leave time for each employee in current year to pdf'''
    month_name = list(calendar.month_name)[1:]
    worker = Employee.objects.get(pk=employee_id)
    employee = EmployeeLeave.objects.filter(worker=worker, leave_date__year=year).order_by('leave_date')
    # create leaves data as associative arrays for selected employee
    leave_data = [item.leave_date for item in employee]
    context = {'leave_data': leave_data, 'month_name': month_name, 'worker': worker, 'year': year}
    html = render_to_string(r'evidence/leaves_data.html', context)

    # create pdf file and save on templates/pdf/leves_data_{}.pdf'.format(employee_id)
    options = {'page-size': 'A4', 'margin-top': '1.0in', 'margin-right': '0.1in',
               'margin-bottom': '0.1in', 'margin-left': '0.1in', 'encoding': "UTF-8",
               'orientation': 'landscape','no-outline': None, 'quiet': '', }

    pdfkit.from_string(html, f'templates/pdf/leaves_data_{employee_id}.pdf', options=options)


# function for listing whole tree for passed directory
def tree(directory):
    print(f'+ {directory}')
    for path in sorted(directory.rglob('*')):
        depth = len(path.relative_to(directory).parts)
        spacer = '    ' * depth
        print(f'{spacer}+ {path.name}')
