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

# my functions
from functions.archive import archiving_of_deleted_records
from functions.myfunctions import erase_records


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
            context.__setitem__('records',erase_records(employee_id,))
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
            active_worker = Employee.objects.filter(status=True).first()
            context.__setitem__('employee_id', active_worker.id)

        if form.is_valid():
            new_values = form.cleaned_data

            if new_values != old_values:
                try:
                    obj, created = Employee.objects.update_or_create(defaults=new_values, **old_values)
                    if created:
                        msg = f'Successful created basicdata for employee {obj}'
                        messages.success(request, msg)
                        kwargs = {'employee_id': obj.id}
                        return HttpResponseRedirect(reverse('employee:employee_extendeddata', kwargs=kwargs))
                    else:
                        msg = f'Successful update data for employee {obj}'
                        messages.success(request, msg)
                        return HttpResponseRedirect(reverse('employee:employee_basicdata', kwargs=kwargs))


                except Employee.DoesNotExist:
                    messages.warning(request, r'Somthing wrong... try again!')

            else:
                messages.info(request, r'Nothing to change!')
                return HttpResponseRedirect(reverse('employee:employee_basicdata', kwargs=kwargs))
        else:
            context.__setitem__('new_employee', True)
            return render(request, 'employee/employee_basicdata.html', context)


class EmployeeEraseAll(View):
    '''class implementing the method for ersing all data in database for the employee by pk=employee_id'''
    def get(self, request, employee_id:int):
        worker = Employee.objects.get(pk=employee_id)
        think_before_you_do = EmployeeData.objects.filter(worker=worker)
        if think_before_you_do.exists():
            archiving_of_deleted_records(worker)
            worker.delete()
            msg = f'You have been deleting all records in database for {worker}'
            messages.success(request, msg)
        else:
            messages.info(request, r'Nothing to delete!')
        return HttpResponseRedirect(reverse('employee:employee_basicdata'))


class EmployeeExtendedDataView(View):
    '''class implementing the method of adding/changing extended data for the employee by pk=employee_id'''
    def get(self, request, employee_id:int)->render:
        worker = Employee.objects.get(id=employee_id)
        employees = Employee.objects.filter(status=True)

        if EmployeeData.objects.filter(worker=worker).exists():
            employee = EmployeeData.objects.get(worker=worker)
            fields = list(employee.__dict__.keys())[2:]
            old_values = EmployeeData.objects.filter(worker=worker).values(*fields)[0]
            old_values['worker'] = old_values.pop('worker_id')
            old_values['worker'] = worker
            form = EmployeeExtendedDataForm(initial=old_values)
        else:
            form = EmployeeExtendedDataForm(initial={'worker': worker})

        context = {'form': form, 'employee_id': employee_id, 'employees': employees, 'employee': worker}

        return render(request, 'employee/employee_extendeddata.html', context)

    def post(self, request, employee_id:int)->HttpResponseRedirect:
        form = EmployeeExtendedDataForm(data=request.POST)
        kwargs = {'employee_id': employee_id}
        worker = Employee.objects.get(id=employee_id)
        employees = Employee.objects.filter(status=True)
        old_values = {'worker': worker}

        context = {'form': form, 'employee_id': employee_id, 'employees': employees, 'employee': worker}

        if EmployeeData.objects.filter(worker=worker).exists():
            employee_extendeddata = EmployeeData.objects.get(worker=worker)
            fields = list(employee_extendeddata.__dict__.keys())[2:]
            old_values.update(EmployeeData.objects.filter(worker=worker).values(*fields)[0])
            old_values.pop('worker_id')
            val=old_values['overtime']
            old_values['overtime']=str(val)

        if form.is_valid():
            new_values = form.cleaned_data

            if new_values != old_values:

                try:
                    obj, created = EmployeeData.objects.update_or_create(**old_values, defaults=new_values)
                    if created:
                        worker = Employee.objects.get(pk=obj.worker_id)
                        EmployeeHourlyRate.objects.create(worker=worker, update=date.today(), hourly_rate=8.00)
                        msg = f'Successful created data for employee {obj} with minimum rate 8.00 PLN/h'
                        messages.success(request, msg)
                        return HttpResponseRedirect(reverse('employee:employee_hourly_rate', kwargs=kwargs))
                    else:
                        msg = f'Successful update data for employee {obj}'
                        messages.success(request, msg)
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
        all_hourly_rate = EmployeeHourlyRate.objects.filter(worker=employee)
        last_hourly_rate = all_hourly_rate.last()
        form = EmployeeHourlyRateForm()
        context = {'employee_id': employee_id, 'employee': employee, 'employees': employees,
                   'last_hourly_rate': last_hourly_rate, 'all_hourly_rate': all_hourly_rate, 'form': form}
        return render(request, 'employee/employee_hourly_rate.html', context)

    def post(self, request, employee_id:int)->render:
        employee = Employee.objects.get(pk=employee_id)
        employees = Employee.objects.filter(status=True)
        values = {'worker': employee, 'update__year': date.today().year, 'update__month': date.today().month}
        form = EmployeeHourlyRateForm(data=request.POST)
        context = {'form': form, 'employee_id': employee_id,
                   'employee': employee, 'employees': employees, 'update': date.today()}

        if form.is_valid():
            data = form.cleaned_data

            if EmployeeHourlyRate.objects.filter(**values).exclude(update__exact=date.today()).exists():
                msg = f'Rate for employee ({employee}) is existing in database...'
                messages.error(request, msg)
                context.__setitem__('check_rate', True)

            else:
                defaults = {'hourly_rate': data['hourly_rate']}
                kwargs = {'worker_id': employee.id, 'update': date.today()}
                obj, created = EmployeeHourlyRate.objects.update_or_create(defaults=defaults, **kwargs)
                context.__setitem__('hourly_rate', obj.hourly_rate)

                if created:
                    msg = f'For employee ({employee}) add new hourly rate ({obj.hourly_rate} PLN)'
                    messages.success(request, msg)
                else:
                    msg = f'For employee ({employee}) update hourly rate ({obj.hourly_rate} PLN)'
                    messages.success(request, msg)

        return render(request, 'employee/employee_hourly_rate.html', context)


class EmployeeHourlyRateEraseView(View):
    '''class implementing the method of deleting the new hourly rate entered for the employee by pk=employee_id'''
    def get(self, request, employee_id:int)->HttpResponseRedirect:
        kwargs = {'employee_id': employee_id}
        employee = Employee.objects.get(id=employee_id)
        check = EmployeeHourlyRate.objects.filter(worker=employee, update__exact=date.today())
        if check.exists():
            check.delete()
            msg = f'Succesful erase last record for {employee}'
            messages.success(request, msg)
            if not EmployeeHourlyRate.objects.filter(worker=employee).exists():
                EmployeeHourlyRate.objects.create(worker=employee, update=date.today(), hourly_rate=8.00)
                msg = f'Set minimum hourly rate for {employee}'
                messages.success(request, msg)
        else:
            messages.info(request, r'Nothing to erase...')

        return HttpResponseRedirect(reverse('employee:employee_hourly_rate', kwargs=kwargs))

