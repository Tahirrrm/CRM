import django.db.models.deletion
from django.db import migrations, models


def copy_managers(apps, schema_editor):
    Supplier = apps.get_model("suppliers", "Supplier")
    Manager = apps.get_model("suppliers", "Manager")

    by_name = {}
    for manager in Manager.objects.all():
        by_name.setdefault(manager.full_name, manager)

    db_alias = schema_editor.connection.alias

    for supplier in Supplier.objects.using(db_alias).exclude(
        responsible_manager=""
    ).exclude(responsible_manager__isnull=True):
        manager = by_name.get(supplier.responsible_manager)
        supplier.responsible_manager_new_id = manager.id if manager else None
        supplier.save(update_fields=["responsible_manager_new"])


def copy_back(apps, schema_editor):
    Supplier = apps.get_model("suppliers", "Supplier")
    Manager = apps.get_model("suppliers", "Manager")

    names = {m.id: m.full_name for m in Manager.objects.all()}
    db_alias = schema_editor.connection.alias

    for supplier in Supplier.objects.using(db_alias).exclude(
        responsible_manager_new__isnull=True
    ):
        supplier.responsible_manager = names.get(supplier.responsible_manager_new_id, "")
        supplier.save(update_fields=["responsible_manager"])


class Migration(migrations.Migration):

    dependencies = [
        ("suppliers", "0004_alter_supplier_options"),
    ]

    operations = [
        migrations.AddField(
            model_name="supplier",
            name="responsible_manager_new",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="suppliers.manager",
            ),
        ),
        migrations.RunPython(copy_managers, copy_back),
        migrations.RemoveField(
            model_name="supplier",
            name="responsible_manager",
        ),
        migrations.RenameField(
            model_name="supplier",
            old_name="responsible_manager_new",
            new_name="responsible_manager",
        ),
        migrations.AlterField(
            model_name="supplier",
            name="responsible_manager",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="suppliers",
                to="suppliers.manager",
                verbose_name="Ответственный менеджер",
            ),
        ),
    ]