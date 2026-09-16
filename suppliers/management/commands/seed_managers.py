from django.contrib.auth.models import Permission, User
from django.core.management.base import BaseCommand

from suppliers.models import Manager

MANAGERS = [
    ("petrov", "Петров Пётр"),
    ("sidorova", "Сидорова Анна"),
    ("kozlov", "Козлов Дмитрий"),
    ("vasileva", "Васильева Ольга"),
    ("fedorov", "Фёдоров Игорь"),
]

DEFAULT_PASSWORD = "manager123"

SUPPLIER_PERMISSIONS = ["view_supplier", "change_supplier"]


class Command(BaseCommand):
    help = "Создаёт пользователей-менеджеров и привязывает их профили"

    def handle(self, *args, **options):
        created_users = 0
        created_profiles = 0
        permissions = list(
            Permission.objects.filter(
                codename__in=SUPPLIER_PERMISSIONS,
                content_type__app_label="suppliers",
            )
        )
        for username, full_name in MANAGERS:
            user, user_created = User.objects.get_or_create(
                username=username,
                defaults={
                    "is_staff": True,
                    "is_active": True,
                },
            )
            if user_created:
                user.set_password(DEFAULT_PASSWORD)
                user.save()
                created_users += 1
            elif not user.is_staff:
                user.is_staff = True
                user.save()

            user.user_permissions.set(permissions)

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
                f"Всего менеджеров: {Manager.objects.count()}. Пароль по умолчанию: {DEFAULT_PASSWORD}"
            )
        )