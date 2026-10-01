from django.core.management.base import BaseCommand

from suppliers.models import STATUSES, Manager, Supplier


SURNAMES = [
    "Иванов", "Смирнов", "Кузнецов", "Попов", "Васильев",
    "Петров", "Соколов", "Михайлов", "Новиков", "Фёдоров",
    "Морозов", "Волков", "Алексеев", "Лебедев", "Семёнов",
    "Егоров", "Павлов", "Козлов", "Степанов", "Николаев",
    "Орлов", "Андреев", "Макаров", "Никитин", "Захаров",
    "Зайцев", "Соловьёв", "Борисов", "Яковлев", "Григорьев",
    "Романов", "Воробьёв", "Сергеев", "Фролов", "Александров",
    "Дмитриев", "Королёв", "Гусев", "Киселёв", "Ильин",
    "Максимов", "Поляков", "Сидоров", "Гаврилов", "Тихонов",
    "Казаков", "Афанасьев", "Данилов", "Савельев", "Титов",
]

NAMES = [
    "Александр", "Дмитрий", "Максим", "Сергей", "Андрей",
    "Алексей", "Артём", "Илья", "Кирилл", "Михаил",
    "Никита", "Матвей", "Роман", "Егор", "Иван",
    "Денис", "Евгений", "Павел", "Тимофей", "Владимир",
]

PATRONYMICS = [
    "Александрович", "Дмитриевич", "Сергеевич", "Андреевич", "Алексеевич",
    "Иванович", "Петрович", "Николаевич", "Михайлович", "Викторович",
    "Владимирович", "Юрьевич", "Олегович", "Васильевич", "Аркадьевич",
]

CITIES = [
    ("Москва", "Москва"),
    ("Санкт-Петербург", "Санкт-Петербург"),
    ("Новосибирск", "Новосибирская область"),
    ("Екатеринбург", "Свердловская область"),
    ("Казань", "Республика Татарстан"),
    ("Нижний Новгород", "Нижегородская область"),
    ("Челябинск", "Челябинская область"),
    ("Самара", "Самарская область"),
    ("Омск", "Омская область"),
    ("Ростов-на-Дону", "Ростовская область"),
    ("Уфа", "Республика Башкортостан"),
    ("Красноярск", "Красноярский край"),
    ("Воронеж", "Воронежская область"),
    ("Пермь", "Пермский край"),
    ("Волгоград", "Волгоградская область"),
    ("Тула", "Тульская область"),
    ("Иркутск", "Иркутская область"),
    ("Хабаровск", "Хабаровский край"),
    ("Владивосток", "Приморский край"),
    ("Ярославль", "Ярославская область"),
]

ORGANIZATIONS = [
    "ООО ПромСнаб", "ООО ТехноТрейд", "АО СтройРесурс", "ООО МеталлТорг",
    "ООО СибКомплект", "ООО УралОпт", "ЗАО ТехноИмпорт", "ООО СтройСервис",
    "ООО БизнесТрейд", "ООО ПромЭкспорт", "ИП Волков", "ООО ГидроТех",
    "ООО ЭнергоСнаб", "ООО ТД Вектор", "ООО КомплектПоставка",
    "АО ТПК Регион", "ООО СпецСтрой", "ООО ТеплоТех", "ООО ОптТорг",
    "ООО СтанкоИмпорт",
]

MANAGER_USERNAMES = [
    "petrov",
    "sidorova",
    "kozlov",
    "vasileva",
    "fedorov",
]

AREA_CODES = ["495", "812", "383", "343", "843", "831", "351", "846", "3812", "863", "347", "391", "473", "342", "8442", "4872", "3952", "4212", "423", "4852"]


class Command(BaseCommand):
    help = "Добавляет 50 заказчиков в базу данных (до общей суммы 50)"

    def handle(self, *args, **options):
        current = Supplier.objects.count()
        need = 50 - current
        if need <= 0:
            self.stdout.write(self.style.WARNING(f"Уже 50+ заказчиков ({current}). Ничего не добавлено."))
            return

        managers = list(
            Manager.objects.filter(
                user__username__in=MANAGER_USERNAMES, is_active=True
            ).select_related("user")
        )
        if not managers:
            self.stdout.write(
                self.style.ERROR(
                    "Нет активных менеджеров. Сначала выполните: python manage.py seed_managers"
                )
            )
            return

        created = 0
        for i in range(need):
            idx = current + i
            surname = SURNAMES[idx % len(SURNAMES)]
            name = NAMES[idx % len(NAMES)]
            patronymic = PATRONYMICS[idx % len(PATRONYMICS)]
            city, region = CITIES[idx % len(CITIES)]
            area_code = AREA_CODES[idx % len(AREA_CODES)]
            org = ORGANIZATIONS[idx % len(ORGANIZATIONS)]
            manager = managers[idx % len(managers)]
            status = STATUSES[idx % len(STATUSES)][0]

            email_domain = org.lower().replace(" ", "").replace("ооо", "").replace("ао", "").replace("зао", "").replace("ип", "").replace(".", "") or "company"
            email_user = f"{surname.lower()}{name.lower()[:1]}{patronymic.lower()[:1]}"

            Supplier.objects.create(
                full_name=f"{surname} {name} {patronymic}",
                region=region,
                city=city,
                organization=org,
                phone=f"+7-{area_code}-{100 + (idx % 800):03d}-{10 + (idx % 80):02d}-{10 + (idx % 80):02d}",
                email=f"{email_user}@{email_domain}.ru",
                status=status,
                responsible_manager=manager,
                is_active=(idx % 5 != 0),
            )
            created += 1

        self.stdout.write(self.style.SUCCESS(f"Добавлено заказчиков: {created}. Всего: {Supplier.objects.count()}."))