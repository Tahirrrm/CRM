from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.utils.crypto import get_random_string

ALPHABET = "abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"
MIN_LENGTH = 8


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
            help="принудительно сгенерировать новый пароль каждому (поведение по умолчанию)",
        )
        parser.add_argument(
            "--length", type=int, default=14, help="длина генерируемого пароля"
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="только показать, что изменится; пароли НЕ сохраняются",
        )

    def handle(self, *args, **options):
        common = options["password"]
        dry_run = options["dry_run"]

        if common and options["random"]:
            raise CommandError("Нельзя одновременно использовать --password и --random.")
        if options["length"] < MIN_LENGTH:
            raise CommandError(f"--length должен быть не меньше {MIN_LENGTH}.")
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
            if not dry_run:
                user.set_password(raw)
                user.save(update_fields=["password"])
            results.append((user.username, raw))

        if dry_run:
            self.stdout.write(
                self.style.WARNING("DRY RUN — пароли НЕ изменены, ничего не сохранено")
            )
            if common:
                for username, _ in results:
                    self.stdout.write(f"  {username:<12} будет установлен пароль «{common}»")
            else:
                for username, _ in results:
                    self.stdout.write(
                        f"  {username:<12} будет сгенерирован новый пароль "
                        f"({options['length']} символов)"
                    )
            return

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