# django core
from django.db import models
from django.urls import reverse

# validators
from validators.my_validator import positive_value

# Create your models here.

'''
oznaczenie firmy np. pieczątka firmowa,

oznaczenie dokumentu oraz jego kolejny numer - można stosować numerację ciągłą lub numerację wskazującą określoną kasę, rok obrachunkowy, miesiąc i dzień, np. Kasa2/ /2015/06/1,

określenie okresu, za który raport został sporządzony - czas ten powinien być zgodny z założeniami przyjętymi w instrukcji kasowej,

nazwę rejestru,

wyszczególnienie wszystkich operacji (treść, numer dowodu źródłowego, data oraz oznaczenie osoby pobierającej / wpłacającej środki pieniężne),

numer konta przeciwstawnego - numery kont, na które, zgodnie z zasadą podwójnego zapisu, odnoszone są operacje gospodarcze ujęte w raporcie kasowym,

wyliczenie obrotów, stanu początkowego i końcowego kasy - saldo RK może być wyłącznie dodatnie, gdyż fizycznie niemożliwe jest wypłacenie większej kwoty pieniędzy niż faktycznie znajduje się w kasie; jeśli raport kasowy prezentuje saldo ujemne najczęściej wiąże się to z błędem ewidencyjnym lub rachunkowym,

liczbę załączników (do sporządzonego RK należy załączyć wszelkie źródłowe dokumenty kasowe oraz zastępcze dowody księgowe),

podpis kasjera oraz data sporządzenia RK,

datę zatwierdzania raportu.

wzór raporu w pliku templates/cashregister/pdf
'''

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
    date = models.DateField(auto_now_add=True)
    symbol = models.CharField(max_length=100, blank=True, verbose_name='Symbol and document number')
    contents = models.CharField(max_length=250)
    income = models.FloatField(default=0.00, validators=[positive_value])
    expenditure = models.FloatField(default=0.00, validators=[positive_value])

    class Meta:
        ordering = ['date']

    def __str__(self):
        return f'Cash register: {self.company}'
