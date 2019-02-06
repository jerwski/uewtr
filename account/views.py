# standard library
import os
import socket
from pathlib import Path

# django library
from django.conf import settings
from django.shortcuts import render
from django.contrib import messages
from django.urls import reverse_lazy
from django.contrib.auth import logout
from django.http import HttpResponseRedirect
from django.views.generic import CreateView, View

# my models
from employee.models import Employee

# my forms
from account.forms import UserCreateForm

# my function
from functions.myfunctions import remgarbage
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

            if socket.gethostname() == 'HOMELAPTOP':
                args = (settings.FTP, settings.FTP_USER, settings.FTP_LOGIN, settings.ARCHIVE_FILE, settings.ROOT_BACKUP)
                getArchiveFilefromFTP(request, *args)

            elif socket.gethostname() == 'OFFICELAPTOP':
                context.__setitem__('zip2ftp', True)

            employee = Employee.objects.filter(status=True).first()

            if employee:
                employee_id = employee.id
                context.__setitem__('employee_id', employee_id)
            else:
                return render(request, '500.html', {'user': user})

            return render(request, 'account/admin.html', context)

        return HttpResponseRedirect(reverse_lazy('/login/'))


class Zip2Ftp(View):
    '''class that allows archiving the database of issued invoices'''
    def get(self, request)->HttpResponseRedirect:
        backup_file = Path(os.path.expanduser('~')).joinpath('Desktop/zip2ftp/invoices.zip')
        ftp_invoice_dir = r'Invoice_backup'
        args = (backup_file, ftp_invoice_dir, settings.FTP, settings.FTP_USER, settings.FTP_LOGIN)
        if socket.gethostname() == 'OFFICELAPTOP' and invoices_backup():
            uploadFileFTP(*args)
            messages.info(request, f'\nInvoices archive is safe...')

        return HttpResponseRedirect('account:admin_site')


def exit(request)->HttpResponseRedirect:
    '''backups features and exit from the application'''
    paths = (Path(r'templates/pdf'), Path(os.path.expanduser('~')).joinpath('Downloads'))
    args = (settings.ARCHIVE_FILE, settings.FTP_DIR, settings.FTP, settings.FTP_USER, settings.FTP_LOGIN)

    if check_internet_connection():
        try:
            if socket.gethostname() == 'OFFICELAPTOP':
                backup()
                mkfixture(settings.ROOT_BACKUP)
                make_archives(settings.ARCHIVE_NAME, settings.ROOT_BACKUP, settings.ARCHIVE_FILE)
                uploadFileFTP(*args)

            if request.user.is_authenticated:
                remgarbage(*paths)
                logout(request)

            return HttpResponseRedirect(r'https://www.google.pl/')
        except ConnectionError as error:
                print(f'Connection error... Error code: {error}')

    else:
        return render(request, '500.html', {'error': ConnectionError.__doc__})
