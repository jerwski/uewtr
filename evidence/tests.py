# standart library
from datetime import datetime

# Django library
from django.test import TestCase
from django.db.models import Sum

# my models
from employee.models import Employee
from evidence.models import WorkEvidence

# Create your tests here


class WorkingHourTests(TestCase):
    def setUp(self):
        start = [datetime(2018,9,i,6,0) for i in range(1, 31)]
        end = [datetime(2018,9,i,14,0) for i in range(1, 31)]
        # create dictionary from start and end elements
        dataset = dict(zip(start,end))
        employe = Employee.objects.create(forename='Forename', surname='Surname', pesel='73021602009', status=True)
        pk = employe.id
        worker = Employee.objects.get(pk=pk)
        # create data in evidence_workevidence table
        for k,v in dataset.items():
            WorkEvidence.objects.create(worker=worker, start_work=k, end_work=v, jobhours=8)


    def testPayment(self):
        """method for data compare"""
        week_hours = WorkEvidence.objects.filter(worker_id=1, start_work__week_day__gt=1, end_work__week_day__lt=7)
        saturday_hours = WorkEvidence.objects.filter(worker_id=1, start_work__week_day=7, end_work__week_day=7)
        sunday_hours = WorkEvidence.objects.filter(worker_id=1, start_work__week_day=1, end_work__week_day=1)
        all_hours = WorkEvidence.objects.filter(worker_id=1)

        # create dictionary with key as queryset and value as expected sum of hours
        hours = {week_hours:160, saturday_hours:40, sunday_hours:40, all_hours:240}

        # comparison of data
        for key, value in hours.items():
            qs = key.aggregate(suma=Sum('jobhours'))
            self.assertEqual(qs['suma'] == value, True)
            print(key.query,'\nAmount of hours: ',value,'\n')
