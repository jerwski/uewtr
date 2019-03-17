# Generated by Django 2.1.7 on 2019-03-17 12:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cashregister', '0002_auto_20190316_0749'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cashregister',
            name='contents',
            field=models.CharField(max_length=250),
        ),
        migrations.AlterField(
            model_name='cashregister',
            name='expenditure',
            field=models.FloatField(default=0.0),
        ),
        migrations.AlterField(
            model_name='cashregister',
            name='income',
            field=models.FloatField(default=0.0),
        ),
    ]
