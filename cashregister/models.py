# django core
from django.db import models
from django.urls import reverse

# validators
from validators.my_validator import positive_value, from_transfer

# Create your models here.


class Company(models.Model):
    company = models.CharField(max_length=240,)
    nip = models.CharField(max_length=13,)
    street = models.CharField(blank=True, max_length=100,)
    city = models.CharField(blank=True, max_length=100,)
    postal = models.CharField(blank=True, max_length=10, verbose_name='Postal code')
    phone = models.CharField(blank=True, max_length=20,)
    account = models.CharField(blank=True, max_length=34, verbose_name='Contrary account')
    status = models.IntegerField(default=1,)
    created = models.DateTimeField(auto_now_add=True,)
    updated = models.DateTimeField(auto_now=True,)

    class Meta:
        ordering = ['company']

    def __str__(self):
        return f'{self.company}'

    def get_absolute_url(self):
        return reverse('cashregister:change_company', args=[self.id])

    def add_records(self):
        return reverse('cashregister:cash_register', args=[self.id])


class CashRegister(models.Model):
    company = models.ForeignKey(Company, on_delete=models.DO_NOTHING)
    created = models.DateTimeField(auto_now_add=True,)
    symbol = models.CharField(max_length=200,)
    contents = models.CharField(max_length=250,)
    income = models.FloatField(default=0.0,)
    expenditure = models.FloatField(default=0.0,)
    cashaccept = models.SmallIntegerField(null=True, blank=True)

    class Meta:
        ordering = ['company', 'created']

    def __str__(self):
        return f'Cash register: {self.company}'

    def cash_accept(self):
        return reverse('cashregister:cash_accept', args=[self.company.id, self.id])

    def cashregister_delete(self):
        return reverse('cashregister:cash_register_delete', args=[self.company.id, self.id])
