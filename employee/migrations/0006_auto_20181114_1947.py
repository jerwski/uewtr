# Generated by Django 2.0.9 on 2018-11-14 18:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('employee', '0005_auto_20181114_1828'),
    ]

    operations = [
        migrations.AlterField(
            model_name='employee',
            name='status',
            field=models.BooleanField(default=True, verbose_name='Active'),
        ),
    ]
