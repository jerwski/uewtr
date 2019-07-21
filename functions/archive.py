# standard library
import urllib3
from ftplib import FTP
from pathlib import Path
from collections import deque
from shutil import make_archive, unpack_archive

# django core
from django.apps import apps
from django.conf import settings
from django.contrib import messages
from django.utils.timezone import now
from django.core.management import call_command
from django.core.serializers import serialize, BadSerializer


# my models
from employee.models import Employee


# Create your archive functions here.


def check_internet_connection() -> bool:
	try:
		http = urllib3.PoolManager()
		req = http.request('GET', settings.FTP)
		if req.status == 200:
			return True
		else:
			return False
	except:
		return False


def backup():
	'''total backup of database'''
	if Employee.objects.all().exists():
		try:
			with settings.ARCHIVE_ROOT.open('w', encoding='utf-8') as jsonfile:
				call_command('dumpdata', indent=4, stdout=jsonfile)
			print(f'\nBackup is created at {now().ctime()} in the {settings.ARCHIVE_ROOT} file\n')
		except FileNotFoundError as error:
			print(f'Something wrong... Error: {error}')


def mkfixture(root_backup:Path):
	'''create fixtures in json format'''
	# year = date.today().year
	# query = {'employee': Employee.objects.all(),
	# 		 'employeedata': EmployeeData.objects.all(),
	# 		 'employeehourlyrate': EmployeeHourlyRate.objects.all(),
	# 		 'workevidence': WorkEvidence.objects.filter(start_work__year=year),
	# 		 'employeeleave': EmployeeLeave.objects.filter(leave_date__year=year),
	# 		 'accountpayment': AccountPayment.objects.filter(account_date__year=year),
	# 		 'company': Company.objects.filter(created__year=year),
	# 		 'cashregister': CashRegister.objects.filter(created__year=year)}
	try:
		for app in settings.FIXTURES_APPS:
			models = apps.all_models[app]
			for name, model in models.items():
				with Path.cwd().joinpath(f'{root_backup}/{name}').with_suffix('.json').open('w') as fixture:
					serialize('json', model.objects.all(), indent=4, stream=fixture)
	except:
		print(f'Serialization error...')
		pass


def readfixture(request, root_backup:Path):
	files = deque(file for file in root_backup.iterdir() if file.name.startswith('employee'))
	files.extend(file for file in root_backup.iterdir() if file.name.startswith('company'))
	files.extend(file for file in root_backup.iterdir() if not file.name.startswith('employee') and not file.name.startswith('company'))
	try:
		for file in files:
			call_command('loaddata', file)
			messages.info(request, f'Fixture {file.name} have been loaded...\n')
	except FileNotFoundError as error:
		messages.error(request, f'Fixture doesn\'t exist... => Error code: {error}')


def make_archives(archive_name, root_backup, archive_file):
	'''create compressed in zip format archive file with fixtures'''
	if list(Path.iterdir(root_backup)):
		try:
			make_archive(archive_name, 'zip', root_backup)
			print(f'The archive <<{archive_file.name}>> has been packaged...')
		except FileNotFoundError as error:
			print(f'Archiving has failed => Error code: {error}')
	else:
		print(f'Directory {root_backup} is empty...')


def invoices_backup() -> bool:
	'''create compressed in zip format archive file with invoices'''
	root_backup = settings.INVOICE_BACKUP.expanduser()
	base_name = settings.INVOICE_ZIP.expanduser()
	backup_file = base_name.with_suffix('.zip')
	make_archives(base_name, root_backup, backup_file)
	if check_internet_connection():
		with FTP(settings.FTP, settings.FTP_USER, settings.FTP_LOGIN) as myFTP:
			ftpdirs = list(name for name in myFTP.nlst())
			if settings.FTP_INVOICE_DIR.name not in ftpdirs:
				return True
			else:
				myFTP.cwd(settings.FTP_INVOICE_DIR.name)
				if settings.FTP_INVOICE_FILE.name in myFTP.nlst():
					if myFTP.size(backup_file.name) != backup_file.stat().st_size:
						return True
					else:
						return False
				else:
					return True
	else:
		return False


def uploadFileFTP(sourceFilePath:Path, destinationDirectory:Path, server:str, username:str, password:str):
	'''sending compressed in zip format archive file with fixtures on ftp server'''
	if check_internet_connection():
		try:
			with FTP(server, username, password) as myFTP:
				print(f'\nConnected to FTP...<<{myFTP.host}>>')
				ftpdirs = list(name for name in myFTP.nlst())

				if destinationDirectory not in ftpdirs:
					print(f'\nDestination directory <<{destinationDirectory}>> does not exist...\nCreating a target catalog...')
					try:
						myFTP.mkd(destinationDirectory)
						print(f'Destination directory <<{destinationDirectory}>> has been created...')
						myFTP.cwd(destinationDirectory)
						if Path.is_file(sourceFilePath):
							with sourceFilePath.open('rb') as file:
								myFTP.storbinary(f'STOR {sourceFilePath.name}', file)
								print(f'\nThe <<{sourceFilePath.name}>> file has been sent to the directory <<{destinationDirectory}>>\n')
						else:
							print('\nNo source file...')
					except ConnectionRefusedError as error:
						print(f'\nError code: {error}')
				else:
					try:
						myFTP.cwd(destinationDirectory)
						if Path.is_file(sourceFilePath):
							with sourceFilePath.open('rb') as file:
								myFTP.storbinary(f'STOR {sourceFilePath.name}', file)
								print(f'\nFile <<{sourceFilePath.name}>> was sent to the FTP directory <<{destinationDirectory}>>\n')
					except ConnectionRefusedError as error:
						print(f'\nError code: {error}')
		except ConnectionRefusedError as error:
			print(f'\nError code: {error}')
	else:
		print(r'No internet connection...')


def getArchiveFilefromFTP(request, server:str, username:str, password:str, archive_file, root_backup) -> bool:
	'''loading compressed in zip format archive file with fixtures on ftp server'''
	if check_internet_connection():
		try:
			with FTP(server, username, password) as myFTP:
				myFTP.cwd(settings.FTP_BACKUP_DIR)
				if Path.is_file(archive_file):
					if myFTP.size(archive_file.name) != archive_file.stat().st_size:
						archive_file.unlink()
						myFTP.retrbinary(f'RETR {archive_file.name}', open(archive_file, 'wb').write)
						messages.info(request, f'\nArchive <<{archive_file.name}>> successfully imported...')
						unpack_archive(archive_file, settings.ROOT_BACKUP, 'zip')
						messages.info(request, 'The archive has been unpacked...')
						print(f'\n{"*"*22}\nStart read fixtures...\n{"*"*42}')
						readfixture(request, settings.ROOT_BACKUP)
						print(f'{"*"*42}\nFinish read fixtures...\n{"*"*22}\n')
						messages.info(request, f'\nDatabase is up to date...')
					else:
						messages.info(request, f'\nSince the last archiving, the archival file {archive_file.name} remains unchanged...')
				else:
					myFTP.retrbinary(f'RETR {archive_file.name}', open(archive_file, 'wb').write)
					messages.info(request, f'\nArchive <<{archive_file.name}>> successfully imported...')
					unpack_archive(archive_file, root_backup, 'zip')
					messages.info(request, 'The archive has been added and unpacked...')
					print(f'\n{"*"*22}\nStart read fixtures...\n{"*"*42}')
					readfixture(request, settings.ROOT_BACKUP)
					print(f'{"*"*42}\nFinish read fixtures...\n{"*"*22}\n')

				return True

		except ConnectionRefusedError as error:
			messages.error(request, f'Someting wrong: {error}')

			return False
	else:
		messages.error(request, r'No internet connection...')


# serialization json
def export_as_json(modeladmin, request, queryset):
	opts = modeladmin.model._meta
	path = Path(f'{settings.ADMIN_SERIALIZE}/{opts}').with_suffix('.json')
	try:
		if not path.exists():
			Path.mkdir(path.parent)
		with path.open('w') as file:
			serialize('json', queryset, indent=4, stream=file)
		messages.success(request, f'Selected records have been serialized to <<{opts.verbose_name}>>')
	except:
		messages.warning(request, f'The {path.parent} directory can\'t be created...')


# archiving of delete records
def archiving_of_deleted_records(employee_id):
	all_records = []

	try:
		for app in ('employee', 'evidence'):
			models = apps.all_models[app]
			for model in models.values():
				if model._meta.model_name=='employee':
					all_records.append(model.objects.get(pk=employee_id))
				else:
					all_records += list(model.objects.filter(worker_id=employee_id))
		path = Path(f'{settings.BACKUP_ERASE_WORKER}/{employee_id}').with_suffix('.json')
		with path.open('w', encoding='utf-8') as file:
			serialize('json', all_records, indent=4, stream=file)

	except BadSerializer as error:
		print(f'Serialization error: {error}')
