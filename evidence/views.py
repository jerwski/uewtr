# standard library
import os
from pathlib import Path
from collections import defaultdict
from datetime import date, datetime

# django core
from django.urls import reverse
from django.contrib import messages
from django.db.models import Sum, Q
from django.views.generic import View
from django.shortcuts import render, HttpResponseRedirect

# my forms
from evidence.forms import (WorkEvidenceForm, EmployeeLeaveForm, AccountPaymentForm,
                            PeriodCurrentComplexDataForm, PeriodMonthlyPayrollForm)

# my models
from employee.models import Employee, EmployeeData
from evidence.models import WorkEvidence, EmployeeLeave, AccountPayment

# my function
from functions.myfunctions import (sendPayroll, sendLeavesData, initial_leave_form,
                                   holiday, initial_worktime_form, initial_accountdate_form)
from functions.payment import total_payment, workingdays, employee_total_data, payrollhtml2pdf, leavehtml2pdf


# Create your views here.


class WorkingTimeRecorderView(View):
    '''class implementing the method of adding working time for specific employee'''
    def get(self, request, employee_id:int, default_work:int=0)->render:
        worker = Employee.objects.get(pk=employee_id)
        employees = Employee.objects.filter(employeedata__end_contract__isnull=True, status=True).order_by('surname')
        query = Q(worker=worker) & (Q(overtime=1)|Q(overtime=2))
        overhours = EmployeeData.objects.filter(query).exists()
        context = {'worker': worker, 'employee_id': employee_id, 'employees': employees, 'overhours': overhours}
        employee_total_data(date.today().month, date.today().year, employee_id, context)

        if default_work:
            initial = initial_worktime_form(employee_id)
            form = WorkEvidenceForm(initial=initial)
            context.__setitem__('form', form)
            context.__setitem__('default_work', True)
        else:
            form = WorkEvidenceForm()
            context.__setitem__('form', form)
            context.__setitem__('default_work', False)

        return render(request, 'evidence/working_time_recorder.html', context)


    def post(self, request, employee_id:int)->render:
        form = WorkEvidenceForm(data=request.POST)
        worker = Employee.objects.get(id=employee_id)
        employees = Employee.objects.filter(employeedata__end_contract__isnull=True, status=True).order_by('surname')
        query = Q(worker=worker) & (Q(overtime=1)|Q(overtime=2))
        overhours = EmployeeData.objects.filter(query).exists()
        context = {'form': form, 'worker': worker, 'employee_id': employee_id, 'employees': employees, 'overhours': overhours}

        if form.is_valid():
            data = form.cleaned_data
            data.__setitem__('worker', worker)
            start_work, end_work = data['start_work'], data['end_work']
            jobhours = (end_work - start_work).total_seconds()/3600
            data.__setitem__('jobhours', jobhours)
            context.__setitem__('start_work', start_work)
            context.__setitem__('end_work', end_work)
            context.__setitem__('jobhours', jobhours)
            year, month = start_work.year, start_work.month

            # check or data exisiting in WorkEvidence and EmployeeLeave table
            check_leave = {'worker': worker, 'leave_date': start_work.date(),}
            flag_leave = EmployeeLeave.objects.filter(**check_leave).exists()
            query = Q(worker=worker) & Q(start_work__year=year) & Q(start_work__month=month) & Q(start_work__day=start_work.day) & Q(end_work__day=end_work.day)
            flag_work = WorkEvidence.objects.filter(query).exists()

            if start_work < end_work:

                if flag_work or flag_leave:
                    messages.error(request, f'For worker {worker} this date ({start_work.date()}) is existing in database...')
                    context.__setitem__('flag_work', flag_work)
                    context.__setitem__('flag_leave', flag_leave)

                else:
                    WorkEvidence.objects.create(**data)
                    messages.success(request, f'Succesful register new time working for {worker}')
                    employee_total_data(month, year, employee_id, context)

            elif start_work <= end_work:
                msg = f'Start working ({start_work}) is the same like end working ({end_work}). Please correct it...'
                messages.error(request, msg)
            else:
                msg = f'Start working ({start_work}) is later than end working ({end_work}). Please correct it...'
                messages.error(request, msg)

            employee_total_data(month, year, employee_id, context)

        return render(request, 'evidence/working_time_recorder.html', context)


class WorkingTimeRecorderEraseView(View):
    '''class implementing the method of erase last added working time record for specific employee'''
    def get(self, request, employee_id:int, start_work:str, end_work:str)->HttpResponseRedirect:
        worker = Employee.objects.get(id=employee_id)
        check = WorkEvidence.objects.filter(worker=worker, start_work=start_work, end_work=end_work)
        if check.exists():
            check.delete()
            msg = f'Succesful erase last record for {worker}'
            messages.success(request, msg)

        kwargs = {'employee_id': employee_id}

        return HttpResponseRedirect(reverse('evidence:working_time_recorder_add', kwargs=kwargs))


class LeaveTimeRecorderView(View):
    '''class implementing the method of adding leave time for specific employee'''
    def get(self, request, employee_id:int)->render:
        form = EmployeeLeaveForm(initial=initial_leave_form(employee_id))
        worker = Employee.objects.get(id=employee_id)
        employees = Employee.objects.filter(employeedata__end_contract__isnull=True, status=True).order_by('surname')
        values = {'worker':worker, 'leave_date__year': date.today().year}
        total_leaves = EmployeeLeave.objects.filter(**values).order_by('leave_date')
        remaining_leave = 26 - total_leaves.filter(leave_flag='paid_leave').count()
        leave_set = {year:EmployeeLeave.objects.filter(worker=worker, leave_date__year=year).count() for year in [year for year in range(EmployeeLeave.objects.filter(worker=worker).earliest('leave_date').leave_date.year, date.today().year + 1)]}
        context = {'form': form, 'worker': worker, 'employee_id': employee_id,
                   'employees': employees, 'year': date.today().year, 'leave_set': leave_set,
                   'total_leaves': total_leaves.count(), 'remaining_leave': remaining_leave}
        context.__setitem__('leaves_pl', total_leaves.filter(leave_flag='paid_leave'))
        context.__setitem__('leaves_upl', total_leaves.filter(leave_flag='unpaid_leave'))
        context.__setitem__('leaves_ml', total_leaves.filter(leave_flag='maternity_leave'))
        return render(request, 'evidence/leave_time_recorder.html', context)

    def post(self, request, employee_id:int)->render:
        name_holiday, flag_weekend = False, False
        form = EmployeeLeaveForm(data=request.POST)
        worker = Employee.objects.get(id=employee_id)
        employees = Employee.objects.filter(employeedata__end_contract__isnull=True, status=True).order_by('surname')

        context = {'form': form, 'worker': worker, 'employees': employees, 'employee_id': employee_id}

        if form.is_valid():
            data = form.cleaned_data
            leave_date = data['leave_date']
            leave_flag = data['leave_flag']
            context.__setitem__('leave_date', leave_date)
            data.__setitem__('worker', worker)

            # check or data exisiting in WorkEvidence and EmployeeLeave table or isn't Sunday or Saturday
            check_leave = {'worker': worker, 'leave_date': leave_date}
            flag_leave = EmployeeLeave.objects.filter(**check_leave).exists()

            if leave_date.isoweekday() == 7 or leave_date.isoweekday() == 6:
                flag_weekend = True

            for name, date_holiday in holiday(leave_date.year).items():
                if date_holiday == leave_date:
                    name_holiday = name

            query = Q(worker=worker) & Q(start_work__year=leave_date.year) & Q(start_work__month=leave_date.month) & Q(start_work__day=leave_date.day)
            flag_work = WorkEvidence.objects.filter(query).exists()

            if flag_leave or flag_work:
                msg = f'For worker {worker} this date ({leave_date}) is existing in database...'
                messages.error(request, msg)
                context.__setitem__('flag_leave', flag_leave)
                context.__setitem__('flag_work', flag_work)

            elif flag_weekend:
                msg = f'Selectet date {leave_date} is Saturday or Sunday. You can not set this as leave day'
                messages.error(request, msg)
                context.__setitem__('flag_weekend', flag_weekend)

            elif leave_date in holiday(leave_date.year).values():
                msg = f'Selectet date {leave_date} is holiday ({name_holiday}). You can not set this as leave day'
                messages.error(request, msg)
                context.__setitem__('name_holiday', name_holiday)

            else:
                EmployeeLeave.objects.create(**data)
                msg = f'Succesful register new leave time for {worker}'
                messages.success(request, msg)
                leave_set = {year:EmployeeLeave.objects.filter(worker=worker, leave_date__year=year).count() for year in [year for year in range(EmployeeLeave.objects.filter(worker=worker).earliest('leave_date').leave_date.year, date.today().year + 1)]}
                context.__setitem__('leave_flag', leave_flag)
                context.__setitem__('leave_set', leave_set)

            values = {'worker':worker, 'leave_date__year': date.today().year}
            total_leaves = EmployeeLeave.objects.filter(**values).order_by('leave_date')
            remaining_leave = 26 - total_leaves.filter(leave_flag='paid_leave').count()

            context.__setitem__('remaining_leave', remaining_leave)
            context.__setitem__('total_leaves', total_leaves.count())
            context.__setitem__('leaves_pl', total_leaves.filter(leave_flag='paid_leave'))
            context.__setitem__('leaves_upl', total_leaves.filter(leave_flag='unpaid_leave'))
            context.__setitem__('leaves_ml', total_leaves.filter(leave_flag='maternity_leave'))

        return render(request, 'evidence/leave_time_recorder.html', context)


class LeaveTimeRecorderEraseView(View):
    '''class implementing the method of erase last added leave time record for specific employee'''
    def get(self, request, employee_id:int, leave_date:date)->HttpResponseRedirect:
        worker = Employee.objects.get(id=employee_id)
        check = EmployeeLeave.objects.filter(worker=worker, leave_date=leave_date)
        if check.exists():
            check.delete()
            messages.success(request, f'Succesful erase last record for {worker}')
        else:
            messages.info(request, r'Nothing to erase...')

        kwargs = {'employee_id': employee_id}

        return HttpResponseRedirect(reverse('evidence:leave_time_recorder_add', kwargs=kwargs))


class LeavesDataPrintView(View):
    '''class representing the view of monthly payroll print'''
    def post(self, request, employee_id:int)->HttpResponseRedirect:
        # convert html file (evidence/leaves_data.html) to pdf file
        year = int(request.POST['leave_year'])
        leavehtml2pdf(employee_id, year)
        file = Path(f'C:/Users/kopia/Desktop/UniApps/uniwork/templates/pdf/leaves_data_{employee_id}.pdf')
        try:
            os.popen(f'explorer.exe "file:///{file}"')
            messages.info(request, r'File leaves_data.pdf file was sending to browser....')
        except WindowsError as err:
            print(err)

        kwargs = {'employee_id': employee_id}

        return HttpResponseRedirect(reverse('evidence:leave_time_recorder_add', kwargs=kwargs))


class LeavesDataPdf(View):
    '''class representing the view for sending leaves date as pdf file'''
    def get(self, request, employee_id:int)->HttpResponseRedirect:
        # convert html file (evidence/leave_data_{}.html.format(employee_id) to pdf file
        leavehtml2pdf(employee_id, date.today().year)
        # send e-mail with attached payroll in pdf format
        sendLeavesData(employee_id)
        messages.info(request, r'The pdf file was sending....')

        kwargs = {'employee_id': employee_id}

        return HttpResponseRedirect(reverse('evidence:leave_time_recorder_add', kwargs=kwargs))


class MonthlyPayrollView(View):
    '''class representing the view of monthly payroll'''
    def get(self, request)->render:
        now = date.today()
        month, year = now.month, now.year
        heads = ['Employee', 'Total Pay', 'Basic Pay', 'Leave Pay', 'Overhours', 'Saturday Pay', 'Sunday Pay', 'Account Pay', 'Value remaining']
        form = PeriodMonthlyPayrollForm(initial={'choice_date': now})
        employees = Employee.objects.all()
        employee_id = employees.filter(employeedata__end_contract__isnull=True, status=True).first()
        employee_id = employee_id.id
        total_work_hours = len(list(workingdays(year, month))) * 8
        employees = employees.exclude(employeedata__end_contract__lt=date(year, month, 1)).order_by('surname')

        # create data for payroll as associative arrays for every engaged employee
        payroll = {employee: total_payment(employee.id, year, month) for employee in employees}

        # create defaultdict with summary payment
        amountpay = defaultdict(float)
        for item in payroll.values():
            if item['accountpay'] != item['brutto']:
                for k,v in item.items():
                    amountpay[k] += v

        context = {'form': form, 'heads': heads, 'payroll': payroll, 'month': month, 'year': year,
                   'total_work_hours': total_work_hours, 'amountpay': dict(amountpay), 'employee_id': employee_id}

        return render(request, 'evidence/monthly_payroll.html', context)

    def post(self, request)->render:
        heads = ['Employee', 'Total Pay', 'Basic Pay', 'Leave Pay', 'Overhours', 'Saturday Pay', 'Sunday Pay', 'Account Pay', 'Value remaining']
        employees = Employee.objects.all()
        employee_id = employees.filter(employeedata__end_contract__isnull=True, status=True).first()
        employee_id = employee_id.id
        choice_date = datetime.strptime(request.POST['choice_date'],'%m/%Y')
        form = PeriodMonthlyPayrollForm(data={'choice_date':choice_date})

        # building complex query for actual list of employee
        month, year = choice_date.month, choice_date.year
        qfirst = (year, month, 1)
        if month == 12:
            qsecond = (year + 1, 1, 1)
        else:
            qsecond = (year, month + 1, 1)
        complex_query = Q(employeedata__end_contract__lt=date(*qfirst))|Q(employeedata__start_contract__gte=date(*qsecond))
        employees = employees.exclude(complex_query).order_by('surname')
        context = {'form': form, 'heads': heads, 'employee_id': employee_id,}

        if form.is_valid():
            total_work_hours = len(list(workingdays(year, month))) * 8
            # create data for payroll as associative arrays for every engaged employee
            payroll = {employee: total_payment(employee.id, year, month) for employee in employees}
            # create defaultdict with summary payment
            amountpay = defaultdict(float)
            for item in payroll.values():
                for k,v in item.items():
                    amountpay[k] += v

            context.__setitem__('payroll', payroll)
            context.__setitem__('month', month)
            context.__setitem__('year', year)
            context.__setitem__('total_work_hours', total_work_hours)
            context.__setitem__('amountpay', dict(amountpay))

        return render(request, 'evidence/monthly_payroll.html', context)


class MonthlyPayrollPrintView(View):
    '''class representing the view of monthly payroll print'''
    def get(self, request, month:int, year:int)->HttpResponseRedirect:
        # convert html file (evidence/monthly_payroll_pdf.html) to .pdf file
        if payrollhtml2pdf(month, year):
            file = Path(f'C:/Users/kopia/Desktop/UniApps/uniwork/templates/pdf/payroll_{month}_{year}.pdf')
            try:
                os.popen(f'explorer.exe "file:///{file}"')
                messages.info(request, f'File payroll_{month}_{year}.pdf file was sending to browser....')
            except FileNotFoundError as error:
                messages.warning(request, f'File {file} does not exist...\nError: {error}')
        else:
            messages.warning(request, r'Nothing to print...')

        return HttpResponseRedirect(reverse('evidence:monthly_payroll_view'))


class SendPayrollPdf(View):
    '''class representing the view for sending monthly payroll as pdf file'''
    def get(self, request, month:int, year:int)->HttpResponseRedirect:
        # convert html file (evidence/monthly_payroll_pdf.html) to pdf file
        if payrollhtml2pdf(month, year):
            # send e-mail with attached payroll in pdf format
            sendPayroll(month, year)
            messages.info(request, r'The pdf file was sending....')
        else:
            messages.warning(request, r'Nothing to send...')

        return HttpResponseRedirect(reverse('evidence:monthly_payroll_view'))


class AccountPaymentView(View):
    '''class representing the view of payment on account'''
    def get(self, request, employee_id:int)->render:
        month, year = date.today().month, date.today().year
        form = AccountPaymentForm(initial=initial_accountdate_form())
        worker = Employee.objects.get(id=employee_id)
        employees = Employee.objects.filter(employeedata__end_contract__isnull=True).order_by('surname')
        salary = total_payment(employee_id, year, month)
        salary = salary['brutto']
        context = {'form': form, 'worker': worker, 'employee_id': employee_id, 'employees': employees, 'salary': salary}
        query = Q(worker=worker) & Q(account_date__year=date.today().year) & Q(account_date__month=date.today().month)
        total_account = AccountPayment.objects.filter(query)

        if total_account.exists():
            total_account = total_account.aggregate(ta=Sum('account_value'))
            total_account = total_account['ta']
            context.__setitem__('total_account', total_account)
        else:
            total_account = 0
            context.__setitem__('total_account', total_account)

        return render(request, 'evidence/account_payment.html', context)

    def post(self, request, employee_id:int)->render:
        form = AccountPaymentForm(data=request.POST)
        worker = Employee.objects.get(id=employee_id)
        employees = Employee.objects.filter(employeedata__end_contract__isnull=True).order_by('surname')

        context = {'form': form, 'worker': worker, 'employee_id': employee_id, 'employees': employees}

        if form.is_valid():
            data = form.cleaned_data
            data.__setitem__('worker', worker)
            account_date, account_value = data['account_date'], float(data['account_value'])
            context.__setitem__('account_date', account_date)
            context.__setitem__('account_value', account_value)

            # check if the total of advances is not greater than the income earned
            salary = total_payment(employee_id, account_date.year, account_date.month)
            salary = salary['brutto']
            context.__setitem__('salary', salary)
            query = Q(worker=worker) & Q(account_date__year=account_date.year) & Q(account_date__month=account_date.month)
            advances = AccountPayment.objects.filter(query).aggregate(ap=Sum('account_value'))
            if advances['ap'] is None:
                advances = account_value
                context.__setitem__('advances', advances)
            else:
                advances = advances['ap'] + account_value
                context.__setitem__('advances', advances)

            if salary >= advances:
                AccountPayment.objects.create(**data)
                messages.success(request, f'Employee {worker} has become an account {account_value:,.2f} PLN on {account_date}')
            else:
                msg = f'The sum of advances ({advances:,.2f} PLN) is greater than the income earned so far ({salary:,.2f} PLN). The advance can not be paid...'
                messages.error(request, msg)

            return render(request, 'evidence/account_payment.html', context)


class AccountPaymentEraseView(View):
    '''class implementing the method of erase last added working time record for specific employee'''
    def get(self, request, employee_id:int, account_date:str, account_value:float)->HttpResponseRedirect:
        worker = Employee.objects.get(id=employee_id)
        account_value = float(account_value)
        check = AccountPayment.objects.filter(worker=worker, account_date=account_date, account_value=account_value)
        if check.exists():
            check.delete()
            msg = f'Succesful erase last record for {worker}'
            messages.success(request, msg)
        else:
            messages.info(request, r'Nothing to erase...')

        kwargs = {'employee_id': employee_id}

        return HttpResponseRedirect(reverse('evidence:account_payment', kwargs=kwargs))


class EmployeeCurrentComplexDataView(View):
    '''class representing employee complex data view'''
    def get(self, request, employee_id:int)->render:
        choice_date = date.today()
        month, year = choice_date.month, choice_date.year
        form = PeriodCurrentComplexDataForm(initial={'choice_date': choice_date})
        worker = Employee.objects.get(id=employee_id)
        employees = Employee.objects.filter(employeedata__end_contract__isnull=True, status=True).order_by('surname')
        holidays = holiday(year)
        leave_kind = ('unpaid_leave', 'paid_leave', 'maternity_leave')
        month_leaves = EmployeeLeave.objects.filter(worker=worker, leave_date__year=year, leave_date__month=month)
        year_leaves = EmployeeLeave.objects.filter(worker=worker, leave_date__year=year)
        month_leaves = {kind:month_leaves.filter(leave_flag=kind).count() for kind in leave_kind}
        year_leaves = {kind:year_leaves.filter(leave_flag=kind).count() for kind in leave_kind}

        context = {'form': form, 'worker': worker, 'employee_id': employee_id, 'choice_date': choice_date,
                   'employees': employees, 'month_leaves': month_leaves, 'year_leaves': year_leaves, 'holidays': holidays}

        employee_total_data(month, year, employee_id, context)

        return render(request, r'evidence/current_complex_evidence_data.html', context)

    def post(self, request, employee_id:int)->render:
        choice_date = datetime.strptime(request.POST['choice_date'],'%m/%Y')
        form = PeriodCurrentComplexDataForm(data={'choice_date':choice_date})
        worker = Employee.objects.get(id=employee_id)
        employees = Employee.objects.filter(employeedata__end_contract__isnull=True, status=True).order_by('surname')

        if form.is_valid():
            data = form.cleaned_data
            choice_date = data['choice_date']
            month, year = choice_date.month, choice_date.year
            leave_kind = ('unpaid_leave', 'paid_leave', 'maternity_leave')
            holidays = holiday(year)
            month_leaves = EmployeeLeave.objects.filter(worker=worker, leave_date__year=year, leave_date__month=month)
            year_leaves = EmployeeLeave.objects.filter(worker=worker, leave_date__year=year)
            month_leaves = {kind:month_leaves.filter(leave_flag=kind).count() for kind in leave_kind}
            year_leaves = {kind:year_leaves.filter(leave_flag=kind).count() for kind in leave_kind}

            context = {'form': form, 'worker': worker, 'employee_id': employee_id, 'choice_date': choice_date,
                       'employees': employees, 'month_leaves': month_leaves, 'year_leaves': year_leaves, 'holidays': holidays}

            employee_total_data(month, year, employee_id, context)

        else:
            context = {'form': form, 'worker': worker, 'employee_id': employee_id, 'employees': employees}

        return render(request, r'evidence/current_complex_evidence_data.html', context)
