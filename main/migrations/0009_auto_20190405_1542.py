# Generated by Django 2.1.5 on 2019-04-05 15:42

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('people', '0006_classroom_solicits_preferences'),
        ('main', '0008_shiftpreference_period'),
    ]

    operations = [
        migrations.CreateModel(
            name='ShiftAssignmentCollection',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(default=django.utils.timezone.now)),
                ('period', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.Period')),
            ],
        ),
        migrations.RemoveField(
            model_name='shiftassignment',
            name='period',
        ),
        migrations.AlterUniqueTogether(
            name='shiftpreference',
            unique_together={('child', 'shift', 'period')},
        ),
        migrations.AddField(
            model_name='shiftassignment',
            name='collection',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='main.ShiftAssignmentCollection'),
        ),
    ]
