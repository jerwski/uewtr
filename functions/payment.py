# standard library
import os
import calendar
from pathlib import Path
from collections import defaultdict
from datetime import date, timedelta


# pdfkit library
import pdfkit

# matplotlib library
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# django library
from django.db.models import Sum, Q
from django.template.loader import render_to_string

# my models
from employee.models import Employee, EmployeeData, EmployeeHourlyRate
from evidence.models import WorkEvidence, EmployeeLeave, AccountPayment

# my function
from functions.myfunctions import holiday


# Create your payment functions here


def worker_rate(employee_id:int, year:int, month:int)->float:
    day = calendar.monthrange(year, month)
    rate = EmployeeHourlyRate.objects.filter(worker_id=employee_id, update__lte=date(year, month, day[1])).last()
    if rate is None:
        rate=EmployeeHourlyRate.objects.filter(worker_id=employee_id).earliest('hourly_rate')
        rate = rate.hourly_rate
    else:
        rate = rate.hourly_rate
    return rate


def workingdays(year:int, month:int):
    '''return quanity of working days in a given year and month'''
    day = calendar.monthrange(year, month)[1]
    start = date(year, month, 1)
    stop = date(start.year, start.month, day)
    while start <= stop:
        if start.weekday() < 5 and start not in holiday(year).values():
            yield start
        start += timedelta(1)


def saturday_payment(employee_id:int, year:int, month:int)->float:
    '''returns the employee's income for worked Saturdays without Holidays in a given year and month'''
    satpay = 0
    rate= worker_rate(employee_id, year, month)
    holidays = holiday(year).values()
    mainquery = Q(worker_id=employee_id) & Q(start_work__year=year) & Q(start_work__month=month)
    saturdaysquery = Q(start_work__week_day=7) & (Q(end_work__week_day=7) | Q(end_work__week_day=1))
    exclude_holidays = Q(start_work__date__in=list(holidays)) & Q(end_work__date__in=list(holidays))
    saturday_hours = WorkEvidence.objects.filter(mainquery&saturdaysquery).exclude(exclude_holidays)
    if saturday_hours.exists():
        # satpay => remuneration for work on Saturday without Holidays
        satpay = saturday_hours.aggregate(sh=Sum('jobhours') * rate)
        satpay = satpay['sh']
    return satpay


def sunday_payment(employee_id:int, year:int, month:int)->float:
    '''returns the employee's income for worked Sundays without Holidays in a given year and month'''
    sunpay = 0
    rate= worker_rate(employee_id, year, month)
    holidays = holiday(year).values()
    mainquery = Q(worker_id=employee_id) & Q(start_work__year=year) & Q(start_work__month=month)
    sundaysquery = Q(start_work__week_day=1) & Q(end_work__week_day=1)
    exclude_holidays = Q(start_work__date__in=list(holidays)) & Q(end_work__date__in=list(holidays))
    sunday_hours = WorkEvidence.objects.filter(mainquery&sundaysquery).exclude(exclude_holidays)
    if sunday_hours.exists():
        # sunpay => remuneration for work on Sunday without Holidays
        sunpay = sunday_hours.aggregate(sh=Sum('jobhours') * rate * 2)
        sunpay = sunpay['sh']
    return sunpay


def holiday_payment(employee_id:int, year:int, month:int)->float:
    '''returns the employee's income for worked Holidays in a given year and month'''
    holidaypay = 0
    rate= worker_rate(employee_id, year, month)
    holidays = holiday(year).values()
    mainquery = Q(worker_id=employee_id) & Q(start_work__year=year) & Q(start_work__month=month)
    holidays_query = Q(start_work__date__in=list(holidays)) & Q(end_work__date__in=list(holidays))
    holiday_hours = WorkEvidence.objects.filter(mainquery&holidays_query)
    if holiday_hours.exists():
        # holidaypay => remuneration for work on Holidays
        holidaypay = holiday_hours.aggregate(hh=Sum('jobhours') * rate * 2)
        holidaypay = holidaypay['hh']
    return holidaypay


def overhours_payment(employee_id:int, year:int, month:int)->float:
    '''returns the employee's income for overtimes in a given year and month'''
    overhourspay, basic_work_hours = 0, 0
    worker_exdata = EmployeeData.objects.get(worker_id=employee_id)
    rate= worker_rate(employee_id, year, month)

    if worker_exdata.overtime:
        # setting the overtime rate
        rate = rate/2
        # returns the number of working hours in a given month
        monthly_work_hours = len(list(workingdays(year, month))) * 8
        holidays = holiday(year).values()
        mainquery = Q(worker_id=employee_id) & Q(start_work__year=year) & Q(start_work__month=month)
        filterquery = Q(start_work__week_day__range=[1,6]) & Q(end_work__week_day__gt=1)
        exclude_sundays = Q(start_work__week_day=1) & Q(end_work__week_day=1)
        exclude_holidays = Q(start_work__date__in=list(holidays)) & Q(end_work__date__in=list(holidays))

        if worker_exdata.overtime == 1:
            # returns the number of hours worked without Holidyas Saturdays and Sundays in a given year and month
            basic_work_hours = WorkEvidence.objects.filter(mainquery&filterquery).exclude(exclude_holidays)
        elif worker_exdata.overtime == 2:
            # returns the number of hours worked on Saturdays but no Sundays and Holidays in a given year and month
            basic_work_hours = WorkEvidence.objects.filter(mainquery).exclude(exclude_sundays)
            basic_work_hours = basic_work_hours.exclude(exclude_holidays)

        # returns the number of paid holiday hours in a given year and month
        leave_paid_hours = EmployeeLeave.objects.filter(worker_id=employee_id, leave_date__year=year, leave_date__month=month)
        leave_paid_hours = leave_paid_hours.filter(leave_flag='paid_leave').count() * 8
        # returns the number of hours of maternity leave in a given year and month
        leave_maternity_hours = EmployeeLeave.objects.filter(worker_id=employee_id, leave_date__year=year, leave_date__month=month)
        leave_maternity_hours = leave_maternity_hours.filter(leave_flag='maternity_leave').count() * 8
        # returns the number of overtime for a given employee in the selected year and month
        if basic_work_hours.exists():
            basic_work_hours = basic_work_hours.aggregate(bwh=Sum('jobhours'))
            if basic_work_hours['bwh'] > monthly_work_hours:
                overhours = basic_work_hours['bwh'] + leave_paid_hours + leave_maternity_hours - monthly_work_hours
                overhourspay = overhours * rate
                return overhourspay
            else:
                return overhourspay
        else:
            return overhourspay
    else:
        return overhourspay


def basic_payment(employee_id:int, year:int, month:int)->float:
    '''returns the employee's basic income (without Saturdays, Sundays, holidays) in a given year and month'''
    rate= worker_rate(employee_id, year, month)
    holidays = holiday(year).values()
    mainquery = Q(worker_id=employee_id) & Q(start_work__year=year) & Q(start_work__month=month)
    filterquery = Q(start_work__week_day__range=[1,6]) & Q(end_work__week_day__gt=1)
    exclude_holidays = Q(start_work__date__in=list(holidays)) & Q(end_work__date__in=list(holidays))
    basic_work_hours = WorkEvidence.objects.filter(mainquery&filterquery).exclude(exclude_holidays)
    if basic_work_hours.exists():
        # returns the employee's basic salary in a given year and month
        basicpay = basic_work_hours.aggregate(bwh=Sum('jobhours') * rate)
        basicpay = basicpay['bwh']
    else:
        basicpay = 0
    return basicpay


def leave_payment(employee_id:int, year:int, month:int)->float:
    '''returns the employee's income for paid vacation in a given year and month'''
    rate= worker_rate(employee_id, year, month)
    query = Q(worker_id=employee_id) & Q(leave_date__year=year) & Q(leave_date__month=month) & Q(leave_flag='paid_leave')
    leave_paid_hours = EmployeeLeave.objects.filter(query)

    if leave_paid_hours.exists():
        # returns the employee's remuneration for paid leave in a given year and month
        leavepay = leave_paid_hours.count() * 8 * rate
    else:
        leavepay = 0
    return leavepay


def account_payment(employee_id:int, year:int, month:int)->float:
    '''returns the employee's income for paid vacation in a given year and month'''
    account_paid = AccountPayment.objects.filter(worker_id=employee_id, account_date__year=year, account_date__month=month)

    if account_paid.exists():
        account_paid = account_paid.aggregate(ap=Sum('account_value'))
        accountpay = account_paid['ap']
    else:
        accountpay = 0
    return accountpay


def total_payment(employee_id:int, year:int, month:int)->dict:
    '''returns the total payout for a given employee in a given month and year'''
    basicpay = basic_payment(employee_id, year, month)
    leavepay = leave_payment(employee_id, year, month)
    overhourspay = overhours_payment(employee_id, year, month)
    satpay = saturday_payment(employee_id, year, month)
    sunpay = sunday_payment(employee_id, year, month)
    holipay = holiday_payment(employee_id, year, month)
    if holipay:
        sunpay += holipay
    accountpay = account_payment(employee_id, year, month)
    # returns the total wage for a given employee in selected year and month
    brutto = basicpay + leavepay + overhourspay + satpay + sunpay
    salary = brutto - accountpay
    context = {'brutto': brutto, 'basicpay': basicpay, 'leavepay': leavepay, 'overhourspay': overhourspay,
               'satpay': satpay, 'sunpay': sunpay, 'accountpay': accountpay, 'salary': salary}

    return context


def employee_total_data(employee_id:int, year:int, month:int, context:dict)->dict:
    '''returns complete data on the employee's wokrhours, rate, income in a given date'''
    rate= worker_rate(employee_id, year, month)
    query = Q(worker_id=employee_id) & Q(start_work__year=year) & Q(start_work__month=month)
    total_hours = WorkEvidence.objects.filter(query)

    if total_hours.exists():
        total_hours = total_hours.aggregate(th=Sum('jobhours'))
        total_hours = total_hours['th']
    else:
        total_hours = 0

    context.__setitem__('total_hours', total_hours)
    context.__setitem__('rate', rate)
    payroll = total_payment(employee_id, year, month)
    context.update(payroll)
    return context


def total_brutto_set(employee_id):
    total_brutto = dict()
    if WorkEvidence.objects.filter(worker_id=employee_id).exists():
        for year in [year for year in range(WorkEvidence.objects.filter(worker_id=employee_id).earliest('start_work').start_work.year, date.today().year + 1)]:
            total_brutto.__setitem__(year,{month:WorkEvidence.objects.filter(worker_id=10,start_work__year=2018,start_work__month=month).aggregate(Sum('jobhours')) for month in range(1,13)})
    else:
        total_brutto = None
    context = {'total_brutto_set': total_brutto}
    return context


def data_chart(employee_id:int, year:int)->dict:
    '''return data for Annual chart income for passed employee_id'''
    month_name = list(calendar.month_name)[1:]
    brutto_income=[total_payment(employee_id,year,month)['brutto'] for month in range(1,13)]
    incomes = dict(zip(month_name,brutto_income))

    return incomes


def plot_chart(employee_id:int, year:int):
    worker = Employee.objects.get(pk=employee_id)
    incomes = data_chart(employee_id, year)
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(list(incomes.keys()), list(incomes.values()), color='green')
    labels = ax.get_xticklabels()
    plt.setp(labels, rotation=45, horizontalalignment='right')
    ax.set(xlabel='Months', ylabel='Value [PLN]', title=f'Incomes in {year} year for {worker}')
    image = Path.cwd().joinpath(f'templates/pdf/income.png')
    plt.savefig(image, transparent=False, dpi=144, bbox_inches="tight")
    plt.close(fig)
    try:
        os.popen(f'explorer.exe "file:///{image}"')
    except:
        raise FileNotFoundError


def payrollhtml2pdf(month:int, year:int):
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
    '''convert html annuall leave time for each employee in current yaear to pdf'''
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
