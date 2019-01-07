# standard library
import filecmp
import pathlib
import http.client as client
from ftplib import FTP, error_reply
from shutil import make_archive, unpack_archive, copy2, ExecError

# django core
from django.conf import settings
from django.contrib import messages
from django.core import serializers
from django.core.management import call_command

# my models
from employee.models import EmployeeData, EmployeeHourlyRate
from evidence.models import WorkEvidence, EmployeeLeave, AccountPayment


# Create your archive functions here.


def check_internet_connection():
    connect = client.HTTPConnection("www.google.com", timeout=5)
    try:
        connect.request("HEAD", "/")
        connect.close()
        return True
    except:
        connect.close()
        return False


def backup(request):
    '''total backup of data base'''
    path = pathlib.Path(r'backup_json/db.json')
    try:
        with open(path, 'w') as jsonfile:
            call_command('dumpdata', indent=4, stdout=jsonfile)
    except FileNotFoundError as error:
        messages.error(request, f'Something wrong... Error: {error}')


def mkfixture(request):
    '''create fixtures in json format'''
    for model, path in settings.FIXTURE_DIRS.items():
        try:
            with open(path, 'w') as jsonfile:
                call_command('dumpdata', model, indent=4, stdout=jsonfile)
        except FileNotFoundError as error:
            messages.error(request, f'Serialization error: {error}')


def readfixture(request):
    '''reading fixtures'''
    for model, path in settings.FIXTURE_DIRS.items():
        try:
            call_command('loaddata', path)
            mymodel = model.split('.')[1]
            messages.info(request, f'Base {mymodel} has been updated...\n')
        except FileNotFoundError as error:
            messages.error(request, f'No data => Error code: {error}')


def make_archives(request):
    '''create compressed in zip format archive file with fixtures'''
    archive_name = pathlib.Path(r'backup_json/zip/wtr_archive')
    root_dir = pathlib.Path(r'backup_json/wtr_archive')
    if list(pathlib.Path.iterdir(root_dir)):
        try:
            make_archive(archive_name, 'zip', root_dir)
            messages.info(request, f'The archive <<{archive_name.name}>> has been packaged...')
        except FileNotFoundError as err:
            messages.error(request, f'Archiving has failed => Error code: {err}')
    else:
        messages.error(f'Directory {root_dir} is empty...')


def get_archives(request):
    '''unpacking compressed in zip format archive file with fixtures'''
    args = (request, settings.FTP, settings.FTP_USER, settings.FTP_LOGIN)
    getFilefromFTP(*args)
    archive_path = pathlib.Path(r'backup_json/zip/wtr_archive.zip')
    archtmp_path = pathlib.Path(r'backup_json/temp/wtr_archive.zip')
    arch_dir = pathlib.Path(r'backup_json/zip')
    dest_path = pathlib.Path(r'backup_json/wtr_archive')

    if pathlib.Path.is_file(archive_path):
        try:
            if filecmp.cmp(archtmp_path, archive_path, shallow=False):
                messages.error(request, 'There are no new records in fixtures...')
            else:
                archive_path.unlink()
                copy2(archtmp_path, arch_dir)
                unpack_archive(archive_path, dest_path, 'zip')
                messages.info(request, 'The archive has been unpacked...')
                readfixture(request)
        except:
            raise ExecError
    else:
        copy2(archtmp_path, arch_dir)
        unpack_archive(archive_path, dest_path, 'zip')
        messages.info(request, 'The archive has been added and unpacked...')
        readfixture(request)


def uploadFileFTP(request, sourceFilePath:pathlib, destinationDirectory:pathlib, server:str, username:str, password:str):
    '''sending compressed in zip format archive file with fixtures on ftp server'''
    if check_internet_connection():
        try:
            with FTP(server, username, password) as myFTP:
                print('\nConnected to FTP...<<{}>>'.format(myFTP.host))
                ftpdirs = list(name for name in myFTP.nlst())
                if destinationDirectory not in ftpdirs:
                    print(f'\nDestination directory <<{destinationDirectory}>> does not exist...\nCreating a target catalog...')
                    try:
                        myFTP.mkd(destinationDirectory)
                        print(f'Destination directory <<{destinationDirectory}>> has been created...')
                        myFTP.cwd(destinationDirectory)
                        if pathlib.Path.is_file(sourceFilePath):
                            with open(sourceFilePath, 'rb') as fh:
                                myFTP.storbinary('STOR {}'.format(sourceFilePath.name), fh)
                                print(f'\nThe <<{sourceFilePath.name}>> file has been sent to the directory <<{destinationDirectory}>>\n')
                        else:
                            print('\nNo source file...')
                    except:
                        raise error_reply
                else:
                    try:
                        myFTP.cwd(destinationDirectory)
                        if pathlib.Path.is_file(sourceFilePath):
                            with open(sourceFilePath, 'rb') as fh:
                                myFTP.storbinary('STOR {}'.format(sourceFilePath.name), fh)
                                print(f'\nFile <<{sourceFilePath.name}>> was sent to the FTP directory <<{destinationDirectory}>>\n')
                    except:
                        raise error_reply
        except:
            raise ConnectionError
    else:
        messages.error(request, r'No internet connection...')


def getFilefromFTP(request, server:str, username:str, password:str):
    '''loading compressed in zip format archive file with fixtures on ftp server'''
    archfile = pathlib.Path(r'backup_json/temp/wtr_archive.zip')
    if check_internet_connection():
        try:
            with FTP(server, username, password) as myFTP:
                try:
                    if pathlib.Path.is_file(archfile):
                        archfile.unlink()
                    myFTP.cwd(r'/unikolor_db/')
                    size = myFTP.size(r'wtr_archive.zip')
                    print(size)
                    myFTP.retrbinary(f'RETR {archfile.name}', open(archfile, 'wb').write)
                    messages.info(request, f'\nArchive <<{archfile.name}>> successfully imported...')
                except:
                    messages.error(request, f'File <<{archfile.name}>> do not exist...')
        except ConnectionError as error:
            messages.error(request, f'Connection error: {error}')
    else:
        messages.error(request, r'No internet connection...')


# serialization json
def export_as_json(modeladmin, request, queryset):
    opts = modeladmin.model._meta
    path = pathlib.Path(f'backup_json/{opts.verbose_name}.json')
    with open(path, 'w') as file:
        serializers.serialize('json', queryset, indent=4, stream=file)
    messages.success(request, f'Rekordy zapisane do pliku {opts.verbose_name}')


# archiving of delete records
def archiving_of_deleted_records(worker):
    models = EmployeeData, EmployeeHourlyRate, WorkEvidence, EmployeeLeave, AccountPayment
    all_records = [worker]

    for model in models:
        all_records += list(model.objects.filter(worker=worker))

    path = pathlib.Path(f'backup_json/erase_worker/{worker.surname}_{worker.forename}.json')
    with open(path, 'w') as file:
        serializers.serialize('json', all_records, indent=4, stream=file)
