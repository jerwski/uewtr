# django core
from django.db import models
from django.urls import reverse
from django.utils.timezone import now

# my models
from cashregister.models import Company

# my validators
from validators.my_validator import positive_value

# Create your models here.


class Customer(models.Model):
	customer = models.CharField(max_length=240,)
	nip = models.CharField(max_length=13,)
	street = models.CharField(blank=True, max_length=100,)
	city = models.CharField(blank=True, max_length=100,)
	postal = models.CharField(blank=True, max_length=10, verbose_name='Postal code')
	phone = models.CharField(blank=True, max_length=20,)
	email = models.EmailField(blank=True,)
	status = models.IntegerField(default=1,)
	created = models.DateTimeField(auto_now_add=True,)
	updated = models.DateTimeField(auto_now=True,)

	class Meta:
		ordering = ['customer']

	def __str__(self):
		return self.customer

	def get_absolute_url(self):
		return reverse('accountancy:change_customer', args=[self.id])


class Products(models.Model):
	name = models.CharField(max_length=200, db_index=True, unique=True, verbose_name='Nazwa Produktu')
	slug = models.SlugField(max_length=200, db_index=True)
	unit = models.PositiveSmallIntegerField(blank=True,)
	netto = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Wartośc netto')
	vat = models.DecimalField(max_digits=4, decimal_places=2, verbose_name='Stawka podatku VAT')
	created = models.DateTimeField(auto_now_add=True)
	updated = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ('name',)
		indexes = [models.Index(fields=['id', 'slug']),]

	def __str__(self):
		return self.name

	def get_absolute_url(self):
		return reverse('accountancy:change_customer', args=[self.id, self.slug])

	def get_brutto(self):
		brutto = self.netto * (1 + self.vat / 100)
		return brutto


class AccountancyDocument(models.Model):
	company = models.ForeignKey(Company, limit_choices_to={'status__range': [1, 3]}, on_delete=models.DO_NOTHING)
	customer = models.ForeignKey(Customer, limit_choices_to={'status__range': [1, 3]}, on_delete=models.DO_NOTHING, verbose_name='Klient')
	number = models.SmallIntegerField(verbose_name='Nr porządkowy dokumentu')
	conveyance = models.CharField(max_length=25,)
	waybill = models.CharField(max_length=100, blank=True, verbose_name='Nr listu przewozowego')
	date_of_shipment = models.DateField()
	invoice = models.CharField(max_length=250, verbose_name='Numer faktury')
	order = models.CharField(max_length=250, verbose_name='Zamówienie')
	created = models.DateTimeField(auto_now_add=True)
	updated = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['-number']

	def __str__(self):
		return f'{self.number}/{now().month}/{now().year}'

	def get_total_cost(self):
		total_cost = sum(item.get_cost() for item in self.products.all())
		return total_cost


class AccountancyProducts(models.Model):
	document = models.ForeignKey(AccountancyDocument, related_name='products', on_delete=models.CASCADE)
	product = models.ForeignKey(Products, on_delete=models.DO_NOTHING)
	quanity = models.DecimalField(max_digits=9, decimal_places=2, verbose_name='Ilość', validators=[positive_value])
	created = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['product']

	def __str__(self):
		return f'{self.product}'

	def get_cost(self):
		worth = self.product.get_brutto() * self.quanity
		return worth

	def product_delete(self):
		args = [self.id, self.document.company_id, self.document.customer_id, self.document_id]
		return reverse('accountancy:delete_product', args=args)
