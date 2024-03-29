# standard library
import os
import shutil
import calendar
import platform
from io import BytesIO
from pathlib import Path
from collections import deque
from collections import defaultdict
from random import shuffle, sample, randrange
from datetime import date, datetime, timedelta

# pdfkit library
import pdfkit

# matplotlib library
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Pillow library
from PIL import Image

# num2words library
import num2words

# PyPDF4 library
from PyPDF4 import PdfFileMerger

# django library
from django.conf import settings
from django.http import HttpResponse
from django.utils.timezone import now
from django.core.mail import EmailMessage
from django.shortcuts import get_object_or_404
from django.template.loader import get_template
from django.db.models import Case, Count, IntegerField, Max, Q, Sum, Value, When

# my models
from cashregister.models import Company, CashRegister
from employee.models import Employee, EmployeeData, EmployeeHourlyRate
from evidence.models import WorkEvidence, EmployeeLeave, AccountPayment
from accountancy.models import AccountancyDocument, AccountancyProducts

# my functions
from functions.payment import total_payment, workingdays, holiday

# utility tags
from employee.templatetags.utility_tags import money_format


# Create your functions here


def sendemail(subject:str, message:str, sender:str, recipient:list, attachments:list, cc=None):
	email = EmailMessage(subject, message, sender, recipient, cc)

	for attachment in attachments:
		email.attach_file(attachment)
		email.send(fail_silently=True)


def initial_worktime_form(work_hours:int) -> dict:
	'''
	return initial data for WorkEvidenceForm,
	args; 12=>06:00-12:00, 14=>12=06:00-14:00,
	16=>06:00-16:00, 18=>06:00-18:00, 6=>22:00-06:00
	'''
	hours = dict(zip([10, 11, 12, 14, 15, 16, 17, 18, 5, 6], [6, 6, 6, 6, 6, 6, 6, 6, 22, 22]))
	start, end = now().date(), now().date()

	if start.isoweekday() == 1:
		if work_hours in [10, 11, 12]:
			start = start - timedelta(days=2)
			end = end - timedelta(days=2)
		elif work_hours in [5, 6]:
			start = start - timedelta(days=3)
			end = end - timedelta(days=2)
		else:
			start = start - timedelta(days=3)
			end = end - timedelta(days=3)

	elif start.isoweekday() == 6:
		if work_hours in [14, 15, 16, 17, 18]:
			start = start - timedelta(days=1)
			end = end - timedelta(days=1)
		elif work_hours == 6:
			start = start - timedelta(days=1)

	elif start.isoweekday() == 7:
		if work_hours in [14, 15, 16, 17, 18]:
			start = start - timedelta(days=2)
			end = end - timedelta(days=2)
		elif work_hours == 12:
			start = start - timedelta(days=1)
			end = end - timedelta(days=1)
		else:
			start = start - timedelta(days=1)
	else:
		if work_hours in [5, 6]:
			start = start - timedelta(days=1)
			end = end
		elif work_hours == 12:
			start = start - timedelta(days=start.isoweekday()+1)
			end = end - timedelta(days=end.isoweekday()+1)
		else:
			start = start - timedelta(days=1)
			end = end - timedelta(days=1)

	start_work = datetime(start.year, start.month, start.day, hours[work_hours], 0)
	end_work = datetime(end.year, end.month, end.day, work_hours, 0)

	initial = {'start_work': start_work, 'end_work': end_work}

	return initial


def previous_month_year(month, year):
	'''return previous month and year'''
	if month==1:
		month, year = 12, year - 1
	else:
		month = month - 1

	return month, year


def initial_account_form(employee_id:int) -> dict:
	'''return initial date for AccountPaymentForm'''
	worker = get_object_or_404(Employee, pk=employee_id)
	jobdays = workingdays(now().year, now().month)
	payday = date(now().year, now().month, 10)
	nowadays = now().date()

	for item in jobdays:
		if item >= payday:
			payday = item
			break

	if nowadays == payday or nowadays == payday - timedelta(days=1):
		account_date = nowadays - timedelta(days=int(nowadays.day))
	else:
		account_date = nowadays

	initial = {'worker': worker, 'account_date': account_date}

	return initial


def initial_leave_form(employee_id:int) -> dict:
	'''return initial leave_flag for EmployeeLeaveForm'''
	worker = get_object_or_404(Employee, pk=employee_id)
	present, state = now().date(), True
	year = present.year
	leave_date = present - timedelta(days=1)

	while state:
		if leave_date in holiday(year).values():
			leave_date -= timedelta(days=1)
		else:
			state = False

	if leave_date.isoweekday() == 7:
		leave_date = leave_date - timedelta(days=2)
	elif leave_date.isoweekday() == 6:
		leave_date = leave_date - timedelta(days=1)

	initial = {'worker': worker, 'leave_date': leave_date}

	if worker.leave==1:
		initial.__setitem__('leave_flag', ['paid_leave',])
	else:
		initial.__setitem__('leave_flag', ['unpaid_leave',])

	return initial


def employee_records(employee_id:int) -> dict:
	context = dict()
	worker = get_object_or_404(Employee, pk=employee_id)

	if worker:
		opt1, opt2 = {'worker': worker, 'then': Value(1)}, {'default': Value(0), 'output_field': IntegerField()}
		db = {EmployeeData._meta.verbose_name: EmployeeData, WorkEvidence._meta.verbose_name: WorkEvidence,
			  EmployeeLeave._meta.verbose_name: EmployeeLeave, AccountPayment._meta.verbose_name: AccountPayment,
			  EmployeeHourlyRate._meta.verbose_name: EmployeeHourlyRate}

		for model_name, model in db.items():
			records = model.objects.aggregate(rec=Sum(Case(When(**opt1), **opt2)))
			context.__setitem__(model_name, records['rec'])

	return context


def data_chart(employee_id:int, year:int) -> tuple:
	'''return data for Annual chart income for passed employee_id'''
	_, *month_name = list(calendar.month_name)
	brutto_income = [total_payment(employee_id, year, month)['brutto'] for month in range(1, 13)]
	total_income = sum(brutto_income)
	income = dict(zip(reversed(month_name), reversed(brutto_income)))
	return income, total_income


def plot_chart(employee_id:int, year:int):
	worker = get_object_or_404(Employee, pk=employee_id)
	income, total_income = data_chart(employee_id, year)
	plt.style.use('dark_background')
	fig, ax = plt.subplots(figsize=(9, 6))
	ax.barh(list(income.keys()), list(income.values()), color='green', label='Income')
	ax.grid(True, linestyle='-.', color='grey')
	fig.legend()
	labels = ax.get_xticklabels()
	plt.setp(labels, rotation=45, horizontalalignment='right')
	ax.set(xlabel='Value [PLN]', ylabel='Months',
		   title=f'Incomes in {year} year for {worker} (total {total_income:,.2f} PLN)')
	for k, v in income.items():
		if 0 < v < 1000:
			ax.set_xlim(0, max(list(income.values())) * 1.25)
			plt.text(v + len(str(v)), k, money_format(v), ha='left', va='center', fontsize=10, fontweight='bold')
		elif v >= 1000:
			plt.text(v - len(str(v)), k, money_format(v), ha='right', va='center', fontsize=10, fontweight='bold')
	imgdata = BytesIO()
	fig.savefig(imgdata, format='png')
	imgdata.seek(0)  # rewind the data
	chart = Image.open(imgdata)
	chart.show()


def payroll_set(month:int, year:int):
	day = calendar.monthrange(year, month)[1]
	# query for employee with valid contract
	val_con = Q(employeedata__end_contract__lt=date(year, month, 1)) | Q(employeedata__start_contract__gt=date(year, month, day))
	employees = Employee.objects.all().exclude(val_con).order_by('surname', 'forename')
	# query for paid leave employee
	qleave=Q(employeeleave__leave_date__year=year, employeeleave__leave_date__month=month) & Q(employeeleave__leave_flag='paid_leave')
	emplq=Employee.objects.filter(qleave).distinct()
	# query for working employee
	weviq=Q(workevidence__start_work__year=year) & Q(workevidence__start_work__month=month) & Q(workevidence__jobhours__isnull=False)
	empweq=Employee.objects.filter(weviq).distinct()

	if employees.exists():
		# create data for payroll as associative arrays for all validate employees
		payroll = {emp: total_payment(emp.id, year, month) for emp in employees if emp in emplq or emp in empweq}

		return payroll

	else:
		return None


def payrollhtml2pdf(month:int, year:int, option=None):
	'''convert html file (evidence/monthly_payroll_pdf.html) to pdf file'''
	heads = ['Imię i Nazwisko', 'Brutto', 'Podstawa', 'Urlop', 'Nadgodziny', 'Sobota', 'Niedziela', 'Zaliczka',
			 'Do wypłaty']
	total_work_hours = len(list(workingdays(year, month))) * 8
	# create data for payroll as associative arrays for all employees
	payroll = payroll_set(month, year)
	# create defaultdict with summary payment
	amountpay = defaultdict(float)
	for item in payroll.values():
		for k, v in item.items():
			amountpay[k] += v

	context = {'heads': heads, 'payroll': payroll, 'amountpay': dict(amountpay),
			   'year': year, 'month': month, 'total_work_hours': total_work_hours}

	template = get_template('evidence/monthly_payroll_pdf.html')
	html = template.render(context)
	# create pdf file with following options
	options = {'page-size': 'A4', 'margin-top': '0.2in', 'margin-right': '0.1in',
			   'margin-bottom': '0.1in', 'margin-left': '0.1in', 'encoding': "UTF-8",
			   'orientation': 'landscape','no-outline': None, 'quiet': '', }

	if option == 'print':
		pdfile = pdfkit.from_string(html, False, options=options, css=settings.CSS_FILE)
		filename = f'payroll_{month}_{year}_simple.pdf'
		# create montly pyroll pdf as attachment
		response = HttpResponse(pdfile, content_type='application/pdf')
		response['Content-Disposition'] = 'attachment; filename="' + filename + '"'

		return response

	elif option == 'send':
		# create pdf file
		pdfile = f'templates/pdf/payroll_{month}_{year}.pdf'
		pdfkit.from_string(html, pdfile, options=options, css=settings.CSS_FILE)

		return pdfile

	else:
		return False


def dphtmpd(month:int, year:int):
	'''dphtmpd = detailed payroll html to multi-page pdf document'''
	multipdf = f'templates/pdf/payroll_{month}_{year}.pdf'
	# create multi-pages pdf menager
	merger = PdfFileMerger()
	# all required data
	leave_kind = ('unpaid_leave', 'paid_leave', 'maternity_leave')
	heads = ['Kwota brutto', 'Podstawa', 'Urlop', 'Nadgodziny', 'Za soboty', 'Za niedziele', 'Zaliczka', 'Do wypłaty']
	total_work_days = len(list(workingdays(year, month)))
	holidays = holiday(year).values()
	payroll = payroll_set(month, year)
	# create context
	context = {'month': month, 'year': year, 'heads': heads, 'total_work_days': total_work_days,}
	# options to create pdf file
	options = {'page-size': 'A5', 'margin-top': '0.25in', 'margin-right': '0.2in', 'margin-bottom': '0.1in',
			   'margin-left': '0.2in', 'encoding': "UTF-8", 'orientation': 'landscape','no-outline': None, 'quiet': '',}

	# holidays workhours query
	holq =Q(start_work__date__in=list(holidays)) & Q(end_work__date__in=list(holidays))
	# Saturday workhours query
	satq = Q(start_work__week_day=7) & (Q(end_work__week_day=7) | Q(end_work__week_day=1))
	# Sunday workhours query
	sunq = Q(start_work__week_day=1) & Q(end_work__week_day=1)
	# leaves
	leaq = Q(leave_date__year=year, leave_date__month=month)

	# create dataset for each active employee
	for key, value in payroll.items():
		worker, payroll_val = key, value
		# payroll data
		salary = payroll_val['salary']
		# eliminate no salary worker
		if salary > 0:
			employeedata = get_object_or_404(EmployeeData, worker=worker)
			# main query
			mainquery = WorkEvidence.objects.filter(worker=worker, start_work__year=year, start_work__month=month)
			# Saturdays
			saturday_hours = mainquery.filter(satq).exclude(holq)
			saturday_hours = saturday_hours.aggregate(sh=Sum('jobhours'))['sh']
			# Sundays
			sunday_hours = mainquery.filter(sunq).exclude(holq)
			sunday_hours = sunday_hours.aggregate(sh=Sum('jobhours'))['sh']
			# holidays
			holiday_hours = mainquery.filter(holq)
			holiday_hours = holiday_hours.aggregate(hh=Sum('jobhours'))['hh']
			# total workhours
			total_work_hours = mainquery.aggregate(twh=Sum('jobhours'))['twh']
			# leaves
			year_leaves = EmployeeLeave.objects.filter(worker=worker, leave_date__year=year)
			mls = EmployeeLeave.objects.filter(worker=worker).filter(leaq).order_by('leave_date')
			month_leaves = {kind:mls.filter(leave_flag=kind).count() for kind in leave_kind}
			month_dates = {kind:[item.leave_date for item in mls.filter(leave_flag=kind)] for kind in leave_kind}
			year_leaves = {kind:year_leaves.filter(leave_flag=kind).count() for kind in leave_kind}
			# update context
			context.update({'worker': worker, 'payroll': payroll_val, 'salary': salary,
							'employeedata': employeedata, 'saturday_hours': saturday_hours,
							'month_leaves': month_leaves, 'month_dates': month_dates,
							'sunday_hours': sunday_hours, 'year_leaves': year_leaves,
							'total_work_hours': total_work_hours, 'holiday_hours': holiday_hours})
			# create pdf file with following options
			template = get_template('evidence/monthly_detailed_payroll_pdf.html')
			html = template.render(context)
			pdfile = f'templates/pdf/{worker.surname} {worker.forename} lp_{month}_{year}.pdf'
			pdfkit.from_string(html, pdfile, options=options, css=settings.CSS_FILE)
			# merge all pdf file
			merger.append(pdfile)

	# writete multi-pages pdf file
	merger.write(multipdf)

	return multipdf


def leavehtml2pdf(employee_id:int, year:int) -> bool:
	'''convert html annuall leave time for each employee in current year to pdf'''
	month_name = list(calendar.month_name)[1:]
	worker = get_object_or_404(Employee, pk=employee_id)
	employee = EmployeeLeave.objects.filter(worker=worker, leave_date__year=year)
	if employee.exists():
		employee = employee.order_by('leave_date')
		# create leaves data as associative arrays for selected employee
		leave_data = [item.leave_date for item in employee]
		context = {'leave_data': leave_data, 'month_name': month_name, 'worker': worker, 'year': year}
		template = get_template(r'evidence/leaves_data_pdf.html')
		html = template.render(context)
		return html
	else:
		return False


def workhourshtml2pdf(employee_id:int, month:int, year:int) -> bool:
	'''convert html workhours for curent employee in month and year parameters to pdf'''
	worker = get_object_or_404(Employee, pk=employee_id)
	employee_leave = EmployeeLeave.objects.filter(worker=worker, leave_date__year=year, leave_date__month=month)
	work_hours = WorkEvidence.objects.filter(worker=worker, start_work__year=year, start_work__month=month)
	context = {'work_hours': work_hours.order_by('start_work'), 'worker': worker, 'month': month, 'year': year}

	if worker:
		if work_hours.exists():
			total_hours = work_hours.aggregate(th=Sum('jobhours'))
			total_hours = total_hours['th']
		else:
			total_hours = 0

		if employee_leave.exists():
			employee_leave = employee_leave.order_by('leave_date')
			# create leaves data as associative arrays for selected employee
			leave_data = [item.leave_date for item in employee_leave]
			context.update({'leave_data': leave_data})

		context.update({'total_hours': total_hours})
		template = get_template(r'evidence/workhours_pdf.html')
		html = template.render(context)
		return html
	else:
		return False


def accountpaymenthtml2pdf(employee_id:int, month:int, year:int) -> bool:
	'''convert html statement of advances to pdf'''
	worker = get_object_or_404(Employee, pk=employee_id)
	context = {'worker': worker, 'month': month, 'year': year}

	if worker:
		query = Q(worker=worker) & Q(account_date__year=year) & Q(account_date__month=month)
		advances = AccountPayment.objects.filter(query)
		context.update({'advances': advances})

		if advances is None:
			total_account = 0
		else:
			total_account = advances.aggregate(ta=Sum('account_value'))
			total_account = total_account['ta']

		context.update({'total_account': total_account})
		template = get_template(r'evidence/advances_pdf.html')
		html = template.render(context)

		return html

	else:
		return False


def tree(directory:Path):
	'''listing whole tree for passed directory as instance of class WindowsPath'''
	print(f'+ {directory}')
	for path in sorted(directory.rglob('*')):
		depth = len(path.relative_to(directory).parts)
		spacer = '    ' * depth
		print(f'{spacer} + {path.name}')


def remgarbage(*paths:Path):
	'''removes attachment pdf file'''
	patterns = settings.GARBAGE_PATTERNS
	find = (file for path in paths for file in Path.iterdir(path) for pattern in patterns if file.match(pattern))
	for file in find:
		file.unlink()


# FUNCTION DEPRECATED
def jpk_files(path:Path) -> list:
	'''find all .jpk files created in present month and year'''
	files = []
	year, month = now().year, now().month
	for file in path.rglob('JPK/0001/*.xml'):
		created = datetime.fromtimestamp(file.stat().st_mtime)
		if file.match('jpk_fa_*.xml') and created.date().year==year and created.date().month==month:
			files.append(file.as_posix())
		else:
			file.unlink()

	return files


def cashregisterdata(company_id:int, month:int, year:int) -> dict:
	'''return data from cash register'''
	registerdata, prev_saldo, incomes, expenditures, saldo = dict(), 0 ,0, 0, 0
	register = CashRegister.objects.filter(company_id=company_id)
	current = register.filter(created__month=month, created__year=year)

	if register:
		last_month, last_year = register.last().created.month, register.last().created.year

		if current:
			prev_saldo = current.get(contents='z przeniesienia').income
			income = current.aggregate(inc=Sum('income'))
			expenditures = current.aggregate(exp=Sum('expenditure'))
			incomes, expenditures = income['inc'] - prev_saldo, expenditures['exp']
			saldo = income['inc'] - expenditures
		else:
			last_data = register.filter(created__year=last_year, created__month=last_month)
			income = last_data.aggregate(inc=Sum('income'))
			expenditure = last_data.aggregate(exp=Sum('expenditure'))
			saldo = income['inc'] - expenditure['exp']
			prev_saldo = saldo

			transfer = {'company_id': company_id, 'symbol': f'RK {month}/{year}', 'income': saldo,
						'contents': 'z przeniesienia', 'expenditure': expenditures}
			CashRegister.objects.create(**transfer)

		registerdata.update({'prev_saldo': prev_saldo, 'incomes': incomes, 'expenditures': expenditures, 'saldo': saldo})

	else:
		transfer = {'company_id': company_id, 'symbol': f'RK {month}/{year}', 'income': incomes,
					'contents': 'z przeniesienia', 'expenditure': expenditures}
		CashRegister.objects.create(**transfer)

	return registerdata


def cashregisterhtml2pdf(company_id:int, month:int, year:int) -> bool:
	'''convert html cash register for last month to pdf'''
	company = get_object_or_404(Company, pk=company_id)
	cashregister = CashRegister.objects.filter(company_id=company_id, created__month=month, created__year=year)

	if cashregister.exists():
		# create cash register data as associative arrays for passed arguments
		cashregister = cashregister.exclude(contents='z przeniesienia')
		context = {'company': company, 'cashregister': cashregister, 'month': month, 'year': year}
		registerdata = cashregisterdata(company_id, month, year)
		context.update(registerdata)
		template = get_template(r'cashregister/cashregister_pdf.html')
		html = template.render(context)

		return html
	else:
		return False


def make_attachment(html, filename) -> HttpResponse:
	options = {'page-size'  : 'A4', 'margin-top': '0.4in', 'margin-right': '0.2in', 'margin-bottom': '0.2in',
			   'margin-left': '0.6in', 'encoding': "UTF-8", 'orientation': 'portrait', 'no-outline': None, 'quiet': ''}

	pdf = pdfkit.from_string(html, False, options=options, css=settings.CSS_FILE)

	response = HttpResponse(pdf, content_type='application/pdf')
	response['Content-Disposition'] = 'attachment; filename="' + filename + '"'

	return response


def cashaccept2pdf(record:int, number=1):
	'''convert html cash pay/accept for given record to pdf'''
	data = get_object_or_404(CashRegister, pk=record)
	context = {'data': data}
	company, created, month, year = data.company, data.created, data.created.month, data.created.year
	check = Q(company=company, created__month=month, created__year=year)
	register = CashRegister.objects.filter(check)
	position = register.filter(created__lte=created).exclude(contents='z przeniesienia').aggregate(position=Count('pk'))
	context.update(position)

	if data.income:
		template = get_template(r'cashregister/cashaccept.html')

		if data.cashaccept:
			number = data.cashaccept
		else:
			maxnumber = register.filter(expenditure=0, cashaccept__isnull=False).aggregate(Max('cashaccept'))
			if maxnumber['cashaccept__max']:
				number = maxnumber['cashaccept__max'] + 1
			else:
				number = number

			CashRegister.objects.filter(pk=record).update(cashaccept=number)

		numwords = num2words.num2words(data.income, lang='pl', to='currency', currency='PLN')
	else:
		template = get_template(r'cashregister/cashpay.html')

		if data.cashaccept:
			number = data.cashaccept
		else:
			maxnumber = register.filter(income=0, cashaccept__isnull=False).aggregate(Max('cashaccept'))
			if maxnumber['cashaccept__max']:
				number = maxnumber['cashaccept__max'] + 1
			else:
				number = number

			CashRegister.objects.filter(pk=record).update(cashaccept=number)

		numwords = num2words.num2words(data.expenditure, lang='pl', to='currency', currency='PLN')

	context.__setitem__('number', number)
	context.__setitem__('numwords', numwords)
	html = template.render(context)

	return html


# quiz
def quizdata(file:Path=Path('latin.txt'), encoding='utf-8') -> deque:
	with file.open('r', encoding=encoding) as file:
		quiz_data=deque(line.rstrip(' \n').split(' – ') for line in file if not line.startswith('=='))

	return quiz_data


# upper first letter
def upperfirst(string:str) -> str:

	return string[:1].upper() + string[1:]


def quizset(iterable):

	if len(iterable) >= 4:
		shuffle(iterable)
		query, answer = iterable.popleft()
		answers = [upperfirst(item[1]) for item in sample(iterable, k=3)]
		answers.insert(randrange(0,4), upperfirst(answer))

		return query, upperfirst(answer), answers

	else:
		return None


def spaceusage() -> dict:
	usage = dict()
	if platform.system() == 'Darwin':
		usage |= {'Macintosh HD': shutil.disk_usage('/')._asdict()}
	elif platform.system() == 'Windows':
		drivers = [chr(x)+':' for x in range(65,90) if os.path.exists(chr(x)+':')]
		usage = {drive: shutil.disk_usage(drive)._asdict() for drive in drivers}
	else:
		usage |= {'unknown':{'total': 'You should check someself'}}

	for key, value in usage.items():
		percent = value['used'] * 100 / value['total']
		usage[key].update({'percent': percent})

	return usage


def last_relased_accountancy_document(company_id:int=None) -> int:
	check = {'company_id': company_id, 'created__year': now().year, 'created__month': now().month}
	documents = AccountancyDocument.objects.filter(**check)

	for document in documents:
		if not AccountancyProducts.objects.filter(document_id=document.id):
			document.delete()

	number = AccountancyDocument.objects.filter(**check).aggregate(Max('number'))

	if number['number__max']:
		number = number['number__max'] + 1
	else:
		number = 1

	return number


def rempid():
	if platform.system() == 'Darwin':
		path2pid = Path('/Users/jurgen/Library/Application Support/Postgres/var-11/')
		pidfile = 'postmaster.pid'
		# if old .pid file exist should be removed
		pid = path2pid/pidfile

		if pid.exists():
			pid.unlink()
			print(f'After removed {pid} file you should be restart your PostgreSQL Database')


# with statement
class FileTimeWriter():

	def __init__(self, file_name, mode='w', encoding='utf-8'):
		self.file_name = file_name
		self.mode = mode
		self.encoding = encoding

	def __enter__(self):
		self.file = open(self.file_name, self.mode, encoding=self.encoding)
		self.open_t = now()
		self.file.write(f'File open at: {self.open_t}\n')
		return self.file

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.close_t = now()
		self.file.write(f'\nFile closed at: {self.close_t}')
		self.file.close()

# using with statement with FileTimeWriter

# with FileTimeWriter('myfile.txt') as file:
# 	file.write('Hello World')
