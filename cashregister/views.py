# standard library
import num2words

# django library
from django.db.models import Q
from django.urls import reverse
from django.shortcuts import render
from django.contrib import messages
from django.utils.timezone import now
from django.views.generic import View
from django.http import HttpResponse, HttpResponseRedirect

# pdfkit library
import pdfkit

# my functions
from functions.myfunctions import cashregisterdata, cashregisterhtml2pdf, sendCashRegister

# my models
from cashregister.models import Company, CashRegister

# my forms
from cashregister.forms import CompanyAddForm, CashRegisterForm


# Create your views here.


class CompanyAddView(View):
    '''class implementing the method of adding/changing basic data for the new or existing company'''
    def get(self, request, company_id:int=None)->render:
        companies = Company.objects.filter(status__range=[1,3]).order_by('company')
        if company_id:
            company = Company.objects.get(pk=company_id)
            fields = list(company.__dict__.keys())[2:-2]
            initial = Company.objects.filter(pk=company_id).values(*fields)[0]
            form = CompanyAddForm(initial=initial)
            context = {'form': form, 'company_id': company_id, 'companies': companies,}

        else:
            form = CompanyAddForm()
            context = {'form': form, 'companies': companies,}

        return render(request, 'cashregister/company_add.html', context)

    def post(self, request, company_id:int=None)->HttpResponseRedirect:
        companies = Company.objects.all().order_by('company')
        form = CompanyAddForm(data=request.POST)
        context = {'form': form, 'companies': companies,}

        if company_id:
            employee = Company.objects.get(pk=company_id)
            fields = list(employee.__dict__.keys())[2:-2]
            old_values = Company.objects.filter(pk=company_id).values(*fields)[0]
        else:
            old_values = {'nip': request.POST['nip']}

        if form.is_valid():
            new_values = form.cleaned_data

            if new_values != old_values:
                try:
                    obj, created = Company.objects.update_or_create(defaults=new_values, **old_values)

                    if created:
                        msg = f'Successful created new company {obj}'
                        messages.success(request, msg)
                    else:
                        msg = f'Successful update data for company {obj}'
                        messages.success(request, msg)

                    kwargs = {'company_id': obj.id}
                    return HttpResponseRedirect(reverse('cashregister:change_company', kwargs=kwargs))

                except Company.DoesNotExist:
                    messages.warning(request, r'Somthing wrong... try again!')

            else:
                kwargs = {'company_id': company_id}
                messages.info(request, r'Nothing to change!')
                return HttpResponseRedirect(reverse('cashregister:change_company', kwargs=kwargs))
        else:
            return render(request, 'cashregister/company_add.html', context)


class CashRegisterView(View):
    '''class implementing the method of adding records to the Cash Register'''
    def get(self, request, company_id:int=None)->HttpResponseRedirect:
        check = CashRegister.objects.filter(company_id=company_id)
        companies = Company.objects.filter(status__range=[1,3]).order_by('company')
        context = {'companies': companies}

        if company_id:
            month, year = now().month, now().year
            company = Company.objects.get(pk=company_id)
            registerdata = cashregisterdata(company_id, month, year)
            context.update(dict(registerdata))
            records = check.filter(created__month=month, created__year=year).exclude(contents='Z przeniesienia')
            form = CashRegisterForm(initial={'company': company})
            context.update({'form': form, 'company': company, 'company_id': company_id, 'records': records.order_by('-created')})

            if now().month==1:
                month, year = 12, now().year - 1
            else:
                month, year = now().month - 1, now().year

            previous = check.filter(created__month=month, created__year=year)

            if previous:
                context.__setitem__('previous', True)
            else:
                context.__setitem__('previous', False)

        return render(request, 'cashregister/cashregister.html', context)

    def post(self, request, company_id:int=None)->HttpResponseRedirect:
        form = CashRegisterForm(data=request.POST)
        check = CashRegister.objects.filter(company_id=company_id)
        companies = Company.objects.filter(status__range=[1,3]).order_by('company')
        context = {'form': form, 'companies': companies}

        if company_id:
            kwargs = {'company_id': company_id}
            month, year = now().month, now().year
            company = Company.objects.get(pk=company_id)
            registerdata = cashregisterdata(company_id, month, year)
            context.update(dict(registerdata))
            records = check.filter(created__month=month, created__year=year).exclude(contents='Z przeniesienia')
            context.update({'company': company, 'company_id': company_id, 'records': records.order_by('-created')})

            if now().month==1:
                month, year = 12, now().year - 1
            else:
                month, year = now().month - 1, now().year

            previous = check.filter(created__month=month, created__year=year)

            if previous:
                context.__setitem__('previous', True)
            else:
                context.__setitem__('previous', False)

            if form.is_valid():
                form.save(commit=False)
                data = form.cleaned_data
                income, expenditure = [data[key] for key in ('income', 'expenditure')]
                if income > 0 and expenditure > 0:
                    msg = f'One of the fields (income {income:.2f}PLN or expenditure {expenditure:.2f}PLN)  must be zero!'
                    messages.warning(request, msg)
                    return render(request, 'cashregister/cashregister.html', context)
                elif income or expenditure:
                    form.save(commit=True)
                    if income > 0:
                        msg = f'Succesful register new record in {company} (income={income:.2f}PLN)'
                        messages.success(request, msg)
                    elif expenditure > 0:
                        msg = f'Succesful register new record in {company} (expenditure={expenditure:.2f}PLN)'
                        messages.success(request, msg)

                    return HttpResponseRedirect(reverse('cashregister:cash_register', kwargs=kwargs))


class CashRegisterPrintView(View):
    '''class representing the view of monthly cash register print'''
    def get(self, request, company_id:int)->HttpResponse:
        '''convert html cashregister_pdf for each companies to pdf'''
        # TODO: create KP KW as get_absolute_url
        if now().month==1:
            month, year = 12, now().year - 1
        else:
            month, year = now().month - 1, now().year

        html = cashregisterhtml2pdf(company_id, month, year)

        if html:
            # create pdf file as attachment
            options = {'page-size': 'A4', 'margin-top': '0.4in', 'margin-right': '0.4in',
                       'margin-bottom': '0.4in', 'margin-left': '0.8in', 'encoding': "UTF-8",
                       'orientation': 'portrait','no-outline': None, 'quiet': '', }

            pdf = pdfkit.from_string(html, False, options=options)
            filename = f'cashregister_{company_id}_{year}_{month}.pdf'

            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="' + filename + '"'
            return response
        else:
            messages.warning(request, r'Nothing to print...')
            kwargs = {'company_id': company_id}

            return HttpResponseRedirect(reverse('cashregister:cash_register', kwargs=kwargs))


class CashRegisterSendView(View):
    '''class representing the view for sending cash register as pdf file'''
    def get(self, request, company_id:int)->HttpResponseRedirect:
        kwargs = {'company_id': company_id}
        company = Company.objects.get(pk=company_id)

        if now().month==1:
            month, year = 12, now().year - 1
        else:
            month, year = now().month - 1, now().year

        html = cashregisterhtml2pdf(company_id, month, year)

        if html:
            # create pdf file and save on templates/pdf/cashregister_{company}_{month}_{year}.pdf
            options = {'page-size': 'A4', 'margin-top': '0.4in', 'margin-right': '0.4in',
                       'margin-bottom': '0.4in', 'margin-left': '0.8in', 'encoding': "UTF-8",
                       'orientation': 'portrait','no-outline': None, 'quiet': '', }
            # create pdf file
            pdfile = f'templates/pdf/cashregister_{company}_{month}_{year}.pdf'
            pdfkit.from_string(html, pdfile, options=options)
            # send e-mail with attached pdfile
            sendCashRegister(company_id, month, year)
            messages.info(request, f'Cash register for {company} on {month}/{year} was sending....')
        else:
            messages.warning(request, r'Nothing to send...')

        return HttpResponseRedirect(reverse('cashregister:cash_register', kwargs=kwargs))


class CashRegisterAccept(View):

    def get(self, request, record:int)->HttpResponseRedirect:
        data = CashRegister.objects.get(pk=record)
        check = Q(company_id=3, created__month=data.created.month, created__year=data.created.year, created__lte=data.created)
        number = CashRegister.objects.filter(check).exclude(contents='Z przeniesienia')
        number = len(number)
        if data.income:
            value = f'Income: {data.income}'
            numword = num2words.num2words (data.income, lang='pl', to='currency', currency='PLN')
            msg = f'You call CashRegisterAccept class...record={record}, Income={data.income}, Number={number}'
        else:
            value = f'Expenditure: {data.expenditure}'
            numword=num2words.num2words (data.expenditure, lang='pl', to='currency', currency='PLN')
            msg = f'You call CashRegisterAccept class...record={record}, Expenditure={data.expenditure}, Number={number}'
        print(f'Company; {data.company}\nCreted: {data.created}\nContents: {data.contents}\n{value}')
        print(numword)
        messages.warning(request, msg)
        return HttpResponseRedirect(reverse('cashregister:cash_register'))
