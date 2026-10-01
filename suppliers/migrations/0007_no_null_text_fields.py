from django.db import migrations, models

TEXT_FIELDS = ["region", "city", "organization", "phone", "email"]


def nulls_to_empty_strings(apps, schema_editor):
    Supplier = apps.get_model("suppliers", "Supplier")
    db_alias = schema_editor.connection.alias
    for field in TEXT_FIELDS:
        Supplier.objects.using(db_alias).filter(**{f"{field}__isnull": True}).update(
            **{field: ""}
        )


def empty_strings_to_nulls(apps, schema_editor):
    Supplier = apps.get_model("suppliers", "Supplier")
    db_alias = schema_editor.connection.alias
    for field in TEXT_FIELDS:
        Supplier.objects.using(db_alias).filter(**{field: ""}).update(
            **{field: None}
        )


class Migration(migrations.Migration):

    dependencies = [
        ("suppliers", "0006_last_activity_manual"),
    ]

    operations = [
        migrations.RunPython(nulls_to_empty_strings, empty_strings_to_nulls),
        migrations.AlterField(
            model_name="supplier",
            name="region",
            field=models.CharField(blank=True, default="", max_length=255, verbose_name="Регион"),
        ),
        migrations.AlterField(
            model_name="supplier",
            name="city",
            field=models.CharField(blank=True, default="", max_length=255, verbose_name="Город"),
        ),
        migrations.AlterField(
            model_name="supplier",
            name="organization",
            field=models.CharField(blank=True, default="", max_length=255, verbose_name="Организация"),
        ),
        migrations.AlterField(
            model_name="supplier",
            name="phone",
            field=models.CharField(blank=True, default="", max_length=50, verbose_name="Телефон"),
        ),
        migrations.AlterField(
            model_name="supplier",
            name="email",
            field=models.EmailField(blank=True, default="", verbose_name="e-mail"),
        ),
    ]