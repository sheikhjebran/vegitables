# Generated by Django 4.0.5 on 2022-07-31 06:08

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Arrival_Entry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('gp_no', models.CharField(max_length=100)),
                ('lorry_no', models.CharField(default='', max_length=100)),
                ('date', models.DateField()),
                ('patti_name', models.CharField(max_length=50)),
                ('total_bags', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Arrival_Goods',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('former_name', models.CharField(max_length=50)),
                ('qty', models.CharField(max_length=100)),
                ('weight', models.FloatField(max_length=100)),
                ('remarks', models.CharField(max_length=50)),
                ('iteam_name', models.CharField(max_length=100)),
                ('advance', models.FloatField(default=0, max_length=100)),
                ('arrival_entry', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='shops.arrival_entry')),
            ],
        ),
        migrations.CreateModel(
            name='Patti_entry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('lorry_no', models.CharField(max_length=100)),
                ('date', models.DateField()),
                ('advance', models.FloatField(max_length=100)),
                ('farmer_name', models.CharField(max_length=100)),
                ('total_weight', models.FloatField(max_length=100)),
                ('hamali', models.FloatField(max_length=100)),
                ('net_amount', models.FloatField(max_length=100)),
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
            ],
        ),
        migrations.CreateModel(
            name='Shop',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('shop_name', models.CharField(max_length=50)),
                ('shop_location', models.CharField(max_length=255)),
                ('shop_address', models.CharField(max_length=255)),
                ('shop_owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Sales_Bill_Iteam',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('iteam_name', models.CharField(max_length=10)),
                ('bags', models.CharField(max_length=50)),
                ('net_weight', models.FloatField(max_length=50)),
                ('rates', models.FloatField(max_length=50)),
                ('amount', models.FloatField(max_length=50)),
                ('Sales_Bill_Entry', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='shops.sales_bill_entry')),
                ('arrival_goods', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='shops.arrival_goods')),
            ],
        ),
        migrations.AddField(
            model_name='sales_bill_entry',
            name='shop',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='shops.shop'),
        ),
        migrations.CreateModel(
            name='Patti_entry_list',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('iteam', models.CharField(max_length=100)),
                ('lot_no', models.CharField(max_length=100)),
                ('weight', models.CharField(max_length=100)),
                ('rate', models.CharField(max_length=100)),
                ('amount', models.FloatField(max_length=100)),
                ('patti', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='shops.patti_entry')),
            ],
        ),
        migrations.AddField(
            model_name='patti_entry',
            name='shop',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='shops.shop'),
        ),
        migrations.CreateModel(
            name='Misc_Entry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('expense_type', models.CharField(max_length=50)),
                ('amount', models.FloatField(max_length=100)),
                ('remark', models.CharField(max_length=255)),
                ('shop', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='shops.shop')),
            ],
        ),
        migrations.AddField(
            model_name='arrival_goods',
            name='shop',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='shops.shop'),
        ),
        migrations.AddField(
            model_name='arrival_entry',
            name='shop',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='shops.shop'),
        ),
    ]
