# standard library
import socket
from pathlib import Path
from datetime import datetime

# django library
from django.conf import settings
from django.shortcuts import render
from django.contrib import messages
from django.utils.timezone import now
from django.contrib.auth import logout
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.core.management import call_command
from django.views.generic import CreateView, View

# my models
from account.models import Quiz
from employee.models import Employee
from cashregister.models import Company

# my forms
from account.forms import UserCreateForm

# my function
from functions.myfunctions import remgarbage, sendemail, jpk_files, quizdata, quizset
from functions.archive import mkfixture, make_archives, uploadFileFTP, backup, getArchiveFilefromFTP, check_internet_connection, invoices_backup


# Create your views here.


class RegisterView(CreateView):
	'''class implementing the method of registring new user'''
	template_name ='registration/register.html'
	form_class = UserCreateForm
	success_url = reverse_lazy('login')


class AdminView(View):
	'''class implementing the method of view application's dashboard'''
	def get(self, request)->HttpResponseRedirect:
		if request.user.is_superuser or request.user.is_staff:
			user = request.user.username
			context = {'user': user}
			employee = Employee.objects.filter(status=True).first()
			if employee:
				employee_id = employee.id
				context.update({'employee_id': employee_id, 'nodata': False})
			else:
				backup = Path(r'backup_json/db.json')
				created = datetime.fromtimestamp(backup.stat().st_ctime)
				context.update({'nodata': True, 'backup': str(backup), 'created': created})
				return render(request, '500.html', context)

			if list(Path(r'E:/Fakturowanie').rglob(r'JPK/0001/jpk_fa_*.xml')):
				context.__setitem__('jpk', True)
			if Path('~/Desktop/zip2ftp/invoices.zip').expanduser().is_file():
				context.__setitem__('upload', True)

			if socket.gethostname() == 'HOMELAPTOP':
				args = (settings.FTP, settings.FTP_USER, settings.FTP_LOGIN, settings.ARCHIVE_FILE, settings.ROOT_BACKUP)
				getArchiveFilefromFTP(request, *args)

			return render(request, 'account/admin.html', context)

		return HttpResponseRedirect(reverse_lazy('login'))


class RestoreDataBase(View):
	'''class that allows restoring all records to the database from last saved backup file'''
	def get(self, request):
		try:
			call_command('loaddata', settings.ARCHIVE_ROOT)
			messages.info(request, f'Database have been restored...\n')
		except FileNotFoundError as error:
			messages.error(request, f'Backup file <<{settings.ARCHIVE_ROOT}>> doesn\'t exist... => Error code: {error}')

		return HttpResponseRedirect(reverse_lazy('login'))


class Invoices2Ftp(View):
	'''class that allows archiving the database of issued invoices'''
	def get(self, request)->HttpResponseRedirect:
		backup_file = Path('~/Desktop/zip2ftp/invoices.zip').expanduser()
		ftp_invoice_dir = r'Invoice_backup'
		args = (backup_file, ftp_invoice_dir, settings.FTP, settings.FTP_USER, settings.FTP_LOGIN)
		if socket.gethostname() == 'OFFICELAPTOP' and invoices_backup():
			uploadFileFTP(*args)
			messages.info(request, f'\nInvoices archive is safe...')

		return HttpResponseRedirect(reverse_lazy('account:admin_site'))


class JPK2Accountancy(View):
	'''class to send JPK files to accountancy'''
	def get(self, request):
		if check_internet_connection():
			files = jpk_files(Path(r'E:/Fakturowanie/'))

			if files:
				stamp = now().strftime("%A %d %B %Y %H%M%S.%f")
				companies = Company.objects.filter(status=1).order_by('company').values_list('company', flat=True)
				# send e-mail with attached cash register as file in pdf format
				if now().month == 1:
					month, year = 12, now().year - 1
				else:
					month, year = now().month - 1, now().year
				mail = {'subject': f'pliki JPK za okres {month}/{year}',
				        'message': f'W załączniku pliki JPK dla {list(companies)} za okres {month}/{year}r.',
				        'sender' : settings.EMAIL_HOST_USER, 'recipient': ['biuro.hossa@wp.pl'], 'attachments': files}
				sendemail(**mail)
				messages.info(request, f'JPK files for {list(companies)} on {month}/{year} was sending to accountancy....')

				for nr, file in enumerate(files,1):
					file, parent, suffix = Path(file), Path(file).parent, Path(file).suffix
					file.rename(parent/f'sent{nr}{stamp}{suffix}')
		else:
			messages.error(request, 'No internet connection...')

		return HttpResponseRedirect(reverse_lazy('account:admin_site'))


class QuizView(View):
	def get(self, request, quiz_id:int=None)->render:
		user = request.user
		queryset = quizdata()
		context = {'user': user}
		if quiz_id == None:
			start_play = now()
			quiz = Quiz.objects.create(player=user, start_play = start_play, set_of_questions=0, points=0)
			context.update({'start_play': start_play, 'quiz_id': quiz.id})
		else:
			query, answer, answers = quizset(queryset)
			quiz = Quiz.objects.get(pk=quiz_id)
			points, set_of_questions = quiz.points, quiz.set_of_questions

			if set_of_questions:
				percent = 20 * points / set_of_questions
			else:
				percent = 0

			set_of_questions += 1
			defaults = {'query': query, 'set_of_questions': set_of_questions,
			            'answer': answer, 'answers': ';'.join(answers)}
			Quiz.objects.filter(pk=quiz_id).update(**defaults)
			data = {'quiz_id': quiz_id, 'query': query, 'points': points, 'answer': answer,
			        'answers': answers, 'set_of_questions': set_of_questions, 'percent': percent}
			context.update(data)

		return render(request, 'account/quiz.html', context)

	def post(self, request, quiz_id:int)->render:
		your_answer = request.POST['your_answer']
		quiz = Quiz.objects.get(pk=quiz_id)
		points = quiz.points
		query, answer, answers, set_of_questions = quiz.query, quiz.answer, quiz.answers.split(';'), quiz.set_of_questions
		percent = 20 * points / set_of_questions
		context = {'query': query, 'answer': answer, 'answers': answers, 'percent': percent,
		           'set_of_questions': set_of_questions, 'quiz_id': quiz_id, 'points': points}

		if your_answer == answer:
			points += 5
			context.__setitem__('points', points)
			Quiz.objects.filter(pk=quiz_id).update(points=points, end_play=now())

			return HttpResponseRedirect(reverse('account:quiz', args=[quiz_id]))

		else:
			return render(request, 'account/quiz.html', context)


def exit(request)->HttpResponseRedirect:
	'''backups features and exit from the application'''
	paths = (Path(r'templates/pdf'), Path('~/Downloads').expanduser())
	args = (settings.ARCHIVE_FILE, settings.FTP_DIR, settings.FTP, settings.FTP_USER, settings.FTP_LOGIN)

	if socket.gethostname() == 'OFFICELAPTOP':
		backup()
		mkfixture(settings.ROOT_BACKUP)
		make_archives(settings.ARCHIVE_NAME, settings.ROOT_BACKUP, settings.ARCHIVE_FILE)
		remgarbage(*paths)

		try:
			if check_internet_connection():
				uploadFileFTP(*args)
				return HttpResponseRedirect(r'https://www.google.pl/')
			else:
				return render(request, '500.html', {'error': ConnectionError.__doc__})
		except:
			pass

		finally:
			if request.user.is_authenticated:
				logout(request)

	elif socket.gethostname() == 'HOMELAPTOP':
		if request.user.is_authenticated:
			backup()
			remgarbage(*paths)
			logout(request)
		if check_internet_connection():
			return HttpResponseRedirect(r'https://www.google.pl/')
		else:
			return render(request, '500.html', {'error': ConnectionError.__doc__})
