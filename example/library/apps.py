from django.apps import AppConfig


class LibraryConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "library"

    def ready(self) -> None:
        from django.db.models.signals import post_migrate

        from library.demo import seed_demo

        post_migrate.connect(seed_demo, sender=self, dispatch_uid="library.seed_demo")
