# django core
from django.db import models
from django.urls import reverse
from django.utils.timezone import now

# my models
from cashregister.models import Company
from account.models import CreationModificationDateMixin

# my validators
from validators.my_validator import positive_value

# Create your models here.


class Customer(CreationModificationDateMixin):
	customer = models.CharField(max_length=240,)
	nip = models.CharField(max_length=13,)
	street = models.CharField(blank=True, max_length=100,)
	city = models.CharField(blank=True, max_length=100,)
	postal = models.CharField(blank=True, max_length=10, verbose_name='Postal code')
	phone = models.CharField(blank=True, max_length=20,)
	email = models.EmailField(blank=True,)
	status = models.IntegerField(default=1,)

	class Meta:
		ordering = ['customer']

	def __str__(self):
		return self.customer

	def get_absolute_url(self):
		return reverse('accountancy:change_customer', args=[self.id])


class Product(CreationModificationDateMixin):
	ZW = 0
	VAT5 = 5
	VAT8 = 8
	VAT23 = 23
	VAT = ((VAT23, '23%'), (VAT5, '5%'), (VAT8, '8%'), (ZW, 'Zwolniony'))
	
	SZTUK = 0
	KOMPLET = 1
	TYSIĄC = 2
	ARKUSZ = 3
	LITR = 4
	ROLA = 5
	UNITS = ((SZTUK, 'szt.'), (KOMPLET, 'kpl.'), (TYSIĄC, 'tys.'), (ARKUSZ, 'ark.'), (LITR, 'ltr.'), (ROLA, 'rola'))
	
	name = models.CharField(max_length=200, db_index=True, unique=True, verbose_name='Nazwa Produktu')
	unit = models.PositiveSmallIntegerField(blank=True, choices=UNITS, verbose_name='Jednostka masy')
	netto = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Wartość netto')
	vat = models.DecimalField(max_digits=4, decimal_places=2, choices=VAT, default=VAT23, verbose_name='Stawka podatku VAT')

	class Meta:
		ordering = ('name',)

	def __str__(self):
		return self.name

	def get_absolute_url(self):
		return reverse('accountancy:change_customer', args=[self.id])

	def get_brutto(self):
		brutto = self.netto * (1 + self.vat / 100)
		return brutto


class AccountancyDocument(CreationModificationDateMixin):
	company = models.ForeignKey(Company, limit_choices_to={'status__range': [1, 3]}, on_delete=models.DO_NOTHING)
	customer = models.ForeignKey(Customer, limit_choices_to={'status__range': [1, 3]}, on_delete=models.DO_NOTHING, verbose_name='Klient')
	number = models.SmallIntegerField(verbose_name='Nr porządkowy dokumentu')
	conveyance = models.CharField(max_length=25,)
	waybill = models.CharField(max_length=100, blank=True, verbose_name='Nr listu przewozowego')
	date_of_shipment = models.DateField()
	invoice = models.CharField(max_length=250, verbose_name='Numer faktury')
	order = models.CharField(max_length=250, verbose_name='Zamówienie')

	class Meta:
		ordering = ['-number']

	def __str__(self):
		return f'{self.number}/{now().month}/{now().year}'

	def get_total_cost(self):
		total_cost = sum(item.get_cost() for item in self.products.all())
		return total_cost


class AccountancyProducts(CreationModificationDateMixin):
	document = models.ForeignKey(AccountancyDocument, related_name='products', on_delete=models.CASCADE)
	product = models.ForeignKey(Product, on_delete=models.DO_NOTHING)
	quanity = models.DecimalField(max_digits=9, decimal_places=2, verbose_name='Ilość', validators=[positive_value])

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
