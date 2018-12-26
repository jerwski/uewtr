# django core
from django.db import models
from django.urls import reverse

# my validators
from validators.my_validator import check_pesel


# Create your models here.


class Employee(models.Model):
    '''class representing a basic data table of employee'''
    UNPAID_LEAVE = 0
    PAID_LEAVE = 1
    LEAVE_CHOICE = ((UNPAID_LEAVE, 'Unpaid'), (PAID_LEAVE,'Paid'))
    # fields
    forename = models.CharField(max_length=100,)
    surname = models.CharField(max_length=100,)
    pesel = models.CharField(max_length=11, validators=[check_pesel])
    status = models.BooleanField(default=True, verbose_name='Active')
    leave = models.IntegerField(choices=LEAVE_CHOICE, default=UNPAID_LEAVE)

    class Meta:
        ordering = ['surname']

    def __str__(self):
        return f'{self.surname} {self.forename}'

    def __lt__(self, other):
        return self.surname < other.surname

    def __gt__(self, other):
        return other.surname < self.surname

    def get_absolute_url(self):
        return reverse('employee:employee_basicdata', args=[self.id])

    def employee_change_extend_data_id(self):
        return reverse('employee:employee_extendeddata', args=[self.id])

    def work_employee_id(self):
        return reverse('evidence:working_time_recorder_add', args=[self.id])

    def leave_employee_id(self):
        return reverse('evidence:leave_time_recorder_add', args=[self.id])
    
    def account_payment_employee_id(self):
        return reverse('evidence:account_payment', args=[self.id])

    def hurly_rate_employee_id(self):
        return reverse('employee:employee_hourly_rate', args=[self.id])

    def employee_complex_data(self):
        return reverse('evidence:employee_complex_data', args=[self.id])

    def employee_data_set(self):
        return reverse('evidence:employee_data_set', args=[self.id])


class EmployeeData(models.Model):
    '''class representing an extented data table of employee'''
    worker = models.ForeignKey(Employee, on_delete=models.CASCADE)
    birthday = models.DateField(null=True,)
    postal = models.CharField(max_length=100,)
    city = models.CharField(max_length=100,)
    street = models.CharField(max_length=100,)
    house = models.CharField(max_length=10,)
    flat = models.CharField(max_length=100, blank=True,)
    phone = models.CharField(max_length=50, blank=True)
    workplace = models.CharField(max_length=100, )
    start_contract = models.DateField(null=True,)
    end_contract = models.DateField(null=True, blank=True)
    overtime = models.IntegerField()

    class Meta:
        ordering = ['worker']

    def __str__(self):
        return f'{self.worker}'


class EmployeeHourlyRate(models.Model):
    '''class representing an hourly rate data table of employee'''
    worker = models.ForeignKey(Employee, on_delete=models.CASCADE)
    update = models.DateField()
    hourly_rate = models.FloatField(max_length=5)

    def __str__(self):
        return f'{self.hourly_rate:,.2f} PLN/h'
