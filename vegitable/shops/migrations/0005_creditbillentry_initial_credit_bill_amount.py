# Generated by Django 5.1 on 2024-08-29 17:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shops', '0004_rename_arrival_entry_arrivalentry_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='creditbillentry',
            name='initial_credit_bill_amount',
            field=models.FloatField(default=0, max_length=100),
            preserve_default=False,
        ),
    ]
