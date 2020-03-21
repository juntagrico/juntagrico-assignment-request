# Generated by Django 2.2.4 on 2019-10-20 22:07

import datetime
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('juntagrico', '0018_auto_20191019_2031'),
    ]

    operations = [
        migrations.CreateModel(
            name='AssignmentRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.PositiveIntegerField(default=1, validators=[django.core.validators.MinValueValidator(1)], verbose_name='Wert')),
                ('job_time', models.DateTimeField(default=datetime.datetime.now, verbose_name='Geleistet am')),
                ('request_date', models.DateField(blank=True, default=datetime.date.today, null=True, verbose_name='Beantragt am')),
                ('description', models.TextField(default='', max_length=1000, verbose_name='Beschreibung')),
                ('duration', models.PositiveIntegerField(default=4, verbose_name='Dauer in Stunden')),
                ('location', models.CharField(blank=True, default='', max_length=100, verbose_name='Ort')),
                ('status', models.CharField(choices=[('RE', 'Beantragt'), ('NO', 'Abgelehnt'), ('CO', 'Bestätigt')], default='RE', max_length=2)),
                ('response', models.TextField(blank=True, null=True, verbose_name='Antwort')),
                ('activityarea', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='juntagrico.ActivityArea')),
                ('assignment', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='juntagrico.Assignment')),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='juntagrico.Member')),
                ('approver', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='Referenz', to='juntagrico.Member')),
                ('response_date', models.DateField(blank=True, null=True, verbose_name='Beantwortet am')),
            ],
            options={
                'verbose_name': 'Arbeitseinsatz Anfrage',
                'verbose_name_plural': 'Arbeitseinsatz Anfragen',
                'permissions': (('can_confirm_assignments', 'Kann selbständige Arbeitseinsätze bestätigen'), ('notified_on_unapproved_assignments', 'Wird über nicht abgesprochene Arbeitseinsätze informiert')),
            },
        ),
    ]
