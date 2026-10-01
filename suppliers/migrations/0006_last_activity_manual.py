from datetime import date

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("suppliers", "0005_responsible_manager_fk"),
    ]

    operations = [
        migrations.AlterField(
            model_name="supplier",
            name="last_activity",
            field=models.DateField(
                blank=True,
                default=date.today,
                verbose_name="Последняя активность",
            ),
        ),
    ]