# standard library
import datetime

# django core
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


# my models
from employee.models import Employee


# Create your models here.


class WorkEvidence(models.Model):
    worker = models.ForeignKey(Employee, on_delete=models.CASCADE)
    start_work = models.DateTimeField()
    end_work = models.DateTimeField()
    jobhours = models.FloatField()

    class Meta:
        ordering = ['worker', '-start_work']

    def __str__(self):
        return f'{self.worker}'

    def clean(self):
        # Check the start-work and end-work date is less or equal from today.
        if self.start_work.date() > datetime.date.today() or self.end_work.date() > datetime.date.today():
            raise ValidationError(_('The start-work and end-work date have to be less or equal from today'))


class EmployeeLeave(models.Model):
    worker = models.ForeignKey(Employee, on_delete=models.CASCADE)
    leave_date = models.DateField()
    leave_flag = models.CharField(max_length=25,)

    class Meta:
        ordering = ['worker', '-leave_date']

    def __str__(self):
        return f'{self.worker} : {self.leave_date}'


class AccountPayment(models.Model):
    worker = models.ForeignKey(Employee, on_delete=models.CASCADE)
    account_date = models.DateField()
    account_value = models.FloatField()
    notice = models.TextField()

    class Meta:
        ordering = ['-account_date', 'worker']

    def __str__(self):
        return f'{self.worker}'

    def clean(self):
        # Don't allow value is less than 10.00 PLN.
        if self.account_value < 10.0:
            raise ValidationError(_('The value provided is less than 10.00 PLN'))
