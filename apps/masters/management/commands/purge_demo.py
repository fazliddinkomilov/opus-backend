from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import User


# Phones created by `seed_demo`. Deleting the users cascades to their master
# profile, wallet, orders and offers.
DEMO_PHONES = ["+998901111111", "+998902222222"]


class Command(BaseCommand):
    help = "Delete demo/test users and their masters seeded by seed_demo (production cleanup)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--phones",
            nargs="*",
            default=DEMO_PHONES,
            help="Phone numbers to purge (defaults to the seed_demo demo accounts).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        phones = options["phones"]
        qs = User.objects.filter(phone__in=phones)
        found = list(qs.values_list("phone", flat=True))
        deleted, _ = qs.delete()
        if found:
            self.stdout.write(self.style.SUCCESS(f"Purged demo accounts: {', '.join(found)} ({deleted} rows)."))
        else:
            self.stdout.write("No demo accounts found; nothing to purge.")
