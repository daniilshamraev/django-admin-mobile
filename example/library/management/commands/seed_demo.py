from django.core.management.base import BaseCommand

from library.demo import seed_demo


class Command(BaseCommand):
    help = "Create demo books and a local admin user when ADMIN_MOBILE_DEMO is on."

    def handle(self, *args: object, **options: object) -> None:
        created = seed_demo()
        if created:
            self.stdout.write(self.style.SUCCESS("Demo library created."))
            return
        self.stdout.write("Demo seed skipped or already present.")
