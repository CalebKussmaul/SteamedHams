# Generated by Django 2.1.3 on 2019-01-02 20:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('SteamedHamsFinal', '0002_auto_20181121_1959'),
    ]

    operations = [
        migrations.AlterField(
            model_name='submission',
            name='frame',
            field=models.IntegerField(db_index=True),
        ),
        migrations.AlterField(
            model_name='submission',
            name='id',
            field=models.AutoField(db_index=True, primary_key=True, serialize=False),
        ),
    ]
