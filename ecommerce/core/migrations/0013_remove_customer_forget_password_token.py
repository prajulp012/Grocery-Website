# Generated by Django 4.2.1 on 2023-06-25 01:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_customer_forget_password_token'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customer',
            name='forget_password_token',
        ),
    ]
