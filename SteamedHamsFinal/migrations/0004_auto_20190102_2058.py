# Generated by Django 2.1.3 on 2019-01-02 20:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('SteamedHamsFinal', '0003_auto_20190102_2056'),
    ]

    operations = [
        migrations.AlterField(
            model_name='submission',
            name='id',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
    ]
