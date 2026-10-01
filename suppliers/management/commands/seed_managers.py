from django.contrib.auth.models import Group, Permission, User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.utils.crypto import get_random_string

from suppliers.models import Manager

MANAGERS = [
    ("petrov", "Петров Пётр"),
    ("sidorova", "Сидорова Анна"),
    ("kozlov", "Козлов Дмитрий"),
    ("vasileva", "Васильева Ольга"),
    ("fedorov", "Фёдоров Игорь"),
]

MANAGER_GROUP = "Менеджеры"

SUPPLIER_PERMISSIONS = ["view_supplier", "change_supplier"]

ALPHABET = "abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"


class Command(BaseCommand):
    help = (
        "Создаёт пользователей-менеджеров, группу «Менеджеры» и привязывает их профили. "
        "Менеджеры не получают доступ к стандартной админке Django: is_staff=False, "
        "работают через /admin-panel/. Каждому новому менеджеру назначается собственный "
        "случайный пароль, который печатается один раз."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--password",
            help="общий пароль для всех создаваемых менеджеров (по умолчанию — случайный для каждого)",
        )
        parser.add_argument("--length", type=int, default=14, help="длина пароля")

    def handle(self, *args, **options):
        created_users = 0
        created_profiles = 0
        issued = []
        common = options["password"]
        if common:
            try:
                validate_password(common)
            except ValidationError as exc:
                raise CommandError(
                    "Пароль не проходит проверку: " + "; ".join(exc.messages)
                )

        group, _ = Group.objects.get_or_create(name=MANAGER_GROUP)
        permissions = list(
            Permission.objects.filter(
                codename__in=SUPPLIER_PERMISSIONS,
                content_type__app_label="suppliers",
            )
        )
        group.permissions.set(permissions)

        for username, full_name in MANAGERS:
            user, user_created = User.objects.get_or_create(
                username=username,
                defaults={
                    "is_staff": False,
                    "is_active": True,
                    "is_superuser": False,
                },
            )
            if user_created:
                raw = common or get_random_string(options["length"], ALPHABET)
                user.set_password(raw)
                user.save()
                created_users += 1
                issued.append((username, raw))
            else:
                user.is_staff = False
                user.is_superuser = False
                user.save()

            user.user_permissions.clear()
            user.groups.add(group)

            profile, profile_created = Manager.objects.get_or_create(
                user=user,
                defaults={"full_name": full_name},
            )
            if profile_created:
                created_profiles += 1
            else:
                profile.full_name = full_name
                profile.is_active = True
                profile.save()

        self.stdout.write(
            self.style.SUCCESS(
                f"Пользователей создано: {created_users}, профилей создано: {created_profiles}. "
                f"Группа «{MANAGER_GROUP}»: {group.permissions.count()} прав. "
                f"Всего менеджеров: {Manager.objects.count()}."
            )
        )
        if issued:
            if common:
                self.stdout.write(
                    f"Пароль «{common}» назначен {len(issued)} новым менеджерам."
                )
            else:
                self.stdout.write(self.style.SUCCESS("Пароли (показаны один раз):"))
                for username, raw in issued:
                    self.stdout.write(f"  {username:<12} {raw}")
