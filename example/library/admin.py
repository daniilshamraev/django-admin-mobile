from __future__ import annotations

from django.contrib import admin

from admin_mobile.mixins import MobileAdminMixin
from library.models import (
    Appointment,
    Author,
    Book,
    Chapter,
    Citation,
    Edition,
    Publisher,
    Revision,
    Series,
    Shelf,
    Tag,
)


class ChapterInline(MobileAdminMixin, admin.TabularInline):
    model = Chapter
    extra = 1
    fields = ("title", "order", "starts_at", "word_count")


class CitationInline(admin.StackedInline):
    model = Citation
    extra = 1
    fields = ("quote", "page", "order")


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ("name", "birth_date")
    search_fields = ("name",)


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(Series)
class SeriesAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(Tag)
class TagAdmin(MobileAdminMixin, admin.ModelAdmin):
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    mobile_readonly = True


@admin.register(Shelf)
class ShelfAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(Book)
class BookAdmin(MobileAdminMixin, admin.ModelAdmin):
    list_display = ("title", "author", "status", "published_on", "pages")
    list_filter = (
        "status",
        "author",
        "published_on",
        ("notes", admin.EmptyFieldListFilter),
    )
    date_hierarchy = "published_on"
    list_per_page = 1
    search_fields = ("title", "author__name")
    inlines = (ChapterInline,)
    mobile_card_title = "title"
    mobile_card_subtitle = "author"
    mobile_list_display = ("status", "published_on")
    fieldsets = (
        (None, {"fields": ("title", "author", "status", "pages")}),
        ("Schedule", {"fields": ("published_on", "reading_time", "scheduled_for")}),
        ("Notes", {"fields": ("notes",)}),
    )


@admin.register(Edition)
class EditionAdmin(MobileAdminMixin, admin.ModelAdmin):
    list_display = ("title", "publisher", "format", "featured", "published_on")
    list_filter = (
        "format",
        "featured",
        "publisher",
        "published_on",
        "tags",
        ("notes", admin.EmptyFieldListFilter),
    )
    search_fields = ("title", "publisher__name")
    autocomplete_fields = ("book",)
    raw_id_fields = ("series",)
    filter_horizontal = ("tags",)
    filter_vertical = ("shelves",)
    radio_fields = {"format": admin.HORIZONTAL}
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("internal_code", "cover_preview")

    @admin.display(description="Cover preview")
    def cover_preview(self, obj: Edition | None) -> str:
        from django.utils.html import format_html

        if obj is None or not getattr(obj, "cover", None):
            return ""
        return format_html(
            '<img src="{}" alt="" class="admin-mobile-thumb" width="96" height="96">',
            obj.cover.url,
        )

    inlines = (CitationInline,)
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "title",
                    "slug",
                    "book",
                    "publisher",
                    "series",
                    "format",
                    "featured",
                )
            },
        ),
        ("Catalog", {"fields": ("tags", "shelves", "published_on", "internal_code")}),
        ("Files", {"fields": ("cover", "cover_preview", "manuscript")}),
        ("Notes", {"classes": ("collapse",), "fields": ("notes",)}),
    )


@admin.register(Revision)
class RevisionAdmin(admin.ModelAdmin):
    list_display = ("label", "book", "ready", "note")
    list_editable = ("ready", "note")
    list_per_page = 2
    search_fields = ("label",)


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    """Stock widgets on purpose, so the admin calendar and clock remain."""

    list_display = ("title", "on_date", "at_time", "when")
    fields = ("title", "on_date", "at_time", "when")


if hasattr(admin, "ShowFacets"):
    BookAdmin.show_facets = admin.ShowFacets.ALWAYS
    EditionAdmin.show_facets = admin.ShowFacets.ALWAYS
