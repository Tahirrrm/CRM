from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.utils.crypto import get_random_string

ALPHABET = "abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def validate(raw):
    try:
        validate_password(raw)
    except ValidationError as exc:
        raise CommandError("Пароль не проходит проверку: " + "; ".join(exc.messages))


class Command(BaseCommand):
    help = (
        "Назначает пароли менеджерам. По умолчанию каждому менеджеру генерируется "
        "свой случайный пароль и печатается один раз."
    )

    def add_arguments(self, parser):
        parser.add_argument("usernames", nargs="*", help="логины (по умолчанию — все менеджеры)")
        parser.add_argument(
            "--password",
            help="один общий пароль для всех указанных. Без этой опции каждому свой",
        )
        parser.add_argument(
            "--random",
            action="store_true",
            help="принудительно сгенерировать новый пароль каждому",
        )
        parser.add_argument(
            "--length", type=int, default=14, help="длина генерируемого пароля"
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="только показать, что изменится",
        )

    def handle(self, *args, **options):
        common = options["password"]
        if common:
            validate(common)

        qs = User.objects.filter(is_superuser=False)
        if options["usernames"]:
            found = qs.filter(username__in=options["usernames"])
            missing = set(options["usernames"]) - {u.username for u in found}
            if missing:
                raise CommandError("Не найдены менеджеры: " + ", ".join(sorted(missing)))
        else:
            found = qs.filter(groups__name="Менеджеры").distinct()

        if not found:
            raise CommandError("Менеджеры не найдены. Выполните seed_managers.")

        results = []
        for user in found.order_by("username"):
            if common:
                raw = common
            else:
                raw = get_random_string(options["length"], ALPHABET)
                user.set_password(raw)
                user.save()
            results.append((user.username, raw))

        if options["dry_run"]:
            self.stdout.write(self.style.WARNING("DRY RUN — изменения не сохранены"))

        if common:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Пароль «{common}» назначен: {len(results)} менеджерам: "
                    + ", ".join(u for u, _ in results)
                )
            )
        else:
            self.stdout.write(self.style.SUCCESS("Пароли (показаны один раз):"))
            for username, raw in results:
                self.stdout.write(f"  {username:<12} {raw}")