from datetime import date

from django.conf import settings
from django.db import models


STATUSES = [
    ("новый", "новый"),
    ("контакт установлен", "контакт установлен"),
    ("переговоры", "переговоры"),
    ("принимается решение", "принимается решение"),
    ("заказ", "заказ"),
    ("оплачено", "оплачено"),
]


class Supplier(models.Model):
    full_name = models.CharField("ФИО", max_length=255)
    region = models.CharField("Регион", max_length=255, blank=True, default="")
    city = models.CharField("Город", max_length=255, blank=True, default="")
    organization = models.CharField("Организация", max_length=255, blank=True, default="")
    phone = models.CharField("Телефон", max_length=50, blank=True, default="")
    email = models.EmailField("e-mail", blank=True, default="")
    status = models.CharField("Статус", max_length=50, choices=STATUSES, default="новый")
    responsible_manager = models.ForeignKey(
        "suppliers.Manager",
        verbose_name="Ответственный менеджер",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="suppliers",
    )
    is_active = models.BooleanField("Активен", default=True)
    created_at = models.DateField("Дата создания", auto_now_add=True)
    last_activity = models.DateField(
        "Последняя активность",
        default=date.today,
        blank=True,
    )

    class Meta:
        verbose_name = "Заказчик"
        verbose_name_plural = "Заказчики"
        ordering = ["id"]

    def __str__(self):
        return self.full_name

    def mark_active(self, when=None):
        self.last_activity = when or date.today()
        self.save(update_fields=["last_activity"])


class Manager(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
        related_name="manager_profile",
    )
    full_name = models.CharField("ФИО менеджера", max_length=255, unique=True)
    is_active = models.BooleanField("Работает", default=True)

    class Meta:
        verbose_name = "Менеджер"
        verbose_name_plural = "Менеджеры"
        ordering = ["full_name"]

    def __str__(self):
        return self.full_name


class CalendarNote(models.Model):
    date = models.DateField("Дата")
    text = models.TextField("Заметка")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Автор",
        related_name="calendar_notes",
    )
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        verbose_name = "Заметка календаря"
        verbose_name_plural = "Заметки календаря"
        ordering = ["date", "-created_at"]

    def __str__(self):
        return f"{self.date}: {self.text[:50]}"
