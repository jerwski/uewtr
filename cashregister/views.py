# django library
from django.urls import reverse
from django.shortcuts import render
from django.contrib import messages
from django.utils.timezone import now
from django.views.generic import View
from django.http import HttpResponseRedirect

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
        companies = Company.objects.filter(status__range=[1,3]).order_by('company')
        context = {'companies': companies}

        if company_id:
            month, year = now().month, now().year
            company = Company.objects.get(pk=company_id)
            records = CashRegister.objects.filter(company_id=company_id, date__month=month, date__year=year).order_by('date')
            form = CashRegisterForm(initial={'company': company})
            context.update({'form': form, 'company': company, 'company_id': company_id, 'records': records})

        return render(request, 'cashregister/cashregister.html', context)

    def post(self, request, company_id:int=None)->HttpResponseRedirect:
        form = CashRegisterForm(data=request.POST)
        companies = Company.objects.filter(status__range=[1,3]).order_by('company')
        context = {'form': form, 'companies': companies}

        if company_id:
            kwargs = {'company_id': company_id}
            month, year = now().month, now().year
            company = Company.objects.get(pk=company_id)
            records = CashRegister.objects.filter(company_id=company_id, date__month=month, date__year=year)
            context.update({'company': company, 'company_id': company_id,  'records': records.order_by('date')})

            if form.is_valid():
                form.save(commit=False)
                data = form.cleaned_data
                symbol, contents, income, expenditure = [data[key] for key in ('symbol', 'contents', 'income', 'expenditure')]
                if income > 0 or expenditure > 0:
                    form.save(commit=True)
                    msg = f'Succesful register new record in {company} Cash Register...'
                    messages.success(request, msg)

                return HttpResponseRedirect(reverse('cashregister:cash_register', kwargs=kwargs))

        return render(request, 'cashregister/cashregister.html', context)
