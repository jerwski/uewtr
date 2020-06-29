# django core
from django.urls import reverse
from django.contrib import messages
from django.views.generic import View
from django.utils.timezone import now
from django.shortcuts import render, HttpResponseRedirect, HttpResponsePermanentRedirect

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
	def setup(self, request, *args, **kwargs):
		super(EmployeeBasicDataView, self).setup(request, **kwargs)
		self.request, self.kwargs, self.context, employee_id = request, kwargs, dict(), None
		employees = Employee.objects.all()

		if 'employee_id' in self.kwargs.keys():
			employee_id = self.kwargs['employee_id']
			worker = Employee.objects.get(pk=employee_id)
			fields = list(worker.__dict__.keys())[4:]
			initial = Employee.objects.filter(pk=employee_id).values(*fields)[0]
			self.context = {'employee_id': employee_id, 'worker': worker, 'records': erase_records(employee_id)}
			extdata = EmployeeData.objects.filter(worker=worker)

			if extdata:
				self.context.__setitem__('extdata', True)
			else:
				self.context.__setitem__('extdata', False)

		if employees.exists():
			employees_st = employees.filter(status=True)
			employees_sf = employees.filter(status=False)
			self.context.update({'employees_st': employees_st, 'employees_sf': employees_sf})

		else:
			messages.warning(request, r'No employee in database...')

		if self.request.method == 'GET':
			if employee_id:
				self.form = EmployeeBasicDataForm(initial=initial)

			else:
				self.form = EmployeeBasicDataForm(initial={'status': 0})
				self.context.update({'extdata': False, 'new_employee': True})

		elif self.request.method == 'POST':
			self.form = EmployeeBasicDataForm(data=self.request.POST)
			if employee_id:
				self.old_values = Employee.objects.filter(pk=employee_id).values(*fields)[0]
			else:
				self.old_values = {'pesel': request.POST['pesel']}

		self.context.update({'form': self.form})


	def get(self, request, **kwargs)->render:

		return render(request, 'employee/employee_basicdata.html', self.context)


	def post(self, request, **kwargs)->HttpResponseRedirect:

		if self.form.is_valid():
			new_values = self.form.cleaned_data
			new_values.update({'status': int(new_values['status']), 'leave': int(new_values['leave'])})

			if new_values != self.old_values:
				try:
					obj, created = Employee.objects.update_or_create(defaults=new_values, **self.old_values)
					self.context.update({'employee_id': obj.id})

					if created:
						EmployeeHourlyRate.objects.create(worker=obj, update=now().date(), hourly_rate=8.00)
						msg = f'Successful created basic data for employee {obj} with minimum rate 8.00 PLN/h'
						messages.success(request, msg)

						return HttpResponseRedirect(reverse('employee:employee_extendeddata', args=[obj.id]))

					else:
						msg = f'Successful update data for employee {obj}'
						messages.success(request, msg)

						return HttpResponseRedirect(reverse('employee:employee_basicdata', args=[obj.id]))

				except Employee.DoesNotExist:
					messages.warning(request, r'Somthing wrong... try again!')

			else:
				messages.info(request, r'Nothing to change!')

			return render(request, 'employee/employee_basicdata.html', self.context)
		else:
			self.context.__setitem__('new_employee', True)

		return render(request, 'employee/employee_basicdata.html', self.context)


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
	def setup(self, request, *args, **kwargs):
		super(EmployeeExtendedDataView, self).setup(request, **kwargs)
		self.request, self.kwargs = request, kwargs
		self.employee_id = self.kwargs['employee_id']
		self.worker = Employee.objects.get(id=self.employee_id)
		employees = Employee.objects.filter(status=True)
		self.extdata = EmployeeData.objects.filter(worker=self.worker)

		if self.extdata.exists():
			emplexdata = EmployeeData.objects.get(worker=self.worker)
			self.fields = list(emplexdata.__dict__.keys())[4:]

		self.context = {'employee_id': self.employee_id, 'employees': employees, 'worker': self.worker}

		if self.request.method == 'GET':
			if self.extdata.exists():
				old_values = self.extdata.values(*self.fields)[0]
				old_values.pop('worker_id')
				old_values['worker'] = self.worker
				self.form = EmployeeExtendedDataForm(initial=old_values)
			else:
				self.form = EmployeeExtendedDataForm(initial={'worker': self.worker})

		elif self.request.method == 'POST':
			self.form = EmployeeExtendedDataForm(data=self.request.POST)

		self.context.update({'form': self.form})


	def get(self, request, **kwargs)->render:

		return render(request, 'employee/employee_extendeddata.html', self.context)


	def post(self, request, **kwargs)->HttpResponseRedirect:

		if self.form.is_valid():
			new_values = self.form.cleaned_data
			old_values = {'worker': self.worker}

			if self.extdata.exists():
				old_values.update(self.extdata.values(*self.fields)[0])
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

			return HttpResponseRedirect(reverse('employee:employee_extendeddata', args=[self.employee_id]))

		else:
			return render(request, 'employee/employee_extendeddata.html', self.context)


class EmployeeHourlyRateView(View):
	'''class implementing the method of changing the hourly rate for the employee by pk=employee_id'''
	def setup(self, request, *args, **kwargs):
		super(EmployeeHourlyRateView, self).setup(request, **kwargs)
		self.request, self.kwargs = request, kwargs
		
		if 'employee_id' in self.kwargs.keys():
			self.employee_id = self.kwargs['employee_id']
		
		self.worker = Employee.objects.get(pk=self.employee_id)
		employees = Employee.objects.filter(status=True)
		
		self.context = {'worker': self.worker, 'employee_id': self.employee_id, 'employees': employees}
		
		if self.request.method == 'GET':
			all_hourly_rate = EmployeeHourlyRate.objects.filter(worker=self.worker).order_by('update')
			last_hourly_rate = all_hourly_rate.last()
			initial={'worker': self.worker, 'hourly_rate': f'{last_hourly_rate.hourly_rate:.2f}'}
			self.form = EmployeeHourlyRateForm(initial=initial)
			self.context.update({'all_hourly_rate': all_hourly_rate, 'last_hourly_rate': last_hourly_rate})
		elif self.request.method == 'POST':
			self.form = EmployeeHourlyRateForm(data=self.request.POST)
			self.context.update({'update': now().date()})

		self.context.update({'form': self.form})


	def get(self, request, **kwargs)->render:
		
		return render(request, 'employee/employee_hourly_rate.html', self.context)


	def post(self, request, **kwargs)->render:

		if self.form.is_valid():
			data = self.form.cleaned_data
			values = {'worker': self.worker, 'update__year': now().year, 'update__month': now().month}

			if EmployeeHourlyRate.objects.filter(**values).exclude(update__exact=now().date()).exists():
				msg = f'Rate for employee ({self.worker}) is existing in database...'
				messages.error(request, msg)
				self.context.__setitem__('check_rate', True)
			else:
				all_hourly_rate = EmployeeHourlyRate.objects.filter(worker=self.worker).order_by('update')
				last_exist_hourly_rate = all_hourly_rate.last()

				if data['hourly_rate'] != last_exist_hourly_rate.hourly_rate:
					defaults = {'hourly_rate': data['hourly_rate']}
					kwargs = {'worker_id': self.employee_id, 'update': now().date()}
					obj, created = EmployeeHourlyRate.objects.update_or_create(defaults=defaults, **kwargs)
					self.context.__setitem__('hourly_rate', obj.hourly_rate)

					if created:
						msg = f'For employee ({self.worker}) add new hourly rate ({obj.hourly_rate} PLN)'
						messages.success(request, msg)
					else:
						msg = f'For employee {self.worker} update hourly rate ({obj.hourly_rate} PLN)'
						messages.success(request, msg)
				else:
					msg = f'Last hourly rate {last_exist_hourly_rate} for {self.worker} is the same like enterd.'
					messages.success(request, msg)
					self.context.__setitem__('last_exist_hourly_rate', last_exist_hourly_rate)

		return render(request, 'employee/employee_hourly_rate.html', self.context)


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

