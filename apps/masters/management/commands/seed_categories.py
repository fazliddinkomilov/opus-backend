from django.core.management.base import BaseCommand

from apps.masters.models import ServiceCategory


CATEGORIES = [
    ("electrician", "Электрик", "Elektrik", "⚡", "#F5A623"),
    ("plumber", "Сантехник", "Santexnik", "🚿", "#2D9CDB"),
    ("ac_technician", "Кондиционерщик", "Konditsioner ustasi", "❄", "#56CCF2"),
    ("painter", "Маляр", "Bo'yoqchi", "🖌", "#BB6BD9"),
    ("tiler", "Плиточник", "Plitkachi", "▦", "#27AE60"),
    ("furniture", "Мебельщик", "Mebel ustasi", "▣", "#8D6E63"),
    ("mover", "Грузчик", "Yuk tashuvchi", "□", "#F2994A"),
    ("cleaner", "Уборщик", "Tozalovchi", "◎", "#6FCF97"),
    ("locksmith", "Замочник", "Qulf ustasi", "🔐", "#4F4F4F"),
    ("computer_master", "Компьютерный мастер", "Kompyuter ustasi", "💻", "#2F80ED"),
    ("handyman", "Разнорабочий", "Har xil ish ustasi", "🛠", "#828282"),
    ("welder", "Сварщик", "Payvandchi", "⌁", "#EB5757"),
    ("gardener", "Садовник", "Bog'bon", "🌱", "#219653"),
    ("digger", "Копалщик", "Yer qazuvchi", "◌", "#795548"),
]


class Command(BaseCommand):
    help = "Seed MasterGo service categories from the PRD."

    def handle(self, *args, **options):
        for sort_order, (slug, name_ru, name_uz, icon, color_hex) in enumerate(CATEGORIES, start=1):
            ServiceCategory.objects.update_or_create(
                slug=slug,
                defaults={
                    "name_ru": name_ru,
                    "name_uz": name_uz,
                    "icon": icon,
                    "color_hex": color_hex,
                    "sort_order": sort_order,
                    "is_active": True,
                },
            )
        self.stdout.write(self.style.SUCCESS(f"Seeded {len(CATEGORIES)} service categories."))

