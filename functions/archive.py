# standard library
import os
from ftplib import FTP
from pathlib import Path
from datetime import date
import http.client as client
from shutil import make_archive, unpack_archive

# django core
from django.apps import apps
from django.conf import settings
from django.contrib import messages
from django.core.management import call_command
from django.core.serializers import serialize, BadSerializer


# my models
from cashregister.models import Company, CashRegister
from employee.models import Employee, EmployeeData, EmployeeHourlyRate
from evidence.models import WorkEvidence, EmployeeLeave, AccountPayment


# Create your archive functions here.


def check_internet_connection()->bool:
    '''checks whether the internet is connected'''
    connect = client.HTTPConnection("www.google.com", timeout=5)
    try:
        connect.request("HEAD", "/")
        connect.close()
        return True
    except:
        connect.close()
        return False


def backup():
    '''total backup of database'''
    try:
        with settings.ARCHIVE_ROOT.open('w') as jsonfile:
            call_command('dumpdata', indent=4, stdout=jsonfile)
    except FileNotFoundError as error:
        print(f'Something wrong... Error: {error}')


def mkfixture(root_backup):
    '''create fixtures in json format'''
    year = date.today().year
    querys = {'employee': Employee.objects.all(),
              'employee data': EmployeeData.objects.all(),
              'employee hourly rate': EmployeeHourlyRate.objects.filter(update__year=year),
              'work evidence': WorkEvidence.objects.filter(start_work__year=year),
              'employee leave': EmployeeLeave.objects.filter(leave_date__year=year),
              'account payment': AccountPayment.objects.filter(account_date__year=year),
              'company': Company.objects.filter(created__year=year),
              'cash register': CashRegister.objects.filter(created__year=year)}
    try:
        for app in ('employee', 'evidence', 'cashregister'):
            models = apps.all_models[app]
            for model in models.values():
                with Path.cwd().joinpath(f'{root_backup}/{model._meta.model_name}.json').open('w') as fixture:
                    serialize('json', querys[f'{model._meta.verbose_name}'], indent=4, stream=fixture)
    except FileNotFoundError as error:
        print(f'Serialization error: {error}')


def readfixture(request, root_backup):
    try:
        for file in list(Path.iterdir(root_backup)):
            call_command('loaddata', file)
            messages.info(request, f'Fixture {file.name} have beed loaded...\n')
    except FileNotFoundError as error:
        messages.error(request, f'Fixture don\'t exist... => Error code: {error}')


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


def invoices_backup():
    '''create compressed in zip format archive file with invoices'''
    root = Path(os.path.expanduser('~'))
    root_backup= root.joinpath('Desktop/Invoice_backup')
    base_dir = root.joinpath('Desktop/zip2ftp')
    base_name = base_dir.joinpath('invoices')
    backup_file = base_name.with_suffix('.zip')
    make_archives(base_name, root_backup, backup_file)
    if check_internet_connection():
        with FTP(settings.FTP, settings.FTP_USER, settings.FTP_LOGIN) as myFTP:
            myFTP.cwd(r'Invoice_backup')
            if myFTP.size(backup_file.name) != backup_file.stat().st_size:
                return True
            else:
                return False
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


def getArchiveFilefromFTP(request, server:str, username:str, password:str, archive_file, root_backup):
    '''loading compressed in zip format archive file with fixtures on ftp server'''
    if check_internet_connection():
        try:
            with FTP(server, username, password) as myFTP:
                myFTP.cwd(r'/unikolor_db/')
                if Path.is_file(archive_file):
                    if myFTP.size(archive_file.name) > archive_file.stat().st_size:
                        archive_file.unlink()
                        myFTP.retrbinary(f'RETR {archive_file.name}', open(archive_file, 'wb').write)
                        messages.info(request, f'\nArchive <<{archive_file.name}>> successfully imported...')
                        unpack_archive(archive_file, settings.ROOT_BACKUP, 'zip')
                        messages.info(request, 'The archive has been unpacked...')
                        print(f'\n{"*"*22}\nStart read fixtures...\n{"*"*42}')
                        readfixture(request, settings.ROOT_BACKUP)
                        print(f'{"*"*42}\nFinish read fixtures...\n{"*"*22}\n')
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

        except ConnectionError as error:
            messages.error(request, f'Connection error: {error}')

            return False
    else:
        messages.error(request, r'No internet connection...')



# serialization json
def export_as_json(modeladmin, request, queryset):
    opts = modeladmin.model._meta
    path = Path(f'backup_json/{opts.verbose_name}.json')
    with path.open('w') as file:
        serialize('json', queryset, indent=4, stream=file)
    messages.success(request, f'Selected records have been serialized to <<{opts.verbose_name}>>')


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
        path = Path(f'backup_json/erase_worker/{employee_id}.json')
        with path.open('w') as file:
            serialize('json', all_records, indent=4, stream=file)
    except BadSerializer as error:
        print(f'Serialization error: {error}')
