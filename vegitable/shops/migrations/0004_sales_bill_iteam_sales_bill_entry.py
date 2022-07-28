# Generated by Django 4.0.5 on 2022-07-20 17:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shops', '0003_arrival_goods_iteam_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Sales_Bill_Iteam',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('iteam_name', models.CharField(max_length=10)),
                ('lot_number', models.CharField(max_length=50)),
                ('bags', models.CharField(max_length=50)),
                ('net_weight', models.FloatField(max_length=50)),
                ('rates', models.FloatField(max_length=50)),
                ('amount', models.FloatField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='Sales_Bill_Entry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('payment_type', models.CharField(max_length=10)),
                ('customer_name', models.CharField(max_length=50)),
                ('date', models.DateField()),
                ('rmc', models.FloatField(max_length=50)),
                ('commission', models.FloatField(max_length=50)),
                ('cooli', models.FloatField(max_length=50)),
                ('total_amount', models.FloatField(max_length=50)),
                ('shop', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='shops.shop')),
            ],
        ),
    ]