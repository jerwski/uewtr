# Generated by Django 2.1.7 on 2019-02-20 17:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cashregister', '0003_auto_20190220_1649'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='cashregister',
            options={'ordering': ['-date']},
        ),
    ]