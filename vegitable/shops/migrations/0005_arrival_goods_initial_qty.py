# Generated by Django 4.2.1 on 2023-06-15 19:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shops', '0004_rename_misc_entry_expenditure_entry'),
    ]

    operations = [
        migrations.AddField(
            model_name='arrival_goods',
            name='initial_qty',
            field=models.IntegerField(default=10),
            preserve_default=False,
        ),
    ]