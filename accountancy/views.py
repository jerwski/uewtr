# django library
from django.urls import reverse
from django.shortcuts import render
from django.contrib import messages
from django.utils.timezone import now
from django.views.generic import View
from django.http import HttpResponse, HttpResponseRedirect

# my models
from cashregister.models import Company
from accountancy.models import Customer, Product, AccountancyDocument, AccountancyProducts

# my forms
from accountancy.forms import CustomerAddForm, AccountancyDocumentForm, NewProductAddForm

# my functions
from functions.myfunctions import last_relased_accountancy_document


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


class AccountancyDocumentView(View):
	'''class implementing the method of create the accountancy document'''

	def get(self, request, company_id:int=None, customer_id:int=None) -> HttpResponse:
		context = {'company_id': company_id, 'customer_id': customer_id}
		companies = Company.objects.filter(status__range=[1, 3])
		customers = Customer.objects.filter(status__range=[1, 3])
		documents = AccountancyDocument.objects.filter(company_id=company_id, customer_id=customer_id, created__year=now().year)
		context.update({'companies': companies, 'customers': customers, 'documents': documents})
		number = last_relased_accountancy_document(company_id)

		initial = {'number': number,
		           'date_of_shipment': now().date(),
		           'order': f'{number}/{now().year}',
		           'invoice': f'FS-{number}/{now().year}',
		           'waybill': f'LKW-{number}/{now().year}',}

		if company_id:
			company = Company.objects.get(pk=company_id)
			context.__setitem__('company', company)
			initial.__setitem__('company', company)

		if customer_id:
			customer = Customer.objects.get(pk=customer_id)
			context.__setitem__('customer', customer)
			initial.__setitem__('customer', customer)

		form = AccountancyDocumentForm(initial=initial)
		context.__setitem__('form', form)

		return render(request, 'accountancy/accountancy_document.html', context)


	def post(self, request, company_id:int=None, customer_id:int=None) -> HttpResponseRedirect:
		company = Company.objects.get(pk=company_id)
		form = AccountancyDocumentForm(data=request.POST)

		if form.is_valid():
			data = form.cleaned_data
			number = data['number']
			data.pop('number')
			obj, create = AccountancyDocument.objects.get_or_create(defaults={'number': number}, **data)
			if create:
				document_id = obj.pk
				return HttpResponseRedirect(reverse('accountancy:add_product', args=[company_id, customer_id, document_id]))
		else:
			messages.success(request, 'Some data are not valid. Please type correct data.')

		return render(request, 'accountancy/accountancy_document.html', {'form': form, 'company': company})


class AccountancyProductsAddView(View):
	'''class enabling adding products into accountancy document'''

	def get(self, request, company_id:int=None, customer_id:int=None, document_id:int=None, product_id:int=None, new_id:int=None) -> HttpResponse:
		company = Company.objects.get(pk=company_id)
		customer = Customer.objects.get(pk=customer_id)
		document = AccountancyDocument.objects.get(pk=document_id)
		context = {'company': company, 'customer': customer, 'document':document}
		products = AccountancyProducts.objects.filter(document_id=document_id).order_by('-created')
		products_name = Product.objects.order_by('name').values_list('name', flat=True)
		context.update({'products': products, 'products_name': list(products_name)})
		if product_id:
			product = Product.objects.get(pk=product_id)
			initial = {'name': product.name, 'unit': product.unit, 'netto': product.netto, 'vat': int(product.vat)}
			new_product_form = NewProductAddForm(initial=initial)
			context.update({'product_id': product_id, 'product': product})
		else:
			new_product_form = NewProductAddForm()

		if new_id:
			new_product = Product.objects.get(pk=new_id)
			context.__setitem__('new_name', new_product.name)

		context.update({'new_product_form': new_product_form, 'company_id': company_id,
		                'customer_id': customer_id, 'document_id': document_id})

		return render(request, 'accountancy/accountancy_document_add_product.html', context)

	def post(self, request, company_id:int=None, customer_id:int=None, document_id:int=None, product_id:int=None) -> HttpResponse:
		document = AccountancyDocument.objects.get(pk=document_id)
		products_name = Product.objects.order_by('name').values_list('name', flat=True)
		
		if product_id:
			name, unit, netto, vat = request.POST['name'], request.POST['unit'], request.POST['netto'], request.POST['vat']
			update = {'name': name, 'updated': now(), 'unit': unit, 'netto': netto, 'vat': vat}
			try:
				Product.objects.filter(pk=product_id).update(**update)
				product = Product.objects.get(pk=product_id)
				kwargs = {'product': product, 'updated': now(), 'netto': netto, 'vat': vat}
				AccountancyProducts.objects.filter(document=document, product_id=product_id).update(**kwargs)
				messages.info(request, f'Product <<{product}>> has been updated...')
			except:
				msg = f'Product <<{name}>> exist in database. Name of product need to be unique.'
				messages.info(request, msg)
		else:
			name = request.POST['product']
			quanity = request.POST['quanity']
			quanity = float(quanity)
			
			if name in products_name and quanity > 0:
				product = Product.objects.get(name=name)
				netto, vat = product.netto, product.vat
				data = {'document': document, 'product': product, 'quanity': quanity, 'netto': netto, 'vat': vat}
				AccountancyProducts.objects.create(**data)
			else:
				if name not in products_name:
					msg = f'Products <<{name}>> in not rejestred. Please use "Add new product" button on the right side form.'
					messages.warning(request, msg)
				elif quanity <= 0:
					msg = f'Quanity <<{quanity}>> need be grower than zero value'
					messages.warning(request, msg)

		return HttpResponseRedirect(reverse('accountancy:add_product', args=[company_id, customer_id, document_id]))


class NewProductAddView(View):
	'''class implementing the method of adding new product'''

	def post(self, request, company_id:int=None, customer_id:int=None, document_id:int=None) -> HttpResponseRedirect:
		form = NewProductAddForm(data=request.POST)
		
		if form.is_valid():
			new_product = form.save()
			new_id = new_product.id
			args=[company_id, customer_id, document_id, new_id]

		else:
			args = [company_id, customer_id, document_id]
			messages.warning(request, f'Product exist in database...')

		return HttpResponseRedirect(reverse('accountancy:add_product', args=args))
			



class AccountancyProductDelete(View):
	'''class enabling deleting records in the cash report'''

	def get(self, request, record:int=None, company_id:int=None, customer_id:int=None, document_id:int=None) -> HttpResponseRedirect:
		try:
			record = AccountancyProducts.objects.get(pk=record)
			record.delete()
			msg = f'Succesful erase record <<name: {record.product}, quanity: {record.quanity}>> in accountancy document <<{record.document}>> for {record.document.company}.'
			messages.info(request, msg)
		except:
			messages.info(request, 'Something\'s wrong')
		return HttpResponseRedirect(reverse('accountancy:add_product', args=[company_id, customer_id, document_id]))



class AccountancyDocumentPrintView(View):
	'''class enabling printing selected document'''
	
	def post(self, request, document_id:int=None) -> HttpResponse:
		'''convert html accountancy document  to pdf'''
		# year = int(request.POST['leave_year'])
		# html = leavehtml2pdf(document_id, year)
		#
		# if html:
		# 	# create pdf file
		# 	options = {'page-size'  : 'A4', 'margin-top': '1.0in', 'margin-right': '0.1in', 'margin-bottom': '0.1in',
		# 	           'margin-left': '0.1in', 'encoding': "UTF-8", 'orientation': 'landscape', 'no-outline': None,
		# 	           'quiet'      : '', }
		#
		# 	pdf = pdfkit.from_string(html, False, options=options)
		# 	filename = f'leaves_data_{employee_id}.pdf'
		#
		# 	response = HttpResponse(pdf, content_type='application/pdf')
		# 	response['Content-Disposition'] = 'attachment; filename="' + filename + '"'
		# 	return response
		# else:
		# 	messages.warning(request, r'Nothing to print...')
		#
		# return HttpResponseRedirect(reverse('evidence:leave_time_recorder_add', args=[employee_id]))
