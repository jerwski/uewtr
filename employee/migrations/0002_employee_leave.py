# Generated by Django 2.0.9 on 2018-11-14 16:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('employee', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='leave',
            field=models.IntegerField(choices=[(0, 'Unpaid'), (1, 'Paid')], default=0),
        ),
    ]
