# standard library
import calendar
from datetime import date, timedelta

# django library
from django.db.models import Sum, Q

# my models
from employee.models import EmployeeData, EmployeeHourlyRate
from evidence.models import WorkEvidence, EmployeeLeave, AccountPayment


# Create your payment functions here


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
            all_workhours = basic_work_hours['bwh'] + leave_paid_hours + leave_maternity_hours
            if all_workhours > monthly_work_hours:
                overhours = all_workhours - monthly_work_hours
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


def data_modal_chart(employee_id:int)->dict:
    years = set(WorkEvidence.objects.filter(worker_id=employee_id).values_list('start_work__year', flat=True))
    total_brutto_set = {year:sum([total_payment(employee_id,year,month)['brutto'] for month in range(1,13)]) for year in years}
    return total_brutto_set
