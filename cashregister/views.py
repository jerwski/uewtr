# django library
from django.urls import reverse
from django.shortcuts import render
from django.contrib import messages
from django.views.generic import View
from django.http import HttpResponseRedirect

# my models
from cashregister.models import Company

# my forms
from cashregister.forms import CompanyAddForm


# Create your views here.


class CompanyAddView(View):

    def get(self, request, company_id:int=None)->render:
        companies = Company.objects.all().order_by('company')
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
