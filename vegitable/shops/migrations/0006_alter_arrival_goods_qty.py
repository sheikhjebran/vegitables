# Generated by Django 4.0.5 on 2022-07-27 16:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shops', '0005_sales_bill_iteam_sales_bill_entry'),
    ]

    operations = [
        migrations.AlterField(
            model_name='arrival_goods',
            name='qty',
            field=models.CharField(max_length=100),
        ),
    ]