# Generated by Django 2.1.5 on 2019-04-04 12:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0007_auto_20190403_1917'),
    ]

    operations = [
        migrations.AddField(
            model_name='shiftpreference',
            name='period',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='main.Period'),
        ),
    ]
