from django.db import migrations, models

OLD_TO_NEW = {
    "новый": "new",
    "контакт установлен": "contact",
    "переговоры": "negotiation",
    "принимается решение": "decision",
    "заказ": "order",
    "оплачено": "paid",
}

NEW_TO_OLD = {new: old for old, new in OLD_TO_NEW.items()}


def to_keys(apps, schema_editor):
    Supplier = apps.get_model("suppliers", "Supplier")
    db_alias = schema_editor.connection.alias
    for old, new in OLD_TO_NEW.items():
        Supplier.objects.using(db_alias).filter(status=old).update(status=new)


def to_words(apps, schema_editor):
    Supplier = apps.get_model("suppliers", "Supplier")
    db_alias = schema_editor.connection.alias
    for new, old in NEW_TO_OLD.items():
        Supplier.objects.using(db_alias).filter(status=new).update(status=old)


class Migration(migrations.Migration):
    dependencies = [
        ("suppliers", "0007_no_null_text_fields"),
    ]

    operations = [
        migrations.AlterField(
            model_name="supplier",
            name="status",
            field=models.CharField(
                choices=[
                    ("new", "новый"),
                    ("contact", "контакт установлен"),
                    ("negotiation", "переговоры"),
                    ("decision", "принимается решение"),
                    ("order", "заказ"),
                    ("paid", "оплачено"),
                ],
                default="new",
                max_length=50,
                verbose_name="Статус",
            ),
        ),
        migrations.RunPython(to_keys, to_words),
    ]