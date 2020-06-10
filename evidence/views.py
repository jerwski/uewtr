# standard library
import calendar
from collections import defaultdict
from datetime import date, datetime

# pdfkit library
import pdfkit

# django core
from django.urls import reverse
from django.conf import settings
from django.contrib import messages
from django.db.models import Sum, Q
from django.views.generic import View
from django.utils.timezone import now
from django.shortcuts import render, HttpResponse, HttpResponseRedirect

# my forms
from evidence.forms import WorkEvidenceForm, EmployeeLeaveForm, AccountPaymentForm, PeriodCurrentComplexDataForm, PeriodMonthlyPayrollForm

# my models
from employee.models import Employee, EmployeeData
from evidence.models import WorkEvidence, EmployeeLeave, AccountPayment

# my function
from functions.archive import check_FTPconn
from functions.payment import holiday, total_payment, workingdays, employee_total_data, data_modal_chart
from functions.myfunctions import payrollhtml2pdf, leavehtml2pdf, plot_chart, sendemail, initial_leave_form, initial_worktime_form, initial_account_form, previous_month_year, workhourshtml2pdf, make_attachment, accountpaymenthtml2pdf


# Create your views here.


class WorkingTimeRecorderView(View):
	'''class implementing the method of adding working time for specific employee'''
	def get(self, request, employee_id:int, work_hours:int=None) -> render:
		worker = Employee.objects.get(pk=employee_id)
		initial = {'worker': worker}
		employees = Employee.objects.filter(employeedata__end_contract__isnull=True, status=True)
		employees = employees.order_by('surname', 'forename')
		query = Q(worker=worker) & (Q(overtime=1)|Q(overtime=2))
		overhours = EmployeeData.objects.filter(query).exists()
		context = {'worker': worker, 'employee_id': employee_id, 'employees': employees, 'overhours': overhours}
		employee_total_data(employee_id, now().year, now().month, context)

		if work_hours:
			initial.update(initial_worktime_form(work_hours))
			form = WorkEvidenceForm(initial=initial)
			context.__setitem__('form', form)
		else:
			form = WorkEvidenceForm(initial=initial)
			context.__setitem__('form', form)

		return render(request, 'evidence/working_time_recorder.html', context)

	def post(self, request, employee_id:int) -> render:
		form = WorkEvidenceForm(data=request.POST)
		employees = Employee.objects.filter(employeedata__end_contract__isnull=True, status=True)
		employees = employees.order_by('surname', 'forename')

		context = {'form': form, 'employee_id': employee_id, 'employees': employees}

		if form.is_valid():
			data = form.cleaned_data
			worker, start_work, end_work = data['worker'], data['start_work'], data['end_work']
			query = Q(worker=worker) & (Q(overtime=1)|Q(overtime=2))
			overhours = EmployeeData.objects.filter(query).exists()
			context.update({'worker': worker, 'overhours': overhours})
			jobhours = (end_work - start_work).total_seconds()/3600
			data.__setitem__('jobhours', jobhours)
			context.update({'start_work': start_work, 'end_work': end_work, 'jobhours': jobhours})
			year, month = start_work.year, start_work.month

			# check or data exisiting in WorkEvidence and EmployeeLeave table
			check_leave = {'worker': worker, 'leave_date': start_work.date(),}
			flag_leave = EmployeeLeave.objects.filter(**check_leave).exists()
			mainquery = Q(worker=worker) & Q(start_work__year=year) & Q(start_work__month=month)
			workquery = Q(start_work__day=start_work.day) & Q(end_work__day=end_work.day)
			flag_work = WorkEvidence.objects.filter(mainquery&workquery).exists()

			if start_work < end_work:

				if flag_work or flag_leave:
					messages.error(request, f'For worker {worker} this date ({start_work.date()}) is existing in database...')
					context.__setitem__('flag_work', flag_work)
					context.__setitem__('flag_leave', flag_leave)
				else:
					WorkEvidence.objects.create(**data)
					messages.success(request, f'Succesful register new time working for {worker}')
					employee_total_data(employee_id, year, month, context)

			elif start_work == end_work:
				msg = f'Start working ({start_work}) is the same like end working ({end_work}). Please correct it...'
				messages.error(request, msg)

			else:
				msg = f'Start working ({start_work}) is later than end working ({end_work}). Please correct it...'
				messages.error(request, msg)

			employee_total_data(employee_id, year, month, context)

		return render(request, 'evidence/working_time_recorder.html', context)


class WorkingTimeRecorderEraseView(View):
	'''class implementing the method of erase last added working time record for specific employee'''
	def get(self, request, employee_id:int, start_work:str, end_work:str) -> HttpResponseRedirect:
		check = WorkEvidence.objects.filter(worker_id=employee_id, start_work=start_work, end_work=end_work)

		if check.exists():
			check.delete()
			msg = f'Succesful erase working day: start_work: {start_work} - end_work: {end_work}'
			messages.success(request, msg)

		return HttpResponseRedirect(reverse('evidence:working_time_recorder_add', args=[employee_id]))


class LeaveTimeRecorderView(View):
	'''class implementing the method of adding leave time for specific employee'''
	def get(self, request, employee_id:int) -> render:
		initial=initial_leave_form(employee_id)
		form = EmployeeLeaveForm(initial=initial)
		employees = Employee.objects.filter(employeedata__end_contract__isnull=True, status=True)
		employees = employees.order_by('surname', 'forename')
		worker = initial['worker']
		values = {'worker': worker, 'leave_date__year': now().year}
		total_leaves = EmployeeLeave.objects.filter(**values).order_by('leave_date')
		remaining_leave = 26 - total_leaves.filter(leave_flag='paid_leave').count()

		if EmployeeLeave.objects.filter(worker=worker).exists():
			leave_set = {year:EmployeeLeave.objects.filter(worker=worker, leave_date__year=year).count() for year in [item.year for item in EmployeeLeave.objects.filter(worker=worker).dates('leave_date', 'year', order='DESC')]}
		else:
			leave_set = None
		context = {'form': form, 'worker': worker, 'employee_id': employee_id,
				   'employees': employees, 'year': now().year, 'leave_set': leave_set,
				   'total_leaves': total_leaves.count(), 'remaining_leave': remaining_leave}
		context.__setitem__('leaves_pl', total_leaves.filter(leave_flag='paid_leave'))
		context.__setitem__('leaves_upl', total_leaves.filter(leave_flag='unpaid_leave'))
		context.__setitem__('leaves_ml', total_leaves.filter(leave_flag='maternity_leave'))

		return render(request, 'evidence/leave_time_recorder.html', context)

	def post(self, request, employee_id:int) -> render:
		name_holiday, flag_weekend = False, False
		form = EmployeeLeaveForm(data=request.POST)
		employees = Employee.objects.filter(employeedata__end_contract__isnull=True, status=True)
		employees = employees.order_by('surname', 'forename')
		context = {'form': form, 'employees': employees, 'employee_id': employee_id}

		if form.is_valid():
			form.save(commit=False)
			data = form.cleaned_data
			worker, leave_date, leave_flag = data['worker'], data['leave_date'], data['leave_flag']
			context.update({'worker': worker, 'leave_date': leave_date})

			# check or data exisiting in WorkEvidence and EmployeeLeave table or isn't Sunday or Saturday
			check_leave = {'worker': worker, 'leave_date': leave_date}
			flag_leave = EmployeeLeave.objects.filter(**check_leave).exists()

			if leave_date.isoweekday() == 7 or leave_date.isoweekday() == 6:
				flag_weekend = True

			for name, date_holiday in holiday(leave_date.year).items():
				if date_holiday == leave_date:
					name_holiday = name

			query = Q(worker=worker) & Q(start_work__date=leave_date)
			flag_work = WorkEvidence.objects.filter(query).exists()

			if flag_leave:
				msg = f'For worker {worker} this date ({leave_date}) is existing in database as leave day!'
				messages.error(request, msg)
				context.__setitem__('flag_leave', flag_leave)

			elif flag_work:
				msg = f'For worker {worker} this date ({leave_date}) is existing in database as working day!'
				messages.error(request, msg)
				context.__setitem__('flag_work', flag_work)

			elif flag_weekend:
				msg = f'Selectet date {leave_date} is Saturday or Sunday. You can\'t set this as leave day!'
				messages.error(request, msg)
				context.__setitem__('flag_weekend', flag_weekend)

			elif name_holiday:
				msg = f'Selectet date {leave_date} is holiday ({name_holiday}). You can\'t set this as leave day!'
				messages.error(request, msg)
				context.__setitem__('name_holiday', name_holiday)

			else:
				form.save()
				msg = f'Succesful register new leave day ({leave_date}) for {worker}'
				messages.success(request, msg)
				leave_set = {year:EmployeeLeave.objects.filter(worker=worker, leave_date__year=year).count() for year in [item.year for item in EmployeeLeave.objects.filter(worker=worker).dates('leave_date', 'year', order='DESC')]}
				context.__setitem__('leave_flag', leave_flag)
				context.__setitem__('leave_set', leave_set)

			values = {'worker':worker, 'leave_date__year': now().year}
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
	def get(self, request, employee_id:int, leave_date:date) -> HttpResponseRedirect:
		check = EmployeeLeave.objects.filter(worker_id=employee_id, leave_date=leave_date)

		if check.exists():
			check.delete()
			messages.success(request, f'Succesful erase leave date: {leave_date}')
		else:
			messages.info(request, r'Nothing to erase...')

		return HttpResponseRedirect(reverse('evidence:leave_time_recorder_add', args=[employee_id]))


class LeavesDataPrintView(View):
	'''class representing the view of annual leaves days print'''

	def setup(self, request, **kwargs):
		super().setup(request, **kwargs)
		self.request, self.kwargs = request, kwargs
		self.employee_id = self.kwargs['employee_id']

		if self.request.method == 'GET':
			self.year = now().year

		elif self.request.method == 'POST':
			self.year = int(self.request.POST['leave_year'])

		self.html = leavehtml2pdf(self.employee_id, self.year)

		self.options = {'page-size': 'A4', 'margin-top': '1.0in', 'margin-right': '0.1in',
		                'margin-bottom': '0.1in', 'margin-left': '0.1in', 'encoding': "UTF-8",
		                'orientation': 'landscape','no-outline': None, 'quiet': '',}

	def get(self, request, **kwargs):
		'''convert html annuall leave time for each employee in current year to pdf'''
		if self.html:
			# create pdf file
			pdf = pdfkit.from_string(self.html, False, options=self.options, css=settings.CSS_FILE)
			filename = f'leaves_data_{self.employee_id}.pdf'

			response = HttpResponse(pdf, content_type='application/pdf')
			response['Content-Disposition'] = 'attachment; filename="' + filename + '"'
			return response
		else:
			messages.warning(self.request, r'Nothing to print...')

		return HttpResponseRedirect(reverse('evidence:leave_time_recorder_add', args=[self.employee_id]))

	def post(self, request, **kwargs):
		'''convert html annuall leave time for each employee in selected year to pdf'''
		if self.html:
			# create pdf file
			pdf = pdfkit.from_string(self.html, False, options=self.options, css=settings.CSS_FILE)
			filename = f'leaves_data_{self.employee_id}.pdf'

			response = HttpResponse(pdf, content_type='application/pdf')
			response['Content-Disposition'] = 'attachment; filename="' + filename + '"'
			return response
		else:
			messages.warning(self.request, r'Nothing to print...')

		return HttpResponseRedirect(reverse('evidence:leave_time_recorder_add', args=[self.employee_id]))


class SendLeavesDataPdf(View):
	'''class representing the view for sending leaves date as pdf file'''
	def get(self, request, employee_id:int) -> HttpResponseRedirect:
		# convert html file (evidence/leave_data_{}.html.format(employee_id) to pdf file
		html = leavehtml2pdf(employee_id, now().year)
		# create pdf file and save on templates/pdf/leves_data_{}.pdf'.format(employee_id)
		options = {'page-size': 'A4', 'margin-top': '1.0in', 'margin-right': '0.1in',
				   'margin-bottom': '0.1in', 'margin-left': '0.1in', 'encoding': "UTF-8",
				   'orientation': 'landscape','no-outline': None, 'quiet': '', }
		pdfile = f'templates/pdf/leaves_data_{employee_id}.pdf'

		if check_FTPconn():
			pdf = pdfkit.from_string(html, pdfile, options=options, css=settings.CSS_FILE)

			if pdf:
				# send e-mail with attached leaves_data in pdf format
				worker = Employee.objects.get(pk=employee_id)
				mail = {'subject': f'list of leave for {worker} ({date.today().year})r.',
						'message': f'List of leave in attachment {worker} za {date.today().year}r.',
						'sender': settings.EMAIL_HOST_USER,
						'recipient':  [settings.CC_MAIL],
						'attachments': [pdfile]}
				sendemail(**mail)
				messages.info(request, f'The file <<{pdfile}>> was sending....')
			else:
				messages.warning(request, r'Nothing to send...')
		else:
			messages.error(request, 'FTP connection failure...')

		return HttpResponseRedirect(reverse('evidence:leave_time_recorder_add', args=[employee_id]))


class MonthlyPayrollView(View):
	'''class representing the view of monthly payroll'''
	def get(self, request) -> render:
		month, year = now().month, now().year
		choice_date = datetime.strptime(f'{month}/{year}','%m/%Y')
		heads = ['Employee', 'Total Pay', 'Basic Pay', 'Leave Pay', 'Overhours',
				 'Saturday Pay', 'Sunday Pay', 'Account Pay', 'Value remaining']
		form = PeriodMonthlyPayrollForm(initial={'choice_date': choice_date})
		employees = Employee.objects.all()
		employee_id = employees.filter(employeedata__end_contract__isnull=True)
		
		if employee_id.filter(status=True).exists():
			employee_id = employee_id.filter(status=True).first().id
		else:
			employee_id = employee_id.first().id
			
		total_work_hours = len(list(workingdays(year, month))) * 8
		employees = employees.exclude(employeedata__end_contract__lt=date(year, month, 1)).order_by('surname', 'forename')

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

	def post(self,request) -> render:
		heads = ['Employee', 'Total Pay', 'Basic Pay', 'Leave Pay', 'Overhours',
				 'Saturday Pay', 'Sunday Pay', 'Account Pay', 'Value remaining']
		employees = Employee.objects.all()
		employee_id = employees.filter(employeedata__end_contract__isnull=True)
		
		if employee_id.filter(status=True).exists():
			employee_id = employee_id.filter(status=True).first().id
		else:
			employee_id = employee_id.first().id
			
		choice_date = datetime.strptime(request.POST['choice_date'],'%m/%Y')
		form = PeriodMonthlyPayrollForm(data={'choice_date':choice_date})

		# building query for actual list of employee
		year, month = choice_date.year, choice_date.month
		day = calendar.monthrange(year, month)[1]
		query = Q(employeedata__end_contract__lt=date(year,month,1))|Q(employeedata__start_contract__gt=date(year,month,day))
		employees = employees.exclude(query).order_by('surname', 'forename')
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

			context.update({'payroll': payroll, 'month': month, 'year': year,
			                'total_work_hours': total_work_hours,'amountpay': dict(amountpay)})

		return render(request, 'evidence/monthly_payroll.html', context)


class MonthlyPayrollPrintView(View):
	'''class representing the view of monthly payroll print'''
	def get(self, request, month:int, year:int):
		'''send montly payroll as pdf attachmnet on browser'''
		html = payrollhtml2pdf(month, year)

		if html:
			# create pdf file with following options
			options = {'page-size': 'A4', 'margin-top': '0.2in', 'margin-right': '0.1in',
					   'margin-bottom': '0.1in', 'margin-left': '0.1in', 'encoding': "UTF-8",
					   'orientation': 'landscape','no-outline': None, 'quiet': '', }
			pdf = pdfkit.from_string(html, False, options=options, css=settings.CSS_FILE)
			filename = f'payroll_{month}_{year}.pdf'
			# send montly pyroll as attachment
			response = HttpResponse(pdf, content_type='application/pdf')
			response['Content-Disposition'] = 'attachment; filename="' + filename + '"'

			return response
		else:
			messages.warning(request, r'Nothing to print...')

		return HttpResponseRedirect(reverse('evidence:monthly_payroll_view'))


class SendMonthlyPayrollPdf(View):
	'''class representing the view for sending monthly payroll as pdf file'''
	def get(self, request, month:int, year:int) -> HttpResponseRedirect:
		# convert html file (evidence/monthly_payroll_pdf.html) to pdf file
		if check_FTPconn():
			html = payrollhtml2pdf(month, year)
			if html:
				# create pdf file and save on templates/pdf/payroll_{}_{}.pdf.format(choice_date.month, choice_date.year)
				options = {'page-size': 'A4', 'margin-top': '0.2in', 'margin-right': '0.1in',
						   'margin-bottom': '0.1in', 'margin-left': '0.1in', 'encoding': "UTF-8",
						   'orientation': 'landscape','no-outline': None, 'quiet': '', }
				# create pdf file
				pdfile = f'templates/pdf/payroll_{month}_{year}.pdf'
				pdfkit.from_string(html, pdfile, options=options, css=settings.CSS_FILE)
				# send e-mail with attached payroll as file in pdf format
				mail = {'subject': f'payrol for {month}/{year} r.',
						'message': f'Payroll in attachment {month}-{year}...',
						'sender': settings.EMAIL_HOST_USER,
						'recipient':  [settings.CC_MAIL],
						'attachments': [pdfile]}
				sendemail(**mail)
				messages.info(request, f'The file <<{pdfile}>> was sending....')
			else:
				messages.warning(request, r'Nothing to send...')
		else:
			messages.error(request, 'FTP connection failure...')

		return HttpResponseRedirect(reverse('evidence:monthly_payroll_view'))


class AccountPaymentView(View):
	'''class representing the view of payment on account'''
	def get(self, request, employee_id:int) -> render:
		month, year = now().month, now().year
		initial = initial_account_form(employee_id)
		form = AccountPaymentForm(initial=initial)
		worker = initial['worker']
		salary = total_payment(employee_id, year, month)
		salary = salary['brutto']
		prevmonth, prevyear = initial['account_date'].month, initial['account_date'].year
		prevsalary = total_payment(employee_id, prevyear, prevmonth)
		prevsalary = prevsalary['brutto']

		# set list of valid employees
		queryset = Employee.objects.all().order_by('surname', 'forename')

		q1 = queryset.filter(status=1)
		q2 = queryset.filter(employeedata__end_contract__year__gte=prevyear, employeedata__end_contract__month__gte=prevmonth)
		employees = q1 | q2

		# seting context
		context = {'form': form, 'worker': worker, 'employee_id': employee_id, 'employees': employees, 'year': year,
		           'salary': salary, 'prevsalary': prevsalary, 'earlier_date': initial['account_date'], 'month': month}

		# check out loans, currloan = current loan, prevloan = previous loan
		current_query = Q(worker=worker) & Q(account_date__year=year) & Q(account_date__month=month)
		currloan = AccountPayment.objects.filter(current_query)
		previous_query = Q(worker=worker) & Q(account_date__year=prevyear) & Q(account_date__month=prevmonth)
		prevloan = AccountPayment.objects.filter(previous_query)

		if currloan.exists():
			currloan = currloan.aggregate(ta=Sum('account_value'))
			currloan = currloan['ta']
		else:
			currloan = 0

		if prevloan.exists():
			prevloan = prevloan.aggregate(ta_=Sum('account_value'))
			prevloan = prevloan['ta_']
		else:
			prevloan = 0

		saldo, prevsaldo = salary - currloan, prevsalary - prevloan
		context.update({'currloan': currloan, 'prevloan': prevloan, 'saldo': saldo, 'prevsaldo': prevsaldo})

		return render(request, 'evidence/account_payment.html', context)

	def post(self, request, employee_id:int) -> render:
		form = AccountPaymentForm(data=request.POST)
		month, year = now().month, now().year
		worker = Employee.objects.get(pk=employee_id)
		context = {'form': form, 'employee_id': employee_id, 'worker': worker, 'month': month, 'year': year}

		if form.is_valid():
			form.save(commit=False)
			data = form.cleaned_data
			account_date, account_value = data['account_date'], data['account_value']
			context.update({'account_date': account_date, 'account_value': account_value})

			# check if the total of advances is not greater than the income earned
			salary = total_payment(employee_id, account_date.year, account_date.month)
			salary = round(salary['brutto'], 2)

			# set list of valid employees
			queryset = Employee.objects.all()
			prevmonth, prevyear = previous_month_year(month, year)

			q1 = queryset.filter(status=1)
			q2 = queryset.filter(employeedata__end_contract__year__gte=prevyear, employeedata__end_contract__month__gte=prevmonth)
			employees = q1 | q2

			# updating context
			context.update({'salary': salary, 'employees': employees, 'earlier_date': 'account_date'})

			# check out advances
			query = Q(worker=worker) & Q(account_date__year=account_date.year) & Q(account_date__month=account_date.month)
			advances = AccountPayment.objects.filter(query).aggregate(ap=Sum('account_value'))

			if advances['ap'] is None:
				advances = account_value
			else:
				advances = advances['ap'] + account_value

			context.__setitem__('advances', advances)

			if salary >= advances:
				form.save(commit=True)
				messages.success(request, f'Employee {worker} has become an account {account_value:,.2f} PLN on {account_date}')
			else:
				msg = f'The sum of advances ({advances:,.2f} PLN) is greater than the income earned so far ({salary:,.2f} PLN). The advance can not be paid...'
				messages.error(request, msg)

		return render(request, 'evidence/account_payment.html', context)


class AccountPaymentEraseView(View):
	'''class implementing the method of erase last added working time record for specific employee'''
	def get(self, request, employee_id:int, account_date:date, account_value:float) -> HttpResponseRedirect:
		data = {'worker_id': employee_id, 'account_date': account_date, 'account_value': account_value}
		check = AccountPayment.objects.filter(**data)

		if check.exists():
			check.delete()
			msg = f'Succesful erase account payment {float(account_value):.2f} PLN'
			messages.success(request, msg)
		else:
			messages.info(request, r'Nothing to erase...')

		return HttpResponseRedirect(reverse('evidence:account_payment', args=[employee_id]))


class AccountPaymentPrintView(View):
	'''class representing the view of account payment print'''
	def get(self, request, employee_id:int, month:int, year:int):
		'''send a statement of advances as a pdf attachment to the browser'''

		html = accountpaymenthtml2pdf(employee_id, month, year)

		if html:
			# create pdf file
			filename = f'accountpayment_{employee_id}_{month}_{year}.pdf'
			response = make_attachment(html, filename)

			return response
		else:
			messages.warning(request, r'Nothing to print...')

		return HttpResponseRedirect(reverse('evidence:account_payment', args=[employee_id]))


class EmployeeCurrentComplexDataView(View):
	'''class representing employee complex data view'''

	def setup(self, request, **kwargs):
		super().setup(request, **kwargs)
		self.request, self.kwargs = request, kwargs
		self.employee_id = self.kwargs['employee_id']
		self.worker = Employee.objects.get(pk=self.employee_id)

		if self.request.method == 'GET':
			self.month, self.year = self.kwargs['month'], self.kwargs['year']
			self.choice_date = datetime.strptime(f'{self.month}/{self.year}','%m/%Y')

		elif self.request.method == 'POST':
			self.choice_date = datetime.strptime(self.request.POST['choice_date'],'%m/%Y')
			self.month, self.year = self.choice_date.month, self.choice_date.year

		if self.month == 12:
			self.cut_off_month, self.cut_off_year = 1, self.year + 1
		else:
			self.cut_off_month, self.cut_off_year = self.month + 1, self.year

		self.cut_off_date = datetime.strptime(f'{self.cut_off_month}/{self.cut_off_year}','%m/%Y')
		q1 = Q(employeedata__start_contract__lt=self.cut_off_date)
		q2 = Q(employeedata__end_contract__gte=self.choice_date) | Q(employeedata__end_contract__isnull=True)
		self.employees = Employee.objects.filter(q1 & q2).order_by('surname', 'forename')
		query = Q(worker=self.worker, start_work__year=self.year, start_work__month=self.month)
		self.work_hours = WorkEvidence.objects.filter(query)
		self.holidays = holiday(self.year)
		self.year_leaves = EmployeeLeave.objects.filter(worker=self.worker, leave_date__year=self.year)
		query = Q(worker=self.worker, leave_date__year=self.year, leave_date__month=self.month)
		self.sml = EmployeeLeave.objects.filter(query)


	def get(self, request, **kwargs) -> render:
		form = PeriodCurrentComplexDataForm(initial={'choice_date': self.choice_date})
		leave_kind = ('unpaid_leave', 'paid_leave', 'maternity_leave')
		month_leaves = {kind:self.sml.filter(leave_flag=kind).count() for kind in leave_kind}
		year_leaves = {kind:self.year_leaves.filter(leave_flag=kind).count() for kind in leave_kind}
		context = {'form': form, 'employee_id': self.employee_id, 'choice_date': self.choice_date,
		           'employees': self.employees, 'month_leaves': month_leaves, 'year_leaves': year_leaves,
		           'month': self.month, 'year': self.year, 'holidays' : self.holidays, 'worker': self.worker,
		           'sml': self.sml.order_by('leave_date'), 'work_hours': self.work_hours.order_by('start_work')}
		employee_total_data(self.employee_id, self.year, self.month, context)
		# data for modal chart
		context.__setitem__('total_brutto_set', data_modal_chart(self.employee_id))

		return render(request, r'evidence/current_complex_evidence_data.html', context)

	def post(self, request, **kwargs) -> render:
		form = PeriodCurrentComplexDataForm(data={'choice_date':self.choice_date})
		# data for modal chart
		context = {'total_brutto_set': data_modal_chart(self.employee_id)}

		if form.is_valid():
			leave_kind = ('unpaid_leave', 'paid_leave', 'maternity_leave')
			month_leaves = {kind:self.sml.filter(leave_flag=kind).count() for kind in leave_kind}
			year_leaves = {kind:self.year_leaves.filter(leave_flag=kind).count() for kind in leave_kind}
			context.update({'form': form, 'employee_id': self.employee_id, 'choice_date': self.choice_date,
			                'employees': self.employees, 'month_leaves': month_leaves, 'year_leaves': year_leaves,
			                'month': self.month, 'year': self.year, 'holidays' : self.holidays, 'worker': self.worker,
			                'sml': self.sml.order_by('leave_date'), 'work_hours': self.work_hours.order_by('start_work')})
			employee_total_data(self.employee_id, self.year, self.month, context)

		else:
			context.update({'form': form, 'employee_id': self.employee_id, 'employees': self.employees, 'worker': self.worker})

		return render(request, r'evidence/current_complex_evidence_data.html', context)


class WorkhoursPrintView(View):
	'''class representing the view of workhours print'''
	def get(self, request, employee_id:int, month=None, year=None):
		'''send statement of workhours as pdf attachmnet on browser'''
		if month == None and year == None:
			month, year = now().month, now().year

		html = workhourshtml2pdf(employee_id, month, year)

		if html:
			# create pdf file
			filename = f'workhours_{employee_id}.pdf'
			response = make_attachment(html,filename)

			return response
		else:
			messages.warning(request, r'Nothing to print...')

		return HttpResponseRedirect(reverse('evidence:employee_complex_data_args', args=[employee_id, month, year]))


class PlotChart(View):

	def post(self, request, employee_id:int, month:int, year:int) -> HttpResponseRedirect:
		year_data = int(request.POST['plot_year'])
		plot_chart(employee_id, year_data)

		return HttpResponseRedirect(reverse('evidence:employee_complex_data_args', args=[employee_id, month, year]))
