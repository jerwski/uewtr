# django core
from django.db import models

# my models
from employee.models import Employee


# Create your models here.


class WorkEvidence(models.Model):
    worker = models.ForeignKey(Employee, on_delete=models.CASCADE)
    start_work = models.DateTimeField(blank=True,)
    end_work = models.DateTimeField(blank=True,)
    jobhours = models.FloatField(blank=True,)

    class Meta:
        ordering = ['worker', '-start_work']

    def __str__(self):
        return f'{self.worker}'


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
    account_value = models.FloatField(default=50.00,)
    notice = models.TextField()

    class Meta:
        ordering = ['-account_date', 'worker']

    def __str__(self):
        return str(self.worker)
