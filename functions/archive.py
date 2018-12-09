# standard library
import filecmp
import pathlib
from ftplib import FTP, error_reply
from shutil import make_archive, unpack_archive, copy2, ExecError

# django core
from django.conf import settings
from django.core.management import call_command


def backup():
    '''total backup of data base'''
    path = pathlib.Path(r'backup_json/db.json')
    try:
        with open(path, 'w') as jsonfile:
            call_command('dumpdata', indent=4, stdout=jsonfile)
    except FileNotFoundError as err:
        print('\nSomething wrong... Error: {}'.format(err))


def mkfixture():
    '''create fixtures in json format'''
    for model, path in settings.FIXTURE_DIRS.items():
        try:
            with open(path, 'w') as jsonfile:
                call_command('dumpdata', model, indent=4, stdout=jsonfile)
        except FileNotFoundError as err:
            print('\nSerialization error: {}'.format(err))


def readfixture():
    '''reading fixtures'''
    for model, path in settings.FIXTURE_DIRS.items():
        try:
            call_command('loaddata', path)
            print('Base {} has been updated...\n'.format(model.split('.')[1]))
        except FileNotFoundError as err:
            print('\nNo data => Error code: {}'.format(err))



def make_archives():
    '''create compressed in zip format archive file with fixtures'''
    archive_name = pathlib.Path(r'backup_json/zip/wtr_archive')
    root_dir = pathlib.Path(r'backup_json/wtr_archive')
    if list(pathlib.Path.iterdir(root_dir)):
        try:
            make_archive(archive_name, 'zip', root_dir)
            print('\nThe archive has been packaged...')
        except FileNotFoundError as err:
            print('\nArchiving has failed => Error code:'.format(err))
    else:
        print('\nDirectory {} is empty...'.format(root_dir))


def get_archives():
    '''unpacking compressed in zip format archive file with fixtures'''
    args = (settings.FTP, settings.FTP_USER, settings.FTP_LOGIN)
    getFilefromFTP(*args)
    archive_path = pathlib.Path(r'backup_json/zip/wtr_archive.zip')
    archtmp_path = pathlib.Path(r'backup_json/temp/wtr_archive.zip')
    arch_dir = pathlib.Path(r'backup_json/zip')
    dest_path = pathlib.Path(r'backup_json/wtr_archive')

    if pathlib.Path.is_file(archive_path):
        try:
            if filecmp.cmp(archtmp_path, archive_path, shallow=False):
                print('\nThere are no new records in fixtures...\n')
            else:
                archive_path.unlink()
                copy2(archtmp_path, arch_dir)
                unpack_archive(archive_path, dest_path, 'zip')
                print('The archive has been unpacked...\n')
                readfixture()
        except ExecError as err:
            print('\nThe archive has not been unpacked => Error code: {}'.format(err))
    else:
        copy2(archtmp_path, arch_dir)
        unpack_archive(archive_path, dest_path, 'zip')
        print('The archive has been added and unpacked...\n')
        readfixture()


def uploadFileFTP(sourceFilePath:pathlib, destinationDirectory:pathlib, server:str, username:str, password:str):
    '''sending compressed in zip format archive file with fixtures on ftp server'''
    try:
        with FTP(server, username, password) as myFTP:
            print('\nConnected to FTP...<<{}>>'.format(myFTP.host))
            ftpdirs = list(name for name in myFTP.nlst())
            if destinationDirectory not in ftpdirs:
                print('\nDestination directory <<{}>> does not exist...\nCreating a target catalog...'.format(destinationDirectory))
                try:
                    myFTP.mkd(destinationDirectory)
                    print('Destination directory <<{}>> has been created...'.format(destinationDirectory))
                    myFTP.cwd(destinationDirectory)
                    if pathlib.Path.is_file(sourceFilePath):
                        with open(sourceFilePath, 'rb') as fh:
                            myFTP.storbinary('STOR {}'.format(sourceFilePath.name), fh)
                            print('\nThe <<{}>> file has been sent to the directory <<{}>>\n'.format(sourceFilePath.name,destinationDirectory))
                    else:
                        print('\nNo source file...')

                except error_reply as err:
                    print('\nServer is not responding => Error code: {}'.format(err))

            else:
                try:
                    myFTP.cwd(destinationDirectory)
                    if pathlib.Path.is_file(sourceFilePath):
                        with open(sourceFilePath, 'rb') as fh:
                            myFTP.storbinary('STOR {}'.format(sourceFilePath.name), fh)
                            print('\nFile <<{}>> was sent to the FTP directory <<{}>>\n'.format(sourceFilePath.name, destinationDirectory))
                except error_reply as err:
                    print('\nServer is not responding => Error code: {}'.format(err))

    except ConnectionError as ce:
        print('No connection to FTP => Error code: {}'.format(ce))


def getFilefromFTP(server:str, username:str, password:str):
    '''loading compressed in zip format archive file with fixtures on ftp server'''
    archfile = pathlib.Path(r'backup_json/temp/wtr_archive.zip')

    try:
        with FTP(server, username, password) as myFTP:
            try:
                if pathlib.Path.is_file(archfile):
                    archfile.unlink()
                myFTP.cwd(r'/unikolor_db/')
                myFTP.retrbinary('RETR {}'.format(archfile.name), open(archfile, 'wb').write)
                print('\nArchive <<{}>> successfully imported...'.format(archfile.name))

            except error_reply as err:
                print('\nServer is not responding => Error code: {}'.format(err))

    except ConnectionError as ce:
        print('No connection to FTP => Error code: {}'.format(ce))
