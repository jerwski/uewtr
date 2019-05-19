# django core
from django.urls import reverse
from django.contrib import messages
from django.views.generic import View
from django.utils.timezone import now
from django.shortcuts import render, HttpResponseRedirect

# my models
from employee.models import Employee, EmployeeData, EmployeeHourlyRate

# my forms
from employee.forms import EmployeeBasicDataForm, EmployeeExtendedDataForm, EmployeeHourlyRateForm

# my functions
from functions.myfunctions import erase_records
from functions.archive import archiving_of_deleted_records


# Create your views here.


class EmployeeBasicDataView(View):
	'''class implementing the method of adding/changing basic data for the new or existing employee'''
	def get(self, request, employee_id:int=None)->render:
		context = dict()
		employees = Employee.objects.all()

		if employees.exists():
			context.__setitem__('employees_st', employees.filter(status=True))
			context.__setitem__('employees_sf', employees.filter(status=False))
			context.__setitem__('employee_id', employees.first().id)

		else:
			messages.warning(request, r'No employee in database...')

		if employee_id:
			worker = Employee.objects.get(pk=employee_id)
			fields = list(worker.__dict__.keys())[4:]
			initial = Employee.objects.filter(pk=employee_id).values(*fields)[0]
			active = EmployeeData.objects.filter(worker=worker)

			if active:
				context.__setitem__('active', True)
			else:
				context.__setitem__('active', False)

			form = EmployeeBasicDataForm(initial=initial)
			context.__setitem__('form', form)
			context.__setitem__('worker', worker)
			context.__setitem__('status', worker.status)
			context.__setitem__('employee_id', employee_id)
			context.__setitem__('records',erase_records(employee_id,))

			return render(request, 'employee/employee_basicdata.html', context)

		else:
			form = EmployeeBasicDataForm()
			context.__setitem__('form',form)
			context.__setitem__('active', True)
			context.__setitem__('new_employee', True)

			return render(request, 'employee/employee_basicdata.html', context)

	def post(self, request, employee_id:int=None)->HttpResponseRedirect:
		args = [employee_id]
		form = EmployeeBasicDataForm(data=request.POST)
		context = {'form': form}
		employees = Employee.objects.all()

		if employees.exists():
			context.__setitem__('employees_st', employees.filter(status=True))
			context.__setitem__('employees_sf', employees.filter(status=False))
		else:
			messages.success(request, r'No employee in database...')

		if employee_id:
			employee = Employee.objects.get(pk=employee_id)
			fields = list(employee.__dict__.keys())[4:]
			old_values = Employee.objects.filter(pk=employee_id).values(*fields)[0]
		else:
			old_values = {'pesel': request.POST['pesel']}

		if form.is_valid():
			new_values = form.cleaned_data

			if new_values != old_values:
				try:
					obj, created = Employee.objects.update_or_create(defaults=new_values, **old_values)
					context.__setitem__('employee_id', obj.id)

					if created:
						args = [obj.id]
						EmployeeHourlyRate.objects.create(worker=obj, update=now().date(), hourly_rate=8.00)
						msg = f'Successful created basic data for employee {obj} with minimum rate 8.00 PLN/h'
						messages.success(request, msg)
					else:
						msg = f'Successful update data for employee {obj}'
						messages.success(request, msg)

				except Employee.DoesNotExist:
					messages.warning(request, r'Somthing wrong... try again!')

			else:
				messages.info(request, r'Nothing to change!')

			return HttpResponseRedirect(reverse('employee:employee_basicdata', args=args))
		else:
			context.__setitem__('new_employee', True)

		return render(request, 'employee/employee_basicdata.html', context)


class EmployeeEraseAll(View):
	'''class implementing the method for erasing all data in database for the employee by pk=employee_id'''
	def get(self, request, employee_id:int)->HttpResponseRedirect:
		worker = Employee.objects.get(pk=employee_id)

		if worker:
			archiving_of_deleted_records(employee_id)
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
			fields = list(employee.__dict__.keys())[4:]
			old_values = EmployeeData.objects.filter(worker=worker).values(*fields)[0]
			old_values.pop('worker_id')
			old_values['worker'] = worker
			form = EmployeeExtendedDataForm(initial=old_values)
		else:
			form = EmployeeExtendedDataForm(initial={'worker': worker})

		context = {'form': form, 'employee_id': employee_id, 'employees': employees, 'employee': worker}

		return render(request, 'employee/employee_extendeddata.html', context)

	def post(self, request, employee_id:int)->HttpResponseRedirect:
		form = EmployeeExtendedDataForm(data=request.POST)
		employees = Employee.objects.filter(status=True)
		context = {'form': form, 'employee_id': employee_id, 'employees': employees}

		if form.is_valid():
			new_values = form.cleaned_data
			worker = new_values['worker']
			context.__setitem__('employee', worker)
			old_values = {'worker': worker}

			if EmployeeData.objects.filter(worker=worker).exists():
				employee_extendeddata = EmployeeData.objects.get(worker=worker)
				fields = list(employee_extendeddata.__dict__.keys())[4:]
				old_values.update(EmployeeData.objects.filter(worker=worker).values(*fields)[0])
				old_values.pop('worker_id')
				old_values['overtime'] = str(old_values['overtime'])

			if new_values != old_values:
				try:
					obj, created = EmployeeData.objects.update_or_create(**old_values, defaults=new_values)

					if created:
						messages.success(request, f'Successful created extended data for employee {obj}')

					else:
						messages.success(request, f'Successful update data for employee {obj}')

				except Employee.DoesNotExist:
					messages.warning(request, r'Somthing wrong... try again!')

			else:
				messages.info(request, r'Nothing to change!')

			return HttpResponseRedirect(reverse('employee:employee_extendeddata', args=[employee_id]))

		else:
			return render(request, 'employee/employee_extendeddata.html', context)


class EmployeeHourlyRateView(View):
	'''class implementing the method of changing the hourly rate for the employee by pk=employee_id'''
	def get(self, request, employee_id:int)->render:
		worker = Employee.objects.get(pk=employee_id)
		employees = Employee.objects.filter(status=True)
		all_hourly_rate = EmployeeHourlyRate.objects.filter(worker=worker)
		last_hourly_rate = all_hourly_rate.last()
		initial={'worker': worker, 'hourly_rate': f'{last_hourly_rate.hourly_rate:.2f}'}
		form = EmployeeHourlyRateForm(initial=initial)
		context = {'employee_id': employee_id, 'worker': worker, 'employees': employees,
				   'last_hourly_rate': last_hourly_rate, 'all_hourly_rate': all_hourly_rate, 'form': form}
		return render(request, 'employee/employee_hourly_rate.html', context)

	def post(self, request, employee_id:int)->render:
		employees = Employee.objects.filter(status=True)
		form = EmployeeHourlyRateForm(data=request.POST)
		context = {'form': form, 'employee_id': employee_id, 'employees': employees, 'update': now().date()}

		if form.is_valid():
			data = form.cleaned_data
			worker = data['worker']
			context.__setitem__('worker', worker)
			values = {'worker': worker, 'update__year': now().year, 'update__month': now().month}

			if EmployeeHourlyRate.objects.filter(**values).exclude(update__exact=now().date()).exists():
				msg = f'Rate for employee ({worker}) is existing in database...'
				messages.error(request, msg)
				context.__setitem__('check_rate', True)
			else:
				all_hourly_rate = EmployeeHourlyRate.objects.filter(worker=worker)
				last_exist_hourly_rate = all_hourly_rate.last()

				if data['hourly_rate'] != last_exist_hourly_rate.hourly_rate:
					defaults = {'hourly_rate': data['hourly_rate']}
					kwargs = {'worker_id': employee_id, 'update': now().date()}
					obj, created = EmployeeHourlyRate.objects.update_or_create(defaults=defaults, **kwargs)
					context.__setitem__('hourly_rate', obj.hourly_rate)

					if created:
						msg = f'For employee ({worker}) add new hourly rate ({obj.hourly_rate} PLN)'
						messages.success(request, msg)
					else:
						msg = f'For employee {worker} update hourly rate ({obj.hourly_rate} PLN)'
						messages.success(request, msg)
				else:
					msg = f'Last hourly rate {last_exist_hourly_rate} for {worker} is the same like enterd.'
					messages.success(request, msg)
					context.__setitem__('last_exist_hourly_rate', last_exist_hourly_rate)

		return render(request, 'employee/employee_hourly_rate.html', context)


class EmployeeHourlyRateEraseView(View):
	'''class implementing the method of deleting the new hourly rate entered for the employee by pk=employee_id'''
	def get(self, request, employee_id:int)->HttpResponseRedirect:
		worker = Employee.objects.get(id=employee_id)
		check = EmployeeHourlyRate.objects.filter(worker=worker, update__exact=now().date())

		if check.exists():
			check.delete()
			msg = f'Succesful erase last record for {worker}'
			messages.success(request, msg)

			if not EmployeeHourlyRate.objects.filter(worker=worker).exists():
				EmployeeHourlyRate.objects.create(worker=worker, update=now().date(), hourly_rate=8.00)
				msg = f'Set minimum hourly rate for {worker}'
				messages.success(request, msg)
		else:
			messages.info(request, r'Nothing to erase...')

		return HttpResponseRedirect(reverse('employee:employee_hourly_rate', args=[employee_id]))

