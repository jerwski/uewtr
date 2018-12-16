# standard library
import calendar
from collections import defaultdict
from datetime import date, timedelta

# pdfkit library
import pdfkit

# django library
from django.db.models import Sum, Q
from django.template.loader import render_to_string

# my models
from employee.models import Employee, EmployeeData, EmployeeHourlyRate
from evidence.models import WorkEvidence, EmployeeLeave, AccountPayment

# my function
from functions.myfunctions import holiday


# Create your payment functions here


def workingdays(year:int, month:int):
    '''return quanity of working days in a given year and month'''
    t = calendar.monthrange(year, month)
    start = date(year, month, 1)
    stop = date(start.year, start.month, t[1])
    while start <= stop:
        if start.weekday() < 5 and start not in holiday(year).values():
            yield start
        start += timedelta(1)


def saturday_payment(employee_id:int, year:int, month:int)->float:
    '''returns the employee's income for worked Saturdays in a given year and month'''
    satpay = 0
    employee = Employee.objects.get(id=employee_id)
    rate = EmployeeHourlyRate.objects.filter(name=employee, update__year__lte=year, update__month__lt=month).last()
    if rate is None:
        rate=EmployeeHourlyRate.objects.filter(name=employee).earliest('hourly_rate')
        rate = rate.hourly_rate
    else:
        rate = rate.hourly_rate

    query = Q(worker=employee) & Q(start_work__year=year) & Q(start_work__month=month) & Q(start_work__week_day=7) & (Q(end_work__week_day=7) | Q(end_work__week_day=1))
    saturday_hours = WorkEvidence.objects.filter(query).aggregate(sh=Sum('jobhours'))
    if saturday_hours['sh']:
        # satpay => remuneration for work on Saturday
        satpay = saturday_hours['sh'] * rate
        return satpay
    else:
        return satpay


def sunday_payment(employee_id:int, year:int, month:int)->float:
    '''returns the employee's income for worked Sundays in a given year and month'''
    sunpay = 0
    employee = Employee.objects.get(id=employee_id)
    rate = EmployeeHourlyRate.objects.filter(name=employee, update__year__lte=year, update__month__lt=month).last()
    if rate is None:
        rate=EmployeeHourlyRate.objects.filter(name=employee).earliest('hourly_rate')
        rate = rate.hourly_rate
    else:
        rate = rate.hourly_rate

    query = Q(worker=employee) & Q(start_work__year=year) & Q(start_work__month=month) & Q(start_work__week_day=1) & Q(end_work__week_day=1)
    sunday_hours = WorkEvidence.objects.filter(query).aggregate(sh=Sum('jobhours'))
    if sunday_hours['sh']:
        # sunpay => remuneration for work on Sunday
        sunpay = sunday_hours['sh'] * rate * 2
        return sunpay
    else:
        return sunpay


def overhours_payment(employee_id:int, year:int, month:int)->float:
    '''returns the employee's income for overtimes in a given year and month'''
    overhourspay, basic_work_hours = 0, 0
    employee = Employee.objects.get(id=employee_id)
    worker = EmployeeData.objects.get(name=employee)
    rate = EmployeeHourlyRate.objects.filter(name=employee, update__year__lte=year, update__month__lt=month).last()
    if rate is None:
        rate=EmployeeHourlyRate.objects.filter(name=employee).earliest('hourly_rate')
        rate = rate.hourly_rate
    else:
        rate = rate.hourly_rate

    if worker.overtime:
        # setting the overtime rate
        rate = rate/2
        # returns the number of working hours in a given month
        monthly_work_hours = len(list(workingdays(year, month))) * 8

        if worker.overtime == 1:
            # returns the number of hours worked without Saturdays and Sundays in a given year and month
            query = Q(worker=employee) & Q(start_work__year=year) & Q(start_work__month=month) & Q(start_work__week_day__gte=1) & Q(start_work__week_day__lt=7) & Q(end_work__week_day__gt=1)
            basic_work_hours = WorkEvidence.objects.filter(query)
        elif worker.overtime == 2:
            # returns the number of hours worked on Saturdays but no Sundays in a given year and month
            query = Q(worker=employee) & Q(start_work__year=year) & Q(start_work__month=month)
            basic_work_hours = WorkEvidence.objects.filter(query).exclude(start_work__week_day=1, end_work__week_day=1)

        # returns the number of paid holiday hours in a given year and month
        leave_paid_hours = EmployeeLeave.objects.filter(worker=employee, leave_date__year=year, leave_date__month=month)
        leave_paid_hours = leave_paid_hours.filter(leave_flag='paid_leave').count() * 8
        # returns the number of hours of maternity leave in a given year and month
        leave_maternity_hours = EmployeeLeave.objects.filter(worker=employee, leave_date__year=year, leave_date__month=month)
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
    basicpay = 0
    employee = Employee.objects.get(id=employee_id)
    rate = EmployeeHourlyRate.objects.filter(name=employee, update__year__lte=year, update__month__lt=month).last()
    if rate is None:
        rate=EmployeeHourlyRate.objects.filter(name=employee).earliest('hourly_rate')
        rate = rate.hourly_rate
    else:
        rate = rate.hourly_rate

    query = Q(worker=employee) & Q(start_work__year=year) & Q(start_work__month=month) & Q(start_work__week_day__gte=1) & Q(start_work__week_day__lt=7) & Q(end_work__week_day__gt=1)
    basic_work_hours = WorkEvidence.objects.filter(query)

    if basic_work_hours.exists():
        # returns the number of hours worked without Saturdays and Sundays in a given year and month
        basic_work_hours = basic_work_hours.aggregate(bwh=Sum('jobhours'))
        # returns the employee's basic salary in a given year and month
        basicpay = basic_work_hours['bwh'] * rate
        return basicpay
    else:
        return basicpay


def leave_payment(employee_id:int, year:int, month:int)->float:
    '''returns the employee's income for paid vacation in a given year and month'''
    leavepay = 0
    employee = Employee.objects.get(id=employee_id)
    rate = EmployeeHourlyRate.objects.filter(name=employee, update__year__lte=year, update__month__lt=month).last()
    if rate is None:
        rate=EmployeeHourlyRate.objects.filter(name=employee).earliest('hourly_rate')
        rate = rate.hourly_rate
    else:
        rate = rate.hourly_rate

    query = Q(worker=employee) & Q(leave_date__year=year) & Q(leave_date__month=month) & Q(leave_flag='paid_leave')
    leave_paid_hours = EmployeeLeave.objects.filter(query)

    if leave_paid_hours.exists():
        # returns the number of paid vacation hours in a given year and month
        leave_paid_hours = leave_paid_hours.count() * 8
        # returns the employee's remuneration for paid leave in a given year and month
        leavepay = leave_paid_hours * rate
        return leavepay
    else:
        return leavepay


def account_payment(employee_id:int, year:int, month:int)->float:
    '''returns the employee's income for paid vacation in a given year and month'''
    accountpay = 0
    employee = Employee.objects.get(id=employee_id)
    account_paid = AccountPayment.objects.filter(worker=employee, account_date__year=year, account_date__month=month)

    if account_paid.exists():
        account_paid = account_paid.aggregate(ap=Sum('account_value'))
        accountpay = account_paid['ap']
        return accountpay
    else:
        return accountpay


def total_payment(employee_id:int, year:int, month:int)->dict:
    '''returns the total payout for a given employee in a given month and year'''
    basicpay = basic_payment(employee_id, year, month)
    leavepay = leave_payment(employee_id, year, month)
    overhourspay = overhours_payment(employee_id, year, month)
    satpay = saturday_payment(employee_id, year, month)
    sunpay = sunday_payment(employee_id, year, month)
    accountpay = account_payment(employee_id, year, month)
    # returns the total wage for a given employee in a given year and month
    brutto = basicpay + leavepay + overhourspay + satpay + sunpay
    salary = brutto - accountpay
    context = {'brutto': brutto, 'basicpay': basicpay, 'leavepay': leavepay, 'overhourspay': overhourspay,
               'satpay': satpay, 'sunpay': sunpay, 'accountpay': accountpay, 'salary': salary}

    return context


def employee_total_data(work_date:date, employee_id:int, context:dict)->dict:
    '''returns complete data on the employee's wokrhours, rate, income in a given date'''
    employee = Employee.objects.get(id=employee_id)
    query = Q(worker=employee) & Q(start_work__year=work_date.year) & Q(start_work__month=work_date.month)
    total_hours = WorkEvidence.objects.filter(query)

    if total_hours.exists():
        total_hours = total_hours.aggregate(th=Sum('jobhours'))
        total_hours = total_hours['th']
    else:
        total_hours = 0

    query = Q(name=employee) & Q(update__year__lte=work_date.year) & Q(update__month__lt=work_date.month)
    rate = EmployeeHourlyRate.objects.filter(query).last()
    if rate is None:
        rate=EmployeeHourlyRate.objects.filter(name=employee).earliest('hourly_rate')
        rate = rate.hourly_rate
    else:
        rate = rate.hourly_rate

    context.__setitem__('total_hours', total_hours)
    context.__setitem__('rate', rate)
    payroll = total_payment(employee_id, work_date.year, work_date.month)
    context.update(payroll)
    brutto_income = payroll['salary'] + payroll['accountpay']
    context.__setitem__('brutto_income', brutto_income)
    return context


def payrollhtml2pdf(choice_date:date):
    '''convert html file (evidence/monthly_payroll_pdf.html) to pdf file'''
    heads = ['Imię i Nazwisko', 'Brutto', 'Podstawa', 'Urlop', 'Nadgodziny', 'Sobota', 'Niedziela', 'Zaliczka', 'Do wypłaty', 'Data i podpis']
    total_work_hours = len(list(workingdays(choice_date.year, choice_date.month))) * 8
    query = Q(end_contract__year__gte=choice_date.year) & Q(end_contract__month__gte=choice_date.month) | Q(name__status=True) & Q(start_contract__year__lte=choice_date.year) & Q(start_contract__month__lte=choice_date.month)
    employees = EmployeeData.objects.filter(query).order_by('name')
    # create data for payroll as associative arrays for every active employee
    payroll = {employee.name: total_payment(employee.id, choice_date.year, choice_date.month) for employee in employees}
    # create defaultdict with summary payment
    amountpay = defaultdict(float)
    for item in payroll.values():
        if item['accountpay'] != item['brutto']:
            for k,v in item.items():
                amountpay[k] += v

    context = {'heads': heads, 'payroll': payroll, 'amountpay': dict(amountpay),
               'choice_date': choice_date, 'total_work_hours': total_work_hours}

    html = render_to_string('evidence/monthly_payroll_pdf.html', context)
    # create pdf file and save on templates/pdf/payroll_{}_{}.pdf.format(choice_date.month, choice_date.year)
    options = {'page-size': 'A4', 'margin-top': '0.2in', 'margin-right': '0.1in',
               'margin-bottom': '0.1in', 'margin-left': '0.1in', 'encoding': "UTF-8",
               'orientation': 'landscape','no-outline': None, 'quiet': '', }

    pdfkit.from_string(html, r'templates/pdf/payroll_{}_{}.pdf'.format(choice_date.month, choice_date.year), options=options)


def leavehtml2pdf(employee_id:int):
    '''convert html annuall leave time for each employee in current yaear to pdf'''
    month_name = list(calendar.month_name)[1:]
    worker = Employee.objects.get(pk=employee_id)
    employee = EmployeeLeave.objects.filter(worker_id=employee_id).order_by('leave_date')
    # create leaves data as associative arrays for selected employee
    leave_data = {data.worker:[item.leave_date for item in employee] for data in employee}

    context = {'leave_data': leave_data, 'month_name': month_name, 'worker': worker}
    html = render_to_string(r'evidence/leaves_data.html', context)

    # create pdf file and save on templates/pdf/leves_data_{}.pdf'.format(employee_id)
    options = {'page-size': 'A4', 'margin-top': '1.0in', 'margin-right': '0.1in',
               'margin-bottom': '0.1in', 'margin-left': '0.1in', 'encoding': "UTF-8",
               'orientation': 'landscape','no-outline': None, 'quiet': '', }

    pdfkit.from_string(html, r'templates/pdf/leaves_data_{}.pdf'.format(employee_id), options=options)
