# django library
from django.urls import reverse
from django.conf import settings
from django.shortcuts import render
from django.contrib import messages
from django.utils.timezone import now
from django.views.generic import View
from django.http import HttpResponse, HttpResponseRedirect

# my models
from accountancy.models import Customer

# my forms
from accountancy.forms import CustomerAddForm


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
	#
	# def get(self, request, company_id:int=None) -> HttpResponseRedirect:
	# 	check = CashRegister.objects.filter(company_id=company_id)
	# 	tags = CashRegister.objects.order_by('contents').distinct('contents').exclude(contents='z przeniesienia').values_list('contents', flat=True)
	# 	symbols = CashRegister.objects.order_by('symbol').distinct('symbol').values_list('symbol', flat=True)
	# 	companies = Company.objects.filter(status__range=[1, 3]).order_by('company')
	# 	context = {'companies': companies, 'tags': list(tags), 'symbols': list(symbols)}
	#
	# 	if company_id:
	# 		month, year = now().month, now().year
	# 		company = Company.objects.get(pk=company_id)
	# 		registerdata = cashregisterdata(company_id, month, year)
	# 		context.update(dict(registerdata))
	# 		records = check.filter(created__month=month, created__year=year).exclude(contents='z przeniesienia')
	# 		form = CashRegisterForm(initial={'company': company})
	# 		context.update({'form': form, 'company': company, 'company_id': company_id,
	# 		                'records': records.order_by('-created')})
	#
	# 		if now().month==1:
	# 			month, year = 12, now().year - 1
	# 		else:
	# 			month, year = now().month - 1, now().year
	#
	# 		previous = check.filter(created__month=month, created__year=year)
	#
	# 		if previous:
	# 			context.__setitem__('previous', True)
	# 		else:
	# 			context.__setitem__('previous', False)
	#
	# 	return render(request, 'cashregister/cashregister.html', context)
	#
	# def post(self, request, company_id:int=None) -> HttpResponseRedirect:
	# 	form = CashRegisterForm(data=request.POST)
	# 	check = CashRegister.objects.filter(company_id=company_id)
	# 	companies = Company.objects.filter(status__in=[1,2,3]).order_by('company')
	# 	context = {'form': form, 'companies': companies}
	#
	# 	if company_id:
	# 		month, year = now().month, now().year
	# 		company = Company.objects.get(pk=company_id)
	# 		registerdata = cashregisterdata(company_id, month, year)
	# 		context.update(dict(registerdata))
	# 		records = check.filter(created__month=month, created__year=year).exclude(contents='z przeniesienia')
	# 		context.update({'company': company, 'company_id': company_id, 'records': records.order_by('-created')})
	#
	# 		if now().month==1:
	# 			month, year = 12, now().year - 1
	# 		else:
	# 			month, year = now().month - 1, now().year
	#
	# 		previous = check.filter(created__month=month, created__year=year)
	#
	# 		if previous:
	# 			context.__setitem__('previous', True)
	# 		else:
	# 			context.__setitem__('previous', False)
	#
	# 		if form.is_valid():
	# 			form.save(commit=False)
	# 			data = form.cleaned_data
	# 			income, expenditure = [data[key] for key in ('income', 'expenditure')]
	# 			if income != 0 and expenditure != 0:
	# 				msg = f'One of the fields (income {income:.2f}PLN or expenditure {expenditure:.2f}PLN) must be zero and second have to be positive value!'
	# 				messages.warning(request, msg)
	# 				return render(request, 'cashregister/cashregister.html', context)
	# 			elif income or expenditure:
	# 				if income > 0:
	# 					form.save(commit=True)
	# 					msg = f'Succesful register new record in {company} (income={income:.2f}PLN)'
	# 					messages.success(request, msg)
	# 				elif expenditure > 0:
	# 					if registerdata['status'] - expenditure > 0:
	# 						form.save(commit=True)
	# 						msg = f'Succesful register new record in {company} (expenditure={expenditure:.2f}PLN)'
	# 						messages.success(request, msg)
	# 					else:
	# 						msg = f"Expenditure ({expenditure:.2f}PLN) is greater than the cash register status ({registerdata['status']:.2f}PLN)!"
	# 						messages.warning(request, msg)
	#
	# 	return HttpResponseRedirect(reverse('cashregister:cash_register', args=[company_id]))


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
