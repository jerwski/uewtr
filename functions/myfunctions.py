# matplotlib library
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Pillow library
from PIL import Image

# num2words library
import num2words

# standard library
import calendar
from io import BytesIO
from pathlib import Path
from collections import deque
from collections import defaultdict
from random import shuffle, choices, randrange
from datetime import date, datetime, timedelta

# django library
from django.utils.timezone import now
from django.core.mail import EmailMessage
from django.template.loader import get_template
from django.db.models import Case, Count, IntegerField, Max, Q, Sum, Value, When

# my models
from cashregister.models import Company, CashRegister
from employee.models import Employee, EmployeeData, EmployeeHourlyRate
from evidence.models import WorkEvidence, EmployeeLeave, AccountPayment

# my functions
from functions.payment import total_payment, workingdays

# utility tags
from employee.templatetags.utility_tags import money_format


# Create your functions here


def sendemail(subject: str, message: str, sender: int, recipient: list, attachments: list):
	email = EmailMessage(subject, message, sender, recipient)

	for attachment in attachments:
		email.attach_file(attachment)
		email.send(fail_silently=True)


def initial_worktime_form(work_hours: int) -> dict:
	'''return initial data for WorkEvidenceForm'''
	hours = dict(zip([12, 14, 16, 18, 6], [6, 6, 6, 6, 22]))

	if date.today().isoweekday()==1:
		if work_hours==1:
			start_date = date.today() - timedelta(days=2)
			end_date = date.today() - timedelta(days=2)
		elif work_hours==6:
			start_date = date.today() - timedelta(days=3)
			end_date = date.today() - timedelta(days=2)
		else:
			start_date = date.today() - timedelta(days=3)
			end_date = date.today() - timedelta(days=3)
	else:
		if work_hours==6:
			start_date = date.today() - timedelta(days=1)
			end_date = date.today()
		else:
			start_date = date.today() - timedelta(days=1)
			end_date = date.today() - timedelta(days=1)

	start_date = datetime(start_date.year, start_date.month, start_date.day, hours[work_hours], 0)
	end_date = datetime(end_date.year, end_date.month, end_date.day, work_hours, 0)

	initial = {'start_work': start_date, 'end_work': end_date}

	return initial


def initial_account_form(employee_id: int) -> dict:
	'''return initial date for AccountPaymentForm'''
	worker = Employee.objects.get(pk=employee_id)
	account_date = date.today() - timedelta(days=int(date.today().day))
	initial = {'worker': worker, 'account_date': account_date}

	return initial


def initial_leave_form(employee_id: int) -> dict:
	'''return initial leave_flag for EmployeeLeaveForm'''
	worker = Employee.objects.get(pk=employee_id)
	leave_date = date.today() - timedelta(days=1)
	initial = {'worker': worker, 'leave_date': leave_date}
	if worker.leave==1:
		initial.__setitem__('leave_flag', ['paid_leave', ])
	else:
		initial.__setitem__('leave_flag', ['unpaid_leave', ])

	return initial


def erase_records(employee_id: int) -> dict:
	context = dict()
	worker = Employee.objects.get(pk=employee_id)
	opt1, opt2 = {'worker': worker, 'then': Value(1)}, {'default': Value(0), 'output_field': IntegerField()}
	db = {EmployeeData._meta.verbose_name: EmployeeData, WorkEvidence._meta.verbose_name: WorkEvidence,
	      EmployeeLeave._meta.verbose_name: EmployeeLeave, AccountPayment._meta.verbose_name: AccountPayment,
	      EmployeeHourlyRate._meta.verbose_name: EmployeeHourlyRate, }

	for model_name, model in db.items():
		records = model.objects.aggregate(rec=Sum(Case(When(**opt1), **opt2)))
		context.__setitem__(model_name, records['rec'])

	return context


def data_chart(employee_id: int, year: int) -> tuple:
	'''return data for Annual chart income for passed employee_id'''
	_, *month_name = list(calendar.month_name)
	brutto_income = [total_payment(employee_id, year, month)['brutto'] for month in range(1, 13)]
	total_income = sum(brutto_income)
	income = dict(zip(reversed(month_name), reversed(brutto_income)))
	return income, total_income


def plot_chart(employee_id: int, year: int):
	worker = Employee.objects.get(pk=employee_id)
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
		if 0 < v < 300:
			ax.set_xlim(0, max(list(income.values())) * 1.25)
			plt.text(v + len(str(v)), k, money_format(v), ha='left', va='center', fontsize=10, fontweight='bold')
		elif v!=0:
			plt.text(v - len(str(v)), k, money_format(v), ha='right', va='center', fontsize=10, fontweight='bold')
	imgdata = BytesIO()
	fig.savefig(imgdata, format='png')
	imgdata.seek(0)  # rewind the data
	chart = Image.open(imgdata)
	chart.show()


def payrollhtml2pdf(month: int, year: int) -> bool:
	'''convert html file (evidence/monthly_payroll_pdf.html) to pdf file'''
	heads = ['Imię i Nazwisko', 'Brutto', 'Podstawa', 'Urlop', 'Nadgodziny', 'Sobota', 'Niedziela', 'Zaliczka',
	         'Do wypłaty', 'Data i podpis']
	total_work_hours = len(list(workingdays(year, month))) * 8
	employees = Employee.objects.all()
	# building complex query for actual list of employee
	day = calendar.monthrange(year, month)[1]
	query = Q(employeedata__end_contract__lt=date(year, month, 1)) | Q(
			employeedata__start_contract__gt=date(year, month, day))
	employees = employees.exclude(query).order_by('surname')
	if employees.exists():
		# create data for payroll as associative arrays for all employees
		payroll = {employee: total_payment(employee.id, year, month) for employee in employees}
		# create defaultdict with summary payment
		amountpay = defaultdict(float)
		for item in payroll.values():
			if item['accountpay']!=item['brutto']:
				for k, v in item.items():
					amountpay[k] += v

		context = {'heads': heads, 'payroll': payroll, 'amountpay': dict(amountpay), 'year': year, 'month': month,
		           'total_work_hours': total_work_hours}

		template = get_template('evidence/monthly_payroll_pdf.html')
		html = template.render(context)
		return html
	else:
		return False


def leavehtml2pdf(employee_id: int, year: int):
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


def tree(directory: Path):
	'''listing whole tree for passed directory as instance of class WindowsPath'''
	print(f'+ {directory}')
	for path in sorted(directory.rglob('*')):
		depth = len(path.relative_to(directory).parts)
		spacer = '    ' * depth
		print(f'{spacer} + {path.name}')


def remgarbage(*paths: Path):
	'''removes attachment pdf file'''
	patterns = ('leaves_data_*.pdf', 'payroll_*.pdf', 'cashregister_*.pdf', 'cashaccept_*.pdf')
	find = (file for path in paths for file in Path.iterdir(path) for pattern in patterns if file.match(pattern))
	for file in find:
		file.unlink()


def jpk_files(path: Path):
	'''find all .jpk files created in present month and year'''
	files = []
	year, month = now().year, now().month
	for file in path.rglob('JPK/0001/*.xml'):
		created = datetime.fromtimestamp(file.stat().st_ctime)
		if file.match('jpk_fa_*.xml') and created.date().year==year and created.date().month==month:
			files.append(file.as_posix())
		else:
			file.unlink()

	return files


def cashregisterdata(company_id: int, month: int, year: int) -> dict:
	'''return data from cash register'''
	registerdata, saldo = defaultdict(float), 0
	register = CashRegister.objects.filter(company_id=company_id)

	if register.exclude(created__month__gte=month, created__year__gte=year):
		lastdate = register.exclude(created__month__gte=month, created__year__gte=year).latest('created')
		check = {'created__month': lastdate.created.date().month, 'created__year': lastdate.created.date().year}
		lastdata = register.filter(**check)
		incomes = lastdata.aggregate(inc=Sum('income'))
		expenditures = lastdata.aggregate(exp=Sum('expenditure'))
		saldo = incomes['inc'] - expenditures['exp']

		if not register.filter(created__month=month, created__year=year) and saldo > 0:
			transfer = {'company_id': company_id,
			            'symbol': f'RK {lastdate.created.date().month}/{lastdate.created.date().year}',
			            'contents': 'z przeniesienia', 'income': saldo, 'expenditure': 0}
			CashRegister.objects.create(**transfer)

	registerdata['saldo'] = saldo

	presentdata = register.filter(created__month=month, created__year=year).exclude(contents='z przeniesienia')
	for item in presentdata:
		registerdata['incomes'] += item.income
		registerdata['expenditures'] += item.expenditure

	registerdata['status'] = registerdata['incomes'] - registerdata['expenditures'] + saldo

	return registerdata


def cashregisterhtml2pdf(company_id: int, month: int, year: int):
	'''convert html cash register for last month to pdf'''
	company = Company.objects.get(pk=company_id)
	cashregister = CashRegister.objects.filter(company_id=company_id, created__month=month, created__year=year)

	if cashregister.exists():
		# create cash register data as associative arrays for passed arguments
		cashregister = cashregister.exclude(contents='z przeniesienia')
		context = {'company': company, 'cashregister': cashregister, 'month': month, 'year': year}
		registerdata = dict(cashregisterdata(company_id, month, year))
		context.update(registerdata)
		template = get_template(r'cashregister/cashregister_pdf.html')
		html = template.render(context)

		return html
	else:
		return False


def cashaccept2pdf(record: int, number=1):
	'''convert html cash pay/accept for given record to pdf'''
	data = CashRegister.objects.get(pk=record)
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
def quizdata(file:Path=Path('latin.txt'), encoding='utf-8'):
	with file.open('r', encoding=encoding) as file:
		quiz_data=deque(line.rstrip(' \n').split(' – ') for line in file if not line.startswith('=='))

	return quiz_data


def quizset(iterable):

	while len(iterable) >= 4:
		shuffle(iterable)
		query, answer = iterable.popleft()
		answers = [item[1].capitalize() for item in choices(iterable, k=3)]
		answers.insert(randrange(0,4), answer.capitalize())

		return query, answer.capitalize(), answers
	else:
		return None
