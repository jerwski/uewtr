# django library
from django.urls import reverse
from django.conf import settings
from django.shortcuts import render
from django.contrib import messages
from django.utils.timezone import now
from django.views.generic import View
from django.http import HttpResponse, HttpResponseRedirect
from django.db.models import Case, Count, IntegerField, Max, Q, Sum, Value, When

# my models
from accountancy.models import Customer, Products, AccountancyDocument, AccountancyProducts

# my forms
from accountancy.forms import CustomerAddForm, AccountancyDocumentForm


# Create your views here.


class CustomerAddView(View):
	'''class implementing the method of adding/changing basic data for the new or existing customer'''

	def get(self, request, customer_id:int = None) -> render:
		customers = Customer.objects.order_by('customer')
		if customer_id:
			customer = Customer.objects.get(pk=customer_id)
			fields = list(customer.__dict__.keys())[2:-2]
			initial = Customer.objects.filter(pk=customer_id).values(*fields)[0]
			form = CustomerAddForm(initial=initial)
			context = {'form': form, 'customer_id': customer_id, 'customers': customers, }

		else:
			form = CustomerAddForm()
			context = {'form': form, 'customers': customers, }

		return render(request, 'accountancy/customer_add.html', context)

	def post(self, request, customer_id:int = None) -> HttpResponseRedirect:
		customers = Customer.objects.all().order_by('customer')
		form = CustomerAddForm(data=request.POST)
		context = {'form': form, 'customers': customers, }

		if customer_id:
			employee = Customer.objects.get(pk=customer_id)
			fields = list(employee.__dict__.keys())[2:-2]
			old_values = Customer.objects.filter(pk=customer_id).values(*fields)[0]
			old_values['status'] = str(old_values['status'])
		else:
			old_values = {'nip': request.POST['nip']}

		if form.is_valid():
			new_values = form.cleaned_data

			if new_values!=old_values:

				try:
					obj, created = Customer.objects.update_or_create(defaults=new_values, **old_values)

					if created:
						msg = f'Successful created new customer {obj}'
						messages.success(request, msg)
					else:
						msg = f'Successful update data for customer {obj}'
						messages.success(request, msg)

					return HttpResponseRedirect(reverse('accountancy:change_customer', args=[obj.id]))

				except Customer.DoesNotExist:
					messages.warning(request, r'Somthing wrong... try again!')

			else:
				messages.info(request, r'Nothing to change!')
				return HttpResponseRedirect(reverse('accountancy:change_customer', args=[customer_id]))
		else:
			return render(request, 'accountancy/customer_add.html', context)


class ReleaseOutsideView(View):
	'''class implementing the method of adding records to the Release Outside'''

	def get(self, request, released_id:int=None) -> HttpResponseRedirect:
		user = request.user
		# TODO: set last number of released
		check = {'created__year': now().year, 'created__month': now().month}
		last_released = AccountancyDocument.objects.filter(**check).aggregate(Max('number'))
		if last_released['number__max']:
			number = f"{last_released['number__max'] + 1}/{now().year}"
		else:
			number = 1

		form = AccountancyDocumentForm(initial={'number': number})
		context = {'form': form}

		return render(request, 'accountancy/customer_add.html', context)


	def post(self, request, released_id:int=None) -> HttpResponseRedirect:
		form = AccountancyDocumentForm(data=request.POST)
		context = {'form': form}

		if form.is_valid():
			form.save(commit=False)
			data = form.cleaned_data
			form.save(commit=True)
			msg = f'Let show me: {data}!'
			messages.warning(request, msg)

		return HttpResponseRedirect(reverse('accountancy:add_customer', args=[context]))


class ReleaseOutsideDelete(View):
	'''class enabling deleting records in the release outside'''
	#
	# def get(self, request, company_id:int, record:int) -> HttpResponseRedirect:
	# 	record = CashRegister.objects.get(pk=record)
	# 	if record:
	# 		record.delete()
	# 		msg = f'Succesful erase record <<{record.symbol}, {record.contents} in Cash register for {record.company}.'
	# 		messages.info(request, msg)
	# 	return HttpResponseRedirect(reverse('cashregister:cash_register', args=[company_id]))
