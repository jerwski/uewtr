# standard library
import socket
import platform
from ftplib import FTP
from pathlib import Path
from datetime import datetime

# django library
from django.conf import settings
from django.contrib import messages
from django.dispatch import receiver
from django.utils.timezone import now
from django.contrib.auth import logout
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.db.models.signals import post_save
from django.core.management import call_command
from django.views.generic import CreateView, View
from django.shortcuts import render, get_object_or_404


# my models
from employee.models import *
from evidence.models import *
from account.models import Quiz
from cashregister.models import *

# my forms
from account.forms import UserCreateForm

# my function
from functions.myfunctions import remgarbage, quizdata, quizset, dirdata
from functions.archive import mkfixture, readfixture, make_archives, uploadFileFTP, backup, getArchiveFilefromFTP, check_FTPconn, cmp_fixtures, exec_script


# Create your views here.

@receiver(post_save, sender=Company, weak=False)
@receiver(post_save, sender=Employee, weak=False)
@receiver(post_save, sender=CashRegister, weak=False)
@receiver(post_save, sender=EmployeeData, weak=False)
@receiver(post_save, sender=WorkEvidence, weak=False)
@receiver(post_save, sender=EmployeeLeave, weak=False)
@receiver(post_save, sender=AccountPayment, weak=False)
@receiver(post_save, sender=EmployeeHourlyRate, weak=False)
def set_backup(sender, **kwargs):
	if sender:
		backup_models.append(sender.__name__.lower())
		return backup_models


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
			context.update({'usage': dirdata()})
			employee = Employee.objects.all()
			
			if request.session.get('check_update', True):
				global _queryset, backup_models
				backup_models = list()
				_queryset = quizdata()
				if socket.gethostname() in settings.HOME_HOSTS:
					args = (settings.FTP, settings.FTP_USER, settings.FTP_LOGIN, settings.ARCHIVE_FILE, settings.ROOT_BACKUP)
					getArchiveFilefromFTP(request, *args)
				else:
					msg = f'User: {user}, Host name: {socket.gethostname()}, Host addres: {socket.gethostbyname("localhost")}'
					messages.info(request, msg)
				request.session['check_update'] = False
			
			if employee.exists():
				if employee.filter(status=True):
					employee_id = employee.filter(status=True).first().id
				else:
					employee_id = employee.first().id
				context.update({'employee_id': employee_id, 'nodata': False})
			else:
				backup = settings.ARCHIVE_ROOT
				created = datetime.fromtimestamp(backup.stat().st_mtime)
				context.update({'nodata': True, 'backup': str(backup), 'created': created})
				return render(request, '500.html', context)

			if socket.gethostname() == settings.SERIALIZE_HOST:
				context.__setitem__('serialize', True)

			if check_FTPconn():
				try:
					with FTP(settings.FTP, settings.FTP_USER, settings.FTP_LOGIN) as myFTP:
						try:
							files = [name for name, facts in myFTP.mlsd(settings.FTP_SERIALIZE) if facts['type']=='file']
							if files:
								context.__setitem__('ftp_files', True)
						except:
							context.__setitem__('ftp_files', False)
				except:
					messages.error(request, f'Occurred problem with FTP connection... Directory: {settings.FTP_SERIALIZE}')
			else:
				messages.error(request, r'Occurred problem with FTP connection...')

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


class SerializeView(View):
	'''class to serializng database'''
	def get(self, request)->HttpResponseRedirect:
		if check_FTPconn() and cmp_fixtures():
			root = Path(settings.FTP_SERIALIZE)
			try:
				with FTP(settings.FTP, settings.FTP_USER, settings.FTP_LOGIN) as myFTP:
					dirs = (item[0] for item in myFTP.mlsd(path=root.parent))
					if root.name not in dirs:
						myFTP.mkd(settings.FTP_SERIALIZE)

					myFTP.cwd(settings.FTP_SERIALIZE)
					for file in list(Path.iterdir(settings.TEMP_SERIALIZE)):
						with file.open('rb') as fixture:
							myFTP.storbinary(f'STOR {file.name}', fixture)
						messages.info(request, f'\nFile <<{file.name}>> was sent on the FTP server')
						file.unlink()
				Path.rmdir(settings.TEMP_SERIALIZE)
				messages.info(request, r'All fixtures have been serializing...')
			except:
				msg = f'Occurred problem with FTP connection. Directory: {settings.FTP_SERIALIZE}'
				messages.error(request, msg)

		else:
			messages.info(request, r'All files are up to date...')

		return HttpResponseRedirect(reverse_lazy('account:dashboard'))


class DeserializeView(View):
	'''class to deserializng database'''
	def get(self, request)->HttpResponseRedirect:

		if not Path.exists(settings.ADMIN_SERIALIZE):
			Path.mkdir(settings.ADMIN_SERIALIZE)

		if check_FTPconn():
			try:
				with FTP(settings.FTP, settings.FTP_USER, settings.FTP_LOGIN) as myFTP:
					myFTP.cwd(settings.FTP_SERIALIZE)
					files = (name for name, facts in myFTP.mlsd() if facts['type']=='file')
					for file in files:
						myFTP.retrbinary(f'RETR {file}', open(f'{settings.ADMIN_SERIALIZE}/{file}', 'wb').write)
						myFTP.delete(file)
						messages.info(request, f'\nThe file <<{file}>> has been copied into<<{settings.ADMIN_SERIALIZE}>>')
			except:
				messages.info(request, f'There aren\'t files in {settings.FTP_SERIALIZE}')
		else:
			messages.info(request, r'Occurred problem with FTP connection...')

		readfixture(request, settings.ADMIN_SERIALIZE)
		messages.info(request, f'\nAll database have been deserializing....')

		return HttpResponseRedirect(reverse_lazy('account:dashboard'))


class QuizView(View):

	def get(self, request, quiz_id=None)->render:
		user = request.user
		context = {'user': user}

		if quiz_id:
			try:
				query, answer, answers = quizset(_queryset)
				quiz = get_object_or_404(Quiz, pk=quiz_id)
				points, set_of_questions = quiz.points, quiz.set_of_questions
				start_play, end_play = quiz.start_play, quiz.end_play
	
				if end_play:
					playtime = end_play - start_play
					playtime = str(playtime).split('.')[0]
				else:
					playtime = '0:00:00'
	
				if set_of_questions:
					percent = 20 * points / set_of_questions
				else:
					percent = 0
	
				set_of_questions += 1
				defaults = {'query': query, 'set_of_questions': set_of_questions,
							'answer': answer, 'answers': ';'.join(answers)}
				Quiz.objects.filter(pk=quiz_id).update(**defaults)
				poll = len(_queryset) - 3
				data = {'quiz_id': quiz_id, 'query': query, 'points': points, 'playtime': playtime, 'poll': poll,
						'answers': answers, 'set_of_questions': set_of_questions, 'percent': percent}
				context.update(data)
			except:
				logout(request)
				return HttpResponseRedirect(reverse_lazy('login'))

		else:
			Quiz.objects.all().delete()
			quiz = Quiz.objects.create(player=user, start_play=now(), set_of_questions=0, points=0)
			context.update({'start_play': now(), 'quiz_id': quiz.id})

		return render(request, 'account/quiz.html', context)

	def post(self, request, quiz_id:int)->render:
		your_answer = request.POST['your_answer']
		quiz = get_object_or_404(Quiz, pk=quiz_id)
		points, set_of_questions = quiz.points, quiz.set_of_questions
		query, answer, answers = quiz.query, quiz.answer, quiz.answers.split(';')
		start_play, end_play = quiz.start_play, quiz.end_play

		if end_play:
			playtime = end_play - start_play
			playtime = str(playtime).split('.')[0]
		else:
			playtime = '0:00:00'

		percent = 20 * points / set_of_questions
		context = {'query': query, 'answers': answers, 'percent': percent, 'playtime': playtime,
				   'set_of_questions': set_of_questions, 'quiz_id': quiz_id, 'points': points}

		if your_answer == answer:
			points += 5
			Quiz.objects.filter(pk=quiz_id).update(points=points, end_play=now())

			return HttpResponseRedirect(reverse('account:quiz', args=[quiz_id]))

		else:
			points -= 3
			context.update({'points': points, 'poll': len(_queryset)})
			Quiz.objects.filter(pk=quiz_id).update(points=points, end_play=now())
			return render(request, 'account/quiz.html', context)


def exit(request)->HttpResponseRedirect:
	'''backups features and exit from the application'''
	if platform.system() == 'Darwin':
		paths = (Path('/Users/jurgen/Downloads'), Path('/private/var/tmp'))
	else:
		paths = (Path(r'templates/pdf'), Path('~/Downloads').expanduser())
	args = (settings.ARCHIVE_FILE, settings.FTP_DIR, settings.FTP, settings.FTP_USER, settings.FTP_LOGIN)

	if socket.gethostname() in settings.OFFICE_HOSTS:
		backup()
		mkfixture(settings.ADMIN_SERIALIZE, backup_models=backup_models)
		make_archives(settings.ARCHIVE_NAME, settings.ADMIN_SERIALIZE, settings.ARCHIVE_FILE)
		remgarbage(*paths)

		try:
			if check_FTPconn():
				uploadFileFTP(*args)
				return HttpResponseRedirect(r'https://www.google.pl/')
			else:
				return render(request, '500.html', {'error': 'Occurred problem with FTP connection...'})
		except:
			pass

		finally:
			if request.user.is_authenticated:
				logout(request)

	elif socket.gethostname() in settings.HOME_HOSTS:

		if backup_models:
			backup()
		else:
			print(r'All fixtures are up to date...')

		if request.user.is_authenticated:
			remgarbage(*paths)
			logout(request)

		try:
			if check_FTPconn():
				return HttpResponseRedirect(r'https://www.google.pl/')
		except:
			return render(request, '500.html', {'error': 'Occurred problem with network...'})
		finally:
			if platform.system() == 'Darwin':
				exec_script()
