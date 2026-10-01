import random
from datetime import date, timedelta

from django.core.management.base import BaseCommand

from suppliers.models import Supplier


class Command(BaseCommand):
    help = (
        "Искусственно «состаривает» last_activity у всех заказчиков. 30% — старше 3 месяцев. "
        "Демо-команда: перезаписывает реальные отметки активности."
    )

    def handle(self, *args, **options):
        ids = list(Supplier.objects.values_list("pk", flat=True))
        random.shuffle(ids)
        if not ids:
            self.stdout.write("Заказчиков нет.")
            return

        old = int(len(ids) * 0.3)
        today = date.today()

        old_ids = ids[:old]
        recent_ids = ids[old:]

        old_map = {pk: today - timedelta(days=random.randint(120, 240)) for pk in old_ids}
        recent_map = {pk: today - timedelta(days=random.randint(1, 85)) for pk in recent_ids}

        for pk, dt in old_map.items():
            Supplier.objects.filter(pk=pk).update(last_activity=dt)
        for pk, dt in recent_map.items():
            Supplier.objects.filter(pk=pk).update(last_activity=dt)

        self.stdout.write(self.style.SUCCESS(
            f"Обновлено заказчиков: {len(ids)} (старше 3 мес: {len(old_ids)}, свежие: {len(recent_ids)})."
        ))