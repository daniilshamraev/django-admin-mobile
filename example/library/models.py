from django.db import models


class Author(models.Model):
    name = models.CharField(max_length=120)
    birth_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Book(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    title = models.CharField(max_length=200)
    author = models.ForeignKey(Author, on_delete=models.PROTECT, related_name="books")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    published_on = models.DateField(null=True, blank=True)
    reading_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Typical time you sit down with this book.",
    )
    scheduled_for = models.DateTimeField(null=True, blank=True)
    pages = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["title"]

    def __str__(self) -> str:
        return self.title


class Publisher(models.Model):
    name = models.CharField(max_length=120)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Series(models.Model):
    name = models.CharField(max_length=120)

    class Meta:
        verbose_name_plural = "series"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=80)
    slug = models.SlugField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Shelf(models.Model):
    name = models.CharField(max_length=80)

    class Meta:
        verbose_name_plural = "shelves"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Edition(models.Model):
    class Format(models.TextChoices):
        PAPER = "paper", "Paper"
        EBOOK = "ebook", "Ebook"

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="editions")
    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.PROTECT,
        related_name="editions",
    )
    series = models.ForeignKey(
        Series,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="editions",
    )
    title = models.CharField(max_length=200)
    slug = models.SlugField(blank=True)
    format = models.CharField(
        max_length=20, choices=Format.choices, default=Format.PAPER
    )
    featured = models.BooleanField(default=False)
    tags = models.ManyToManyField(Tag, blank=True)
    shelves = models.ManyToManyField(Shelf, blank=True)
    published_on = models.DateField(null=True, blank=True)
    cover = models.FileField(upload_to="covers/", blank=True)
    manuscript = models.FileField(upload_to="manuscripts/", blank=True)
    notes = models.TextField(
        blank=True,
        help_text="Cataloguer's note. Leave this empty to exercise the empty filter.",
    )
    internal_code = models.CharField(max_length=40, blank=True, editable=False)

    class Meta:
        ordering = ["title"]

    def __str__(self) -> str:
        return self.title

    def save(self, *args: object, **kwargs: object) -> None:
        if not self.internal_code:
            self.internal_code = "ED-LOCAL"
        super().save(*args, **kwargs)


class Citation(models.Model):
    edition = models.ForeignKey(
        Edition, on_delete=models.CASCADE, related_name="citations"
    )
    quote = models.TextField()
    page = models.PositiveIntegerField(default=1)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return self.quote[:40]


class Revision(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="revisions")
    label = models.CharField(max_length=80)
    ready = models.BooleanField(default=False)
    note = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return self.label


class Payment(models.Model):
    """Long Russian labels, rich HTML, and an editable price."""

    class System(models.TextChoices):
        CARD = "card", "Банковская карта"
        WALLET = "wallet", "Электронный кошелёк"

    payer_name = models.CharField("Имя плательщика", max_length=200)
    vk_id = models.CharField("Профиль", max_length=64)
    amount = models.DecimalField("Цена в рублях", max_digits=12, decimal_places=2)
    system = models.CharField(
        "Платежная система",
        max_length=20,
        choices=System.choices,
        default=System.CARD,
    )
    status = models.CharField("Статус платежа", max_length=40, default="Ожидает")
    paid_on = models.DateField("Дата оплаты", null=True, blank=True)
    external_id = models.CharField("Внешний идентификатор", max_length=80, blank=True)
    comment = models.CharField("Комментарий кассира", max_length=200, blank=True)
    currency = models.CharField("Валюта расчёта", max_length=12, default="RUB")
    reviewed = models.BooleanField("Проверен", default=False)

    class Meta:
        verbose_name = "Платёж"
        verbose_name_plural = "Платежи"
        ordering = ["-id"]

    def __str__(self) -> str:
        return self.payer_name


class Appointment(models.Model):
    """Kept on Django's calendar and clock widgets (no native date mixin)."""

    title = models.CharField(max_length=120)
    on_date = models.DateField()
    at_time = models.TimeField()
    when = models.DateTimeField()

    class Meta:
        ordering = ["on_date", "id"]

    def __str__(self) -> str:
        return self.title


class Chapter(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="chapters")
    title = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=1)
    starts_at = models.TimeField(null=True, blank=True)
    word_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return self.title
