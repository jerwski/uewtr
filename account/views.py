# standard library
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
from functions.archive import mkfixture, make_archives, uploadFileFTP, backup, getArchiveFilefromFTP, check_internet_connection


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
            if socket.gethostname() == 'HOMELAPTOP':
                getArchiveFilefromFTP(request, settings.FTP, settings.FTP_USER, settings.FTP_LOGIN)
            employee = Employee.objects.filter(status=True).first()
            if employee:
                employee_id = employee.id
            else:
                return render(request, '500.html', {'user': user})

            return render(request, 'account/admin.html', {'user': user, 'employee_id': employee_id})
        else:
            messages.warning(request, f'User ({request.user.username}) has not permission to the dashboard...')
            return HttpResponseRedirect('/login/')




def exit(request)->HttpResponseRedirect:
    '''backups features and exit from the application'''
    pdfdir = Path(r'templates/pdf')
    downloads = Path(r'C:/Users/kopia/Downloads')

    if check_internet_connection():

        if socket.gethostname() == 'OFFICELAPTOP':
            try:
                backup()
                mkfixture()
                make_archives()
                args = (settings.ARCHIVE_FILE, settings.FTP_DIR, settings.FTP, settings.FTP_USER, settings.FTP_LOGIN)
                uploadFileFTP(*args)

            except ConnectionError as error:
                print(f'Connection error... Error code: {error}')

        if request.user.is_authenticated:
            for file in Path.iterdir(pdfdir):
                file.unlink()
            for file in Path.iterdir(downloads):
                if file.match('leaves_data_*.pdf'):
                    file.unlink()
                if file.match('payroll_*.pdf'):
                    file.unlink()
            logout(request)

        return HttpResponseRedirect(r'https://www.google.pl/')

    else:
        return render(request, '500.html', {'error': ConnectionError.filename})
