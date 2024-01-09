# Generated by Django 4.2.9 on 2024-01-09 02:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('juntagrico_assignment_request', '0005_alter_assignmentrequest_amount'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='assignmentrequest',
            options={'permissions': (('can_confirm_assignments', 'Kann selbständige Arbeitseinsätze bestätigen'), ('can_confirm_assignments_for_area', 'Kann selbständige Arbeitseinsätze im eigenen Tätigkeitsbereich bestätigen'), ('notified_on_unapproved_assignments', 'Wird über nicht abgesprochene Arbeitseinsätze informiert')), 'verbose_name': 'Arbeitseinsatz Anfrage', 'verbose_name_plural': 'Arbeitseinsatz Anfragen'},
        ),
    ]