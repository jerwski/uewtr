# Generated by Django 2.0.9 on 2018-12-25 16:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('employee', '0009_auto_20181224_2202'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='employeedata',
            options={'ordering': ['worker']},
        ),
        migrations.RenameField(
            model_name='employeedata',
            old_name='name',
            new_name='worker',
        ),
        migrations.RenameField(
            model_name='employeehourlyrate',
            old_name='name',
            new_name='worker',
        ),
    ]