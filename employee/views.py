# standard library
from datetime import date

# django core
from django.urls import reverse
from django.contrib import messages
from django.views.generic import View
from django.shortcuts import render, HttpResponseRedirect

# my models
from employee.models import Employee, EmployeeData, EmployeeHourlyRate

# my forms
from employee.forms import EmployeeBasicDataForm, EmployeeExtendedDataForm, EmployeeHourlyRateForm


# Create your views here.


class EmployeeBasicDataView(View):
    '''class implementing the method of adding/changing basic data for the new or existing employee'''
    def get(self, request, employee_id:int=None)->render:
        context = dict()
        employees = Employee.objects.all()
        if employees.exists():
            context.__setitem__('employees_st', employees.filter(status=True))
            context.__setitem__('employees_sf', employees.filter(status=False))
        else:
            messages.success(request, r'No employee in database...')

        if employee_id:
            employee = Employee.objects.get(pk=employee_id)
            fields = list(employee.__dict__.keys())[2:]
            initial = Employee.objects.filter(pk=employee_id).values(*fields)[0]
            form = EmployeeBasicDataForm(initial=initial)
            context.__setitem__('form', form)
            context.__setitem__('employee', employee)
            context.__setitem__('employee_id', employee_id)
            return render(request, 'employee/employee_basicdata.html', context)
        else:
            form = EmployeeBasicDataForm()
            context.__setitem__('form',form)
            active_worker = Employee.objects.filter(status=True).first()
            context.__setitem__('new_employee', True)
            context.__setitem__('employee_id', active_worker.id)
            return render(request, 'employee/employee_basicdata.html', context)

    def post(self, request, employee_id:int=None)->HttpResponseRedirect:
        form = EmployeeBasicDataForm(data=request.POST)
        context = {'form': form}
        employees = Employee.objects.all()
        if employees.exists():
            context.__setitem__('employees_st', employees.filter(status=True))
            context.__setitem__('employees_sf', employees.filter(status=False))
        else:
            messages.success(request, r'No employee in database...')

        if employee_id:
            kwargs = {'employee_id': employee_id}
            employee = Employee.objects.get(pk=employee_id)
            fields = list(employee.__dict__.keys())[2:]
            old_values = Employee.objects.filter(pk=employee_id).values(*fields)[0]
        else:
            kwargs = {}
            old_values = {'pesel': request.POST['pesel']}

        if form.is_valid():
            new_values = form.cleaned_data

            if new_values != old_values:
                try:
                    obj, created = Employee.objects.update_or_create(defaults=new_values, **old_values)
                    if created:
                        msg = r'Successful created basicdata for employee {}'
                        messages.success(request, msg.format(obj))
                        kwargs = {'employee_id': obj.id}
                        return HttpResponseRedirect(reverse('employee:employee_extendeddata', kwargs=kwargs))
                    else:
                        msg = r'Successful update data for employee {}'
                        messages.success(request, msg.format(obj))
                        return HttpResponseRedirect(reverse('employee:employee_basicdata', kwargs=kwargs))


                except Employee.DoesNotExist:
                    messages.warning(request, r'Somthing wrong... try again!')

            else:
                messages.info(request, r'Nothing to change!')
                return HttpResponseRedirect(reverse('employee:employee_basicdata', kwargs=kwargs))
        else:
            return render(request, 'employee/employee_basicdata.html', context)


class EmployeeExtendedDataView(View):
    '''class implementing the method of adding/changing extended data for the employee by pk=employee_id'''
    def get(self, request, employee_id:int)->render:
        name = Employee.objects.get(id=employee_id)
        employees = Employee.objects.filter(status=True)

        if EmployeeData.objects.filter(name=name).exists():
            employee = EmployeeData.objects.get(name=name)
            fields = list(employee.__dict__.keys())[2:]
            old_values = EmployeeData.objects.filter(name=name).values(*fields)[0]
            old_values['name'] = old_values.pop('name_id')
            old_values['name'] = name
            form = EmployeeExtendedDataForm(initial=old_values)
        else:
            form = EmployeeExtendedDataForm(initial={'name': name})

        context = {'form': form, 'employee_id': employee_id, 'employees': employees, 'employee': name}

        return render(request, 'employee/employee_extendeddata.html', context)

    def post(self, request, employee_id:int)->HttpResponseRedirect:
        kwargs = {'employee_id': employee_id}
        old_values = {'name_id': employee_id}
        employee = Employee.objects.get(id=employee_id)
        employees = Employee.objects.filter(status=True)
        form = EmployeeExtendedDataForm(data=request.POST)
        context = {'form': form, 'employee_id': employee_id, 'employees': employees, 'employee': employee}

        if EmployeeData.objects.filter(**old_values).exists():
            employee_extendeddata = EmployeeData.objects.get(name_id=employee_id)
            fields = list(employee_extendeddata.__dict__.keys())[2:]
            old_values = EmployeeData.objects.filter(**old_values).values(*fields)[0]
            old_values['name'] = old_values.pop('name_id')
            old_values['name'] = employee

        if form.is_valid():
            new_values = form.cleaned_data

            if new_values != old_values:

                try:
                    obj, created = EmployeeData.objects.update_or_create(**old_values, defaults=new_values)
                    if created:
                        msg = r'Successful created data for employee {}'
                        messages.success(request, msg.format(obj))
                        return HttpResponseRedirect(reverse('employee:employee_hourly_rate', kwargs=kwargs))
                    else:
                        msg = r'Successful update data for employee {}'
                        messages.success(request, msg.format(obj))
                        return HttpResponseRedirect(reverse('employee:employee_basicdata', kwargs=kwargs))


                except Employee.DoesNotExist:
                    messages.warning(request, r'Somthing wrong... try again!')

            else:
                messages.info(request, r'Nothing to change!')
                return HttpResponseRedirect(reverse('employee:employee_extendeddata', kwargs={'employee_id': employee_id}))
        else:
            return render(request, 'employee/employee_extendeddata.html', context)


class EmployeeHourlyRateView(View):
    '''class implementing the method of changing the hourly rate for the employee by pk=employee_id'''
    def get(self, request, employee_id:int)->render:
        employee = Employee.objects.get(pk=employee_id)
        employees = Employee.objects.filter(status=True)
        all_hourly_rate = EmployeeHourlyRate.objects.filter(name=employee)
        last_hourly_rate = all_hourly_rate.last()
        form = EmployeeHourlyRateForm()
        context = {'employee_id': employee_id, 'employee': employee, 'employees': employees,
                   'last_hourly_rate': last_hourly_rate, 'all_hourly_rate': all_hourly_rate, 'form': form}
        return render(request, 'employee/employee_hourly_rate.html', context)

    def post(self, request, employee_id:int)->render:
        employee = Employee.objects.get(pk=employee_id)
        employees = Employee.objects.filter(status=True)
        values = {'name': employee, 'update__year': date.today().year, 'update__month': date.today().month}
        form = EmployeeHourlyRateForm(data=request.POST)
        context = {'form': form, 'employee_id': employee_id,
                   'employee': employee, 'employees': employees, 'update': date.today()}

        if form.is_valid():
            data = form.cleaned_data

            if EmployeeHourlyRate.objects.filter(**values).exclude(update__exact=date.today()).exists():
                msg = r'Rate for employee ({}) is existing in database...'
                messages.error(request, msg.format(employee))
                context.__setitem__('check_rate', True)

            else:
                defaults = {'hourly_rate': data['hourly_rate']}
                kwargs = {'name_id': employee.id, 'update': date.today()}
                obj, created = EmployeeHourlyRate.objects.update_or_create(defaults=defaults, **kwargs)
                context.__setitem__('hourly_rate', obj.hourly_rate)

                if created:
                    msg = r'For employee ({}) add new hourly rate ({} PLN)'
                    messages.success(request, msg.format(employee, obj.hourly_rate))
                else:
                    msg = r'For employee ({}) update hourly rate ({} PLN)'
                    messages.success(request, msg.format(employee, obj.hourly_rate))

        return render(request, 'employee/employee_hourly_rate.html', context)


class EmployeeHourlyRateEraseView(View):
    '''class implementing the method of deleting the new hourly rate entered for the employee by pk=employee_id'''
    def get(self, request, employee_id:int)->HttpResponseRedirect:
        kwargs = {'employee_id': employee_id}
        employee = Employee.objects.get(id=employee_id)
        check = EmployeeHourlyRate.objects.filter(name=employee, update__exact=date.today())
        if check.exists():
            check.delete()
            msg = r'Succesful erase last record for {}'
            messages.success(request, msg.format(employee))
        else:
            messages.info(request, r'Nothing to erase...')

        return HttpResponseRedirect(reverse('employee:employee_hourly_rate', kwargs=kwargs))
