from django.db import migrations, models

import juntagrico_assignment_request.models


class Migration(migrations.Migration):

    dependencies = [
        ('juntagrico_assignment_request', '0006_alter_assignmentrequest_options'),
    ]

    operations = [
        # add without default first, such that existing requests do not share the same key.
        # Their old emails contain no key anyway.
        migrations.AddField(
            model_name='assignmentrequest',
            name='confirm_key',
            field=models.CharField(editable=False, max_length=64, null=True),
        ),
        migrations.AlterField(
            model_name='assignmentrequest',
            name='confirm_key',
            field=models.CharField(default=juntagrico_assignment_request.models.generate_confirm_key, editable=False,
                                   max_length=64, null=True),
        ),
    ]
