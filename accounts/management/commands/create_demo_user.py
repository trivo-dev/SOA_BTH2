from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from accounts.models import User


class Command(BaseCommand):
    help = "Create the local exercise account without resetting existing credentials."

    def handle(self, *args, **options):
        user, created = User.objects.get_or_create(
            UserName="admin",
            defaults={"Password": make_password("123456")},
        )
        self.stdout.write("Created admin / 123456" if created else "admin already exists; unchanged.")
