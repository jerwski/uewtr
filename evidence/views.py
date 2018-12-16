# standard library
import os
import pathlib
from collections import defaultdict
from datetime import date, datetime

# django core
from django.urls import reverse
from django.db.models import Sum, Q
from django.contrib import messages
from django.views.generic import View
from django.shortcuts import render, HttpResponseRedirect

# my forms
from evidence.forms import WorkEvidenceForm, EmployeeLeaveForm, ChoiceDateForm, AccountPaymentForm

# my models
from employee.models import Employee, EmployeeData
from evidence.models import WorkEvidence, EmployeeLeave, AccountPayment

# my function
from functions.payment import total_payment, workingdays, employee_total_data, payrollhtml2pdf, leavehtml2pdf
from functions.myfunctions import sendPayroll, sendLeavesData, holiday, initial_date, initial_accountdate, initial_leave_flag


# Create your views here.


class WorkingTimeRecorderView(View):
    '''class implementing the method of adding working time for specific employee'''
    def get(self, request, employee_id:int)->render:
        form = WorkEvidenceForm(initial=initial_date(employee_id))
        worker = Employee.objects.get(pk=employee_id)
        employees = Employee.objects.filter(employeedata__end_contract__isnull=True, status=True).order_by('surname')
        query = Q(name=worker) & (Q(overtime=1)|Q(overtime=2))
        overhours = EmployeeData.objects.filter(query).exists()
        context = {'form': form, 'worker': worker, 'employee_id': employee_id, 'employees': employees, 'overhours': overhours}
        work_date = date.today()
        employee_total_data(work_date, employee_id, context)

        return render(request, 'evidence/working_time_recorder.html', context)

    def post(self, request, employee_id:int)->render:
        form = WorkEvidenceForm(data=request.POST)
        worker = Employee.objects.get(id=employee_id)
        employees = Employee.objects.filter(employeedata__end_contract__isnull=True, status=True).order_by('surname')
        query = Q(name=worker) & (Q(overtime=1)|Q(overtime=2))
        overhours = EmployeeData.objects.filter(query).exists()
        context = {'form': form, 'worker': worker, 'employee_id': employee_id, 'employees': employees, 'overhours': overhours}

        if form.is_valid():
            data = form.cleaned_data
            data.__setitem__('worker', worker)
            jobhours = (data['end_work'] - data['start_work']).total_seconds()/3600
            data.__setitem__('jobhours', jobhours)
            context.__setitem__('start_work', data['start_work'])
            context.__setitem__('end_work', data['end_work'])
            context.__setitem__('jobhours', jobhours)
            work_date = data['start_work']

            # check or data exisiting in WorkEvidence and EmployeeLeave table
            check_leave = {'worker': worker, 'leave_date': data['start_work'].date(),}
            flag_leave = EmployeeLeave.objects.filter(**check_leave).exists()
            query = Q(worker=worker) & Q(start_work__year=data['start_work'].year) & Q(start_work__month=data['start_work'].month) & Q(start_work__day=data['start_work'].day) & Q(end_work__day=data['end_work'].day)
            flag_work = WorkEvidence.objects.filter(query).exists()

            if data['start_work'] < data['end_work']:

                if flag_work or flag_leave:
                    msg = r'For worker {} this date ({}) is existing in database...'
                    messages.error(request, msg.format(data['worker'], data['start_work'].date()))
                    context.__setitem__('flag_work', flag_work)
                    context.__setitem__('flag_leave', flag_leave)

                else:
                    WorkEvidence.objects.create(**data)
                    msg = r'Succesful register new time working for {}'
                    messages.success(request, msg.format(data['worker']))
                    employee_total_data(work_date, employee_id, context)
            else:
                msg = r'Start working ({}) is later than end working ({}). Please correct it...'
                messages.error(request, msg.format(data['start_work'], data['end_work']))

            employee_total_data(work_date, employee_id, context)

        return render(request, 'evidence/working_time_recorder.html', context)


class WorkingTimeRecorderEraseView(View):
    '''class implementing the method of erase last added working time record for specific employee'''
    def get(self, request, employee_id:int, start_work:str, end_work:str)->HttpResponseRedirect:
        worker = Employee.objects.get(id=employee_id)
        start_work = datetime.strptime(start_work, "%Y-%m-%d %H:%M:%S")
        end_work = datetime.strptime(end_work, "%Y-%m-%d %H:%M:%S")
        check = WorkEvidence.objects.filter(worker=worker, start_work=start_work, end_work=end_work)
        if check.exists():
            check.delete()
            msg = r'Succesful erase last record for {}'
            messages.success(request, msg.format(worker))

        kwargs = {'employee_id': employee_id}

        return HttpResponseRedirect(reverse('evidence:working_time_recorder_add', kwargs=kwargs))


class LeaveTimeRecorderView(View):
    '''class implementing the method of adding leave time for specific employee'''
    def get(self, request, employee_id:int)->render:
        form = EmployeeLeaveForm(initial=initial_leave_flag(employee_id))
        worker = Employee.objects.get(id=employee_id)
        employees = Employee.objects.filter(employeedata__end_contract__isnull=True, status=True).order_by('surname')
        values = {'worker':worker, 'leave_date__year': date.today().year}
        total_leaves = EmployeeLeave.objects.filter(**values).order_by('leave_date')
        remaining_leave = 26 - total_leaves.filter(leave_flag='paid_leave').count()
        context = {'form': form, 'worker': worker, 'employee_id': employee_id, 'employees': employees,
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
                msg = r'For worker {} this date ({}) is existing in database...'
                messages.error(request, msg.format(worker, leave_date))
                context.__setitem__('flag_leave', flag_leave)
                context.__setitem__('flag_work', flag_work)

            elif flag_weekend:
                msg = r'Selectet date {} is Saturday or Sunday. You can not set this as leave day'
                messages.error(request, msg.format(leave_date))
                context.__setitem__('flag_weekend', flag_weekend)

            elif leave_date in holiday(leave_date.year).values():
                msg = r'Selectet date {} is holiday ({}). You can not set this as leave day'
                messages.error(request, msg.format(leave_date, name_holiday))
                context.__setitem__('name_holiday', name_holiday)

            else:
                EmployeeLeave.objects.create(**data)
                msg = r'Succesful register new leave time for {}'
                messages.success(request, msg.format(worker))
                context.__setitem__('leave_flag', leave_flag)

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
    def get(self, request, employee_id:int, leave_date:str)->HttpResponseRedirect:
        worker = Employee.objects.get(id=employee_id)
        leave_date = datetime.strptime(leave_date, "%Y-%m-%d")
        check = EmployeeLeave.objects.filter(worker=worker, leave_date=leave_date)
        if check.exists():
            check.delete()
            msg = r'Succesful erase last record for {}'
            messages.success(request, msg.format(worker))
        else:
            messages.info(request, r'Nothing to erase...')

        kwargs = {'employee_id': employee_id}

        return HttpResponseRedirect(reverse('evidence:leave_time_recorder_add', kwargs=kwargs))


class LeavesDataPrintView(View):
    '''class representing the view of monthly payroll print'''
    def get(self, request, employee_id:int)->HttpResponseRedirect:
        # convert html file (evidence/leaves_data.html) to pdf file
        leavehtml2pdf(employee_id)
        file = pathlib.Path(r'C:/Users/kopia/Desktop/UniApps/uniwork/templates/pdf/leaves_data_{}.pdf'.format(employee_id))
        try:
            os.popen('explorer.exe "file:///{}"'.format(file))
            messages.info(request, r'File leaves_data.pdf file was sending to browser....')
        except WindowsError as err:
            print(err)

        kwargs = {'employee_id': employee_id}

        return HttpResponseRedirect(reverse('evidence:leave_time_recorder_add', kwargs=kwargs))


class LeavesDataPdf(View):
    '''class representing the view for sending leaves date as pdf file'''
    def get(self, request, employee_id:int)->HttpResponseRedirect:
        # convert html file (evidence/leave_data_{}.html.format(employee_id) to pdf file
        leavehtml2pdf(employee_id)
        # send e-mail with attached payroll in pdf format
        sendLeavesData(employee_id)
        messages.info(request, r'The pdf file was sending....')

        kwargs = {'employee_id': employee_id}

        return HttpResponseRedirect(reverse('evidence:leave_time_recorder_add', kwargs=kwargs))


class MonthlyPayrollView(View):
    '''class representing the view of monthly payroll'''
    def get(self, request)->render:
        payroll = {}
        heads = ['Employee', 'Total Pay', 'Basic Pay', 'Leave Pay', 'Overhours', 'Saturday Pay', 'Sunday Pay', 'Account Pay', 'Value remaining']
        form = ChoiceDateForm()
        employee_id = Employee.objects.filter(employeedata__end_contract__isnull=True).first()
        employee_id = employee_id.id
        total_work_hours = len(list(workingdays(date.today().year, date.today().month))) * 8
        query = Q(end_contract__year=date.today().year) & Q(end_contract__month__lt=date.today().month)
        employees = EmployeeData.objects.exclude(query).order_by('name')

        # create data for payroll as associative arrays for every engaged employee
        for employee in employees:
            payroll.__setitem__(employee.name, total_payment(employee.id, date.today().year, date.today().month))
        # create defaultdict with summary payment
        amountpay = defaultdict(float)
        for item in payroll.values():
            if item['accountpay'] != item['brutto']:
                for k,v in item.items():
                    amountpay[k] += v

        context = {'form': form, 'heads': heads, 'payroll': payroll, 'choice_date': date.today(),
                   'total_work_hours': total_work_hours, 'amountpay': dict(amountpay), 'employee_id': employee_id}

        return render(request, 'evidence/monthly_payroll.html', context)

    def post(self, request)->render:
        payroll = {}
        heads = ['Employee', 'Total Pay', 'Basic Pay', 'Leave Pay', 'Overhours', 'Saturday Pay', 'Sunday Pay', 'Account Pay', 'Value remaining']
        form = ChoiceDateForm(data=request.POST)
        employee_id = Employee.objects.filter(status=True).first()
        employee_id = employee_id.id
        context = {'form': form, 'heads': heads, 'employee_id': employee_id,}

        if form.is_valid():
            data = form.cleaned_data
            choice_date = data['choice_date']
            query = Q(end_contract__isnull=True) &\
                    Q(start_contract__month__lte=choice_date.month) &\
                    Q(start_contract__year__lte=choice_date.year) |\
                    Q(end_contract__month__gte=choice_date.month) &\
                    Q(end_contract__year__gte=choice_date.year)
            employees = EmployeeData.objects.filter(query).order_by('name')
            total_work_hours = len(list(workingdays(choice_date.year, choice_date.month))) * 8

            # create data for payroll as associative arrays for every engaged employee
            for employee in employees:
                payroll.__setitem__(employee.name, total_payment(employee.id, choice_date.year, choice_date.month))
            # create defaultdict with summary payment
            amountpay = defaultdict(float)
            for item in payroll.values():
                for k,v in item.items():
                    amountpay[k] += v

            context.__setitem__('payroll', payroll)
            context.__setitem__('choice_date', choice_date)
            context.__setitem__('total_work_hours', total_work_hours)
            context.__setitem__('amountpay', dict(amountpay))

        return render(request, 'evidence/monthly_payroll.html', context)


class MonthlyPayrollPrintView(View):
    '''class representing the view of monthly payroll print'''
    def get(self, request, choice_date:str)->HttpResponseRedirect:
        choice_date = datetime.strptime(choice_date, "%Y-%m-%d")
        choice_date = choice_date.date()
        # convert html file (evidence/monthly_payroll_pdf.html) to .pdf file
        payrollhtml2pdf(choice_date)
        frm = (choice_date.month, choice_date.year)
        file = pathlib.Path(r'C:/Users/kopia/Desktop/UniApps/uniwork/templates/pdf/payroll_{}_{}.pdf'.format(*frm))
        try:
            os.popen('explorer.exe "file:///{}"'.format(file))
            messages.info(request, r'File payroll_{}_{}.pdf file was sending to browser....'.format(*frm))
        except WindowsError as err:
            print(err)

        return HttpResponseRedirect(reverse('evidence:monthly_payroll_view'))


class PayrollPdf(View):
    '''class representing the view for sending monthly payroll as pdf file'''
    def get(self, request, choice_date:str)->HttpResponseRedirect:
        choice_date = datetime.strptime(choice_date, "%Y-%m-%d")
        choice_date = choice_date.date()
        # convert html file (evidence/monthly_payroll_pdf.html) to pdf file
        payrollhtml2pdf(choice_date)
        # send e-mail with attached payroll in pdf format
        sendPayroll(choice_date)
        messages.info(request, r'The pdf file was sending....')

        return HttpResponseRedirect(reverse('evidence:monthly_payroll_view'))


class AccountPaymentView(View):
    '''class representing the view of payment on account'''
    def get(self, request, employee_id:int)->render:
        form = AccountPaymentForm(initial=initial_accountdate())
        worker = Employee.objects.get(id=employee_id)
        employees = Employee.objects.filter(employeedata__end_contract__isnull=True).order_by('surname')
        salary = total_payment(employee_id, date.today().year, date.today().month)
        salary = salary['salary'] + salary['accountpay']
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
        form = AccountPaymentForm(request.POST)
        worker = Employee.objects.get(id=employee_id)
        employees = Employee.objects.filter(employeedata__end_contract__isnull=True).order_by('surname')

        context = {'form': form, 'worker': worker, 'employee_id': employee_id, 'employees': employees}

        if form.is_valid():
            data = form.cleaned_data
            data.__setitem__('worker', worker)
            context.__setitem__('account_date', data['account_date'])
            context.__setitem__('account_value', data['account_value'])

            # check if the total of advances is not greater than the income earned
            salary = total_payment(employee_id, data['account_date'].year, data['account_date'].month)
            salary = salary['salary'] + salary['accountpay']
            context.__setitem__('salary', salary)
            query = Q(worker=worker) & Q(account_date__year=data['account_date'].year) & Q(account_date__month=data['account_date'].month)
            advances = AccountPayment.objects.filter(query).aggregate(ap=Sum('account_value'))
            if advances['ap'] is None:
                advances = data['account_value']
                context.__setitem__('advances', advances)
            else:
                advances = advances['ap'] + float(data['account_value'])
                context.__setitem__('advances', advances)

            if salary >= advances:
                AccountPayment.objects.create(**data)
                msg = r'Employee {} has become an account {:,.2f} PLN on {}'
                messages.success(request, msg.format(worker, data['account_value'], data['account_date']))
            else:
                msg = r'The sum of advances ({:,.2f} PLN) is greater than the income earned so far ({:,.2f} PLN). The advance can not be paid...'
                messages.error(request, msg.format(advances, salary))

            return render(request, 'evidence/account_payment.html', context)


class AccountPaymentEraseView(View):
    '''class implementing the method of erase last added working time record for specific employee'''
    def get(self, request, employee_id:int, account_date:str, account_value:float)->HttpResponseRedirect:
        worker = Employee.objects.get(id=employee_id)
        account_date = datetime.strptime(account_date, "%Y-%m-%d")
        account_value = float(account_value)
        check = AccountPayment.objects.filter(worker=worker, account_date=account_date, account_value=account_value)
        if check.exists():
            check.delete()
            msg = r'Succesful erase last record for {}'
            messages.success(request, msg.format(worker))
        else:
            messages.info(request, r'Nothing to erase...')

        kwargs = {'employee_id': employee_id}

        return HttpResponseRedirect(reverse('evidence:account_payment', kwargs=kwargs))


class EmployeeCurrentComplexDataView(View):
    '''class representing employee complex data view'''
    def get(self, request, employee_id:int)->render:
        form = ChoiceDateForm()
        worker = Employee.objects.get(id=employee_id)
        employees = Employee.objects.filter(employeedata__end_contract__isnull=True).order_by('surname')
        active_worker = employees.first()
        active_worker = active_worker.id
        choice_date = date.today()
        holidays = holiday(choice_date.year)
        leave_kind = ('unpaid_leave', 'paid_leave', 'maternity_leave')
        month_leaves = EmployeeLeave.objects.filter(worker=worker, leave_date__year=choice_date.year, leave_date__month=choice_date.month)
        year_leaves = EmployeeLeave.objects.filter(worker=worker, leave_date__year=choice_date.year)
        month_leaves = {kind:month_leaves.filter(leave_flag=kind).count() for kind in leave_kind}
        year_leaves = {kind:year_leaves.filter(leave_flag=kind).count() for kind in leave_kind}

        context = {'form': form, 'worker': worker, 'active_worker': active_worker,
                   'employee_id': employee_id, 'employees': employees, 'choice_date': choice_date,
                   'month_leaves': month_leaves, 'year_leaves': year_leaves, 'holidays': holidays}

        employee_total_data(date.today(), employee_id, context)

        return render(request, r'evidence/current_complex_evidence_data.html', context)

    def post(self, request, employee_id:int)->render:
        form = ChoiceDateForm(data=request.POST)
        worker = Employee.objects.get(id=employee_id)
        employees = Employee.objects.filter(employeedata__end_contract__isnull=True).order_by('surname')
        active_worker = employees.first()
        active_worker = active_worker.id

        if form.is_valid():
            data = form.cleaned_data
            choice_date = data['choice_date']
            leave_kind = ('unpaid_leave', 'paid_leave', 'maternity_leave')
            holidays = holiday(choice_date.year)
            month_leaves = EmployeeLeave.objects.filter(worker=worker, leave_date__year=choice_date.year, leave_date__month=choice_date.month)
            year_leaves = EmployeeLeave.objects.filter(worker=worker, leave_date__year=choice_date.year)
            month_leaves = {kind:month_leaves.filter(leave_flag=kind).count() for kind in leave_kind}
            year_leaves = {kind:year_leaves.filter(leave_flag=kind).count() for kind in leave_kind}

            context = {'form': form, 'worker': worker, 'active_worker': active_worker,
                       'employee_id': employee_id, 'employees': employees, 'choice_date': choice_date,
                       'month_leaves': month_leaves, 'year_leaves': year_leaves, 'holidays': holidays}

            employee_total_data(choice_date, employee_id, context)

            return render(request, r'evidence/current_complex_evidence_data.html', context)

        else:
            context = {'form': form, 'worker': worker, 'active_worker': active_worker, 'employee_id': employee_id}
            return render(request, r'evidence/current_complex_evidence_data.html', context)
