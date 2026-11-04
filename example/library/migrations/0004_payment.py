from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("library", "0003_shelf_plural"),
    ]

    operations = [
        migrations.CreateModel(
            name="Payment",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "payer_name",
                    models.CharField(max_length=200, verbose_name="Имя плательщика"),
                ),
                ("vk_id", models.CharField(max_length=64, verbose_name="Профиль")),
                (
                    "amount",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=12,
                        verbose_name="Цена в рублях",
                    ),
                ),
                (
                    "system",
                    models.CharField(
                        choices=[
                            ("card", "Банковская карта"),
                            ("wallet", "Электронный кошелёк"),
                        ],
                        default="card",
                        max_length=20,
                        verbose_name="Платежная система",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        default="Ожидает",
                        max_length=40,
                        verbose_name="Статус платежа",
                    ),
                ),
                (
                    "paid_on",
                    models.DateField(
                        blank=True, null=True, verbose_name="Дата оплаты"
                    ),
                ),
                (
                    "external_id",
                    models.CharField(
                        blank=True,
                        max_length=80,
                        verbose_name="Внешний идентификатор",
                    ),
                ),
                (
                    "comment",
                    models.CharField(
                        blank=True,
                        max_length=200,
                        verbose_name="Комментарий кассира",
                    ),
                ),
                (
                    "currency",
                    models.CharField(
                        default="RUB",
                        max_length=12,
                        verbose_name="Валюта расчёта",
                    ),
                ),
                (
                    "reviewed",
                    models.BooleanField(default=False, verbose_name="Проверен"),
                ),
            ],
            options={
                "verbose_name": "Платёж",
                "verbose_name_plural": "Платежи",
                "ordering": ["-id"],
            },
        ),
    ]
