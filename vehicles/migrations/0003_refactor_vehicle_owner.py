from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('vehicles', '0002_inspection_confidence'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Add user field to Inspection
        migrations.AddField(
            model_name='inspection',
            name='user',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        # Remove owner from Vehicle
        migrations.RemoveField(
            model_name='vehicle',
            name='owner',
        ),
    ]
