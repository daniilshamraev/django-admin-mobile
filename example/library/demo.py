"""Demo rows for the example project.

The known password is created only when both DEBUG and ADMIN_MOBILE_DEMO are
set. Never enable ADMIN_MOBILE_DEMO on a shared host.
"""

from __future__ import annotations

from datetime import date, datetime, time

from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone


def seed_demo(*args: object, **kwargs: object) -> bool:
    if not settings.DEBUG or not getattr(settings, "ADMIN_MOBILE_DEMO", False):
        return False

    from django.contrib.auth import get_user_model

    from library.models import (
        Appointment,
        Author,
        Book,
        Chapter,
        Citation,
        Edition,
        Payment,
        Publisher,
        Revision,
        Series,
        Shelf,
        Tag,
    )

    user_model = get_user_model()
    if not user_model.objects.filter(username="admin").exists():
        user_model.objects.create_superuser("admin", "admin@example.com", "admin")

    if Author.objects.exists():
        return False

    lovelace = Author.objects.create(name="Ada Lovelace", birth_date=date(1815, 12, 10))
    hopper = Author.objects.create(name="Grace Hopper", birth_date=date(1906, 12, 9))
    knuth = Author.objects.create(name="Donald Knuth", birth_date=date(1938, 1, 10))

    notes = Book.objects.create(
        title="Notes on the Analytical Engine",
        author=lovelace,
        status=Book.Status.PUBLISHED,
        published_on=date(1843, 8, 1),
        reading_time=time(21, 30),
        scheduled_for=timezone.make_aware(datetime(2026, 3, 14, 18, 0)),
        pages=96,
        notes="Margin notes translated beside the memoir.",
    )
    Chapter.objects.create(
        book=notes,
        title="Translator's notes",
        order=1,
        starts_at=time(21, 30),
        word_count=4200,
    )
    Chapter.objects.create(
        book=notes,
        title="Note G",
        order=2,
        starts_at=time(22, 15),
        word_count=1800,
    )

    compiler = Book.objects.create(
        title="The First Compiler",
        author=hopper,
        status=Book.Status.DRAFT,
        published_on=date(1952, 5, 3),
        reading_time=time(7, 45),
        pages=240,
    )
    Chapter.objects.create(
        book=compiler,
        title="A-0 system",
        order=1,
        starts_at=time(8, 0),
        word_count=3100,
    )

    Book.objects.create(
        title="Concrete Mathematics",
        author=knuth,
        status=Book.Status.PUBLISHED,
        published_on=date(1989, 2, 1),
        reading_time=time(6, 15),
        pages=672,
    )
    Book.objects.create(
        title="The Art of Computer Programming, Vol. 1",
        author=knuth,
        status=Book.Status.ARCHIVED,
        published_on=date(1968, 1, 1),
        pages=634,
    )

    press = Publisher.objects.create(name="Local Press")
    series = Series.objects.create(name="Computing Classics")
    margin = Tag.objects.create(name="Margin notes", slug="margin-notes")
    primary = Shelf.objects.create(name="Reading room")
    edition = Edition.objects.create(
        book=notes,
        publisher=press,
        series=series,
        title="Notes, second printing",
        slug="notes-second-printing",
        format=Edition.Format.PAPER,
        featured=True,
        published_on=date(1843, 8, 1),
        notes="Kept for the empty-filter counterpart on other editions.",
    )
    edition.tags.add(margin)
    edition.shelves.add(primary)
    edition.manuscript.save("memo.txt", ContentFile(b"Local demo file.\n"), save=True)
    Citation.objects.create(
        edition=edition,
        quote="The Analytical Engine weaves algebraical patterns.",
        page=1,
        order=1,
    )
    Revision.objects.create(
        book=notes, label="Proof 1", ready=True, note="Margins checked"
    )
    Revision.objects.create(
        book=notes, label="Proof 2", ready=False, note="Awaiting plates"
    )
    Revision.objects.create(
        book=compiler, label="Draft A", ready=False, note="Incomplete"
    )
    Appointment.objects.create(
        title="Reading hour",
        on_date=date(2026, 4, 2),
        at_time=time(18, 30),
        when=timezone.make_aware(datetime(2026, 4, 2, 18, 30)),
    )
    Payment.objects.create(
        payer_name="Мария Александровна Волконская",
        vk_id="123456789012345678",
        amount="1490.50",
        system=Payment.System.WALLET,
        status="Оплачен",
        paid_on=date(2026, 3, 2),
        external_id="pay-1843-notes",
        comment="Перевод за второе издание",
        currency="RUB",
    )
    return True
