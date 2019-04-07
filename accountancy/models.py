# django core
from django.db import models
from django.urls import reverse

# my models
from cashregister.models import Company

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
		return f'{self.customer}'

	def get_absolute_url(self):
		return reverse('accountancy:change_customer', args=[self.id])


class Products(models.Model):
	name = models.CharField(max_length=200, db_index=True)
	slug = models.SlugField(max_length=200, db_index=True)
	netto = models.DecimalField(max_digits=10, decimal_places=2)
	vat = models.DecimalField(max_digits=4, decimal_places=2, default=23)
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


class ReleaseOutside(models.Model):
	company = models.ForeignKey(Company, limit_choices_to={'status__range': [1, 3]}, on_delete=models.DO_NOTHING)
	customer = models.ForeignKey(Customer, limit_choices_to={'status__range': [1, 3]}, on_delete=models.DO_NOTHING)
	number = models.SmallIntegerField(unique_for_month=True,)
	conveyance = models.CharField(max_length=25,)
	waybill = models.CharField(max_length=100,)
	date_of_shipment = models.DateField()
	invoice = models.CharField(max_length=250,)
	order = models.CharField(max_length=250,)
	created = models.DateTimeField(auto_now_add=True)
	updated = models.DateTimeField(auto_now=True)

	def get_total_cost(self):
		total_cost = sum(item.get_cost() for item in self.products.all())
		return total_cost


class ReleaseOutsideProduct(models.Model):
	release = models.ForeignKey(ReleaseOutside, related_name='products', on_delete=models.DO_NOTHING)
	product = models.ForeignKey(Products, on_delete=models.DO_NOTHING)
	quanity = models.PositiveIntegerField(default=1,)
	unit = models.CharField(max_length=25,)

	def get_cost(self):
		worth = self.product.get_brutto() * self.quanity
		return worth
