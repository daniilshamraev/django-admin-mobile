"""375px admin screenshots and filter-package DOM compatibility."""

from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
from pathlib import Path

import pytest
from django.contrib.admin.models import ADDITION, LogEntry
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile
from django.utils import timezone

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

playwright_sync = pytest.importorskip("playwright.sync_api")
Page = playwright_sync.Page
expect = playwright_sync.expect

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.playwright]

SCREENSHOTS = Path(__file__).resolve().parents[1] / "docs" / "screenshots"
PACKAGE = Path(__file__).resolve().parents[1] / "src" / "admin_mobile"
FILTER_FIXTURE = """
<!DOCTYPE html>
<html class="admin-mobile admin-mobile-filters" data-theme="light"
      data-admin-mobile-filters-label="Filters">
<head><meta charset="utf-8"></head>
<body>
  <div id="changelist">
    <div id="changelist-filter">
      <h2>Filter</h2>
      <div class="admindatefilter">
        <label>From <input class="range-filter" name="published_on__range__gte"></label>
      </div>
      <details class="more-admin-filters">
        <summary>Status</summary>
        <ul><li><a href="?status__exact=published">Published</a></li></ul>
      </details>
    </div>
  </div>
</body>
</html>
"""


@pytest.fixture
def catalog(live_server: object) -> dict[str, str]:
    del live_server
    user_model = get_user_model()
    user_model.objects.create_superuser("shot", "shot@example.com", "secret")
    lovelace = Author.objects.create(name="Ada Lovelace", birth_date=date(1815, 12, 10))
    hopper = Author.objects.create(name="Grace Hopper", birth_date=date(1906, 12, 9))
    notes = Book.objects.create(
        title="Notes on the Analytical Engine",
        author=lovelace,
        status=Book.Status.PUBLISHED,
        published_on=date(1843, 8, 1),
        reading_time=time(21, 30),
        pages=96,
    )
    Book.objects.create(
        title="The First Compiler",
        author=hopper,
        status=Book.Status.DRAFT,
        published_on=date(1952, 5, 3),
        pages=240,
    )
    Chapter.objects.create(
        book=notes,
        title="Note G",
        order=1,
        starts_at=time(22, 15),
        word_count=1800,
    )
    user = user_model.objects.get(username="shot")
    LogEntry.objects.create(
        user_id=user.pk,
        content_type_id=ContentType.objects.get_for_model(notes).pk,
        object_id=str(notes.pk),
        object_repr=str(notes)[:200],
        action_flag=ADDITION,
        change_message="Added for the history screen.",
    )
    press = Publisher.objects.create(name="Local Press")
    series = Series.objects.create(name="Computing Classics")
    tag = Tag.objects.create(name="Margin notes", slug="margin-notes")
    shelf = Shelf.objects.create(name="Reading room")
    edition = Edition.objects.create(
        book=notes,
        publisher=press,
        series=series,
        title="Notes, second printing",
        slug="notes-second-printing",
        featured=True,
        published_on=date(1843, 8, 1),
    )
    edition.tags.add(tag)
    edition.shelves.add(shelf)
    edition.manuscript.save("memo.txt", ContentFile(b"Local demo file.\n"), save=True)
    cover = (
        Path(__file__).resolve().parents[1]
        / "src/admin_mobile/static/admin_mobile/icons/icon-192.png"
    )
    if cover.is_file():
        edition.cover.save("cover.png", ContentFile(cover.read_bytes()), save=True)
    Citation.objects.create(
        edition=edition,
        quote="The Analytical Engine weaves algebraical patterns.",
        page=12,
        order=1,
    )
    Revision.objects.create(book=notes, label="Proof 1", ready=True, note="Margins")
    Revision.objects.create(book=notes, label="Proof 2", ready=False, note="Plates")
    Revision.objects.create(
        book=hopper_book(hopper), label="Draft A", ready=False, note="Early"
    )
    visit = Appointment.objects.create(
        title="Reading hour",
        on_date=date(2026, 4, 2),
        at_time=time(18, 30),
        when=timezone.make_aware(datetime(2026, 4, 2, 18, 30)),
    )
    Payment.objects.create(
        payer_name="Мария Александровна Волконская",
        vk_id="123456789012345678",
        amount=Decimal("1490.50"),
        system=Payment.System.WALLET,
        status="Оплачен",
        paid_on=date(2026, 3, 2),
        external_id="pay-1843-notes",
        comment="Перевод за второе издание",
        currency="RUB",
    )
    return {
        "change": f"/admin/library/book/{notes.pk}/change/",
        "list": "/admin/library/book/",
        "history": f"/admin/library/book/{notes.pk}/history/",
        "delete": f"/admin/library/book/{notes.pk}/delete/",
        "edition": f"/admin/library/edition/{edition.pk}/change/",
        "edition_add": "/admin/library/edition/add/",
        "revisions": "/admin/library/revision/",
        "appointment": f"/admin/library/appointment/{visit.pk}/change/",
        "tag": f"/admin/library/tag/{tag.pk}/change/",
        "payments": "/admin/library/payment/",
        "search": "/admin/admin-mobile/search/?q=Notes",
        "recent": "/admin/admin-mobile/recent/",
    }


def hopper_book(hopper: Author) -> Book:
    return Book.objects.get(author=hopper)


def _login(page: Page, base_url: str) -> None:
    page.goto(f"{base_url}/admin/login/")
    page.fill("#id_username", "shot")
    page.fill("#id_password", "secret")
    page.click('input[type="submit"]')
    expect(page.locator("#header")).to_be_visible()


def test_filter_sidebar_accepts_third_party_markup(page: Page) -> None:
    page.set_viewport_size({"width": 375, "height": 812})
    page.set_content(FILTER_FIXTURE)
    page.add_style_tag(path=str(PACKAGE / "static/admin_mobile/css/admin_mobile.css"))
    page.add_script_tag(path=str(PACKAGE / "static/admin_mobile/js/admin_mobile.js"))
    toggle = page.locator("#admin-mobile-filter-toggle")
    expect(toggle).to_be_visible()
    expect(toggle).to_have_attribute("aria-expanded", "false")
    expect(page.locator(".admindatefilter")).to_be_hidden()
    toggle.click()
    expect(page.locator(".admindatefilter")).to_be_visible()
    expect(page.locator(".more-admin-filters summary")).to_be_visible()
    expect(page.locator("input.range-filter")).to_be_visible()
    page.set_viewport_size({"width": 1100, "height": 800})
    expect(toggle).to_be_hidden()
    expect(page.locator("#changelist-filter")).to_be_visible()


def test_admin_screenshots_at_phone_width(
    page: Page,
    live_server: object,
    catalog: dict[str, str],
) -> None:
    SCREENSHOTS.mkdir(parents=True, exist_ok=True)
    base_url = str(live_server.url)
    page.emulate_media(color_scheme="light")
    _login(page, base_url)

    page.set_viewport_size({"width": 375, "height": 812})
    page.goto(f"{base_url}{catalog['list']}")
    title_cell = page.locator("#result_list tbody tr").first.locator("th, td").nth(1)
    expect(title_cell).to_have_attribute("data-label", "Title")
    expect(page.locator("#result_list .action-checkbox input").first).to_be_visible()
    expect(page.locator(".admin-mobile-sort")).to_be_visible()
    expect(page.locator("#admin-mobile-select-all")).to_be_visible()
    expect(page.locator(".toplinks a").first).to_be_visible()
    expect(page.locator(".paginator").first).to_be_visible()
    display = title_cell.evaluate("element => getComputedStyle(element).display")
    assert display == "grid"
    _pair(page, "changelist-375.png")
    page.locator("#admin-mobile-select-all").check()
    expect(page.locator("#result_list .action-checkbox input").first).to_be_checked()

    page.locator("#admin-mobile-filter-toggle").click()
    expect(page.locator("#changelist-filter")).to_be_visible()
    expect(page.locator("#changelist-filter").get_by_text("By status")).to_be_visible()
    _pair(page, "filters-375.png")
    page.locator("#admin-mobile-filter-toggle").click()

    page.set_viewport_size({"width": 800, "height": 900})
    page.goto(f"{base_url}{catalog['list']}")
    overflow = page.locator("#changelist .results").evaluate(
        "element => getComputedStyle(element).overflowX"
    )
    assert overflow == "auto"
    row_display = page.locator("#result_list tbody tr").first.evaluate(
        "element => getComputedStyle(element).display"
    )
    assert row_display == "table-row"

    page.set_viewport_size({"width": 375, "height": 812})
    page.goto(f"{base_url}{catalog['change']}")
    expect(page.locator("input[type='date']").first).to_be_visible()
    expect(page.locator("input[type='time']").first).to_be_visible()
    inline_cell = page.locator(
        ".inline-group .tabular tr.form-row:not(.empty-form) td.field-title"
    ).first
    expect(inline_cell).to_have_attribute("data-label", "Title")
    font_size = page.locator("#id_title").evaluate(
        "element => getComputedStyle(element).fontSize"
    )
    assert font_size == "16px"
    sticky = page.locator("form .submit-row").last.evaluate(
        "element => getComputedStyle(element).position"
    )
    assert sticky == "fixed"

    title_inputs = page.locator(
        ".inline-group .tabular tr.form-row:not(.empty-form) input[name$='-title']"
    )
    before_add = title_inputs.count()
    page.locator(".inline-group .tabular tr.add-row a").click()
    expect(title_inputs).to_have_count(before_add + 1)
    added = page.locator(
        ".inline-group .tabular tr.form-row:not(.empty-form) td.field-title"
    ).last
    expect(added).to_have_attribute("data-label", "Title")
    page.locator(".inline-deletelink").last.click()
    expect(title_inputs).to_have_count(before_add)

    _pair(page, "change-form-375.png")


def _shot(page: Page, name: str) -> None:
    page.screenshot(path=str(SCREENSHOTS / name), full_page=False)


def _theme(page: Page, name: str) -> None:
    page.emulate_media(color_scheme=name)
    page.evaluate(
        "(theme) => document.documentElement.setAttribute('data-theme', theme)",
        name,
    )
    # Django fades link color and background for 150ms. Wait so screenshots
    # show the settled theme, not the previous one mid-transition.
    page.wait_for_timeout(220)


def _pair(page: Page, name: str) -> None:
    stem, _, ext = name.rpartition(".")
    _theme(page, "light")
    _shot(page, name)
    _theme(page, "dark")
    if not stem.endswith("-dark"):
        _shot(page, f"{stem}-dark.{ext}")
    _theme(page, "light")


def test_builtin_admin_surfaces(
    page: Page,
    live_server: object,
    catalog: dict[str, str],
) -> None:
    SCREENSHOTS.mkdir(parents=True, exist_ok=True)
    base_url = str(live_server.url)
    page.set_viewport_size({"width": 375, "height": 812})

    page.goto(f"{base_url}/admin/login/")
    expect(page.locator("#id_username")).to_be_visible()
    _pair(page, "login-375.png")
    _login(page, base_url)

    page.goto(f"{base_url}/admin/")
    expect(page.locator("#content-main")).to_be_visible()
    _pair(page, "index-375.png")
    _pair(page, "tabs-375.png")

    page.goto(f"{base_url}/admin/library/")
    expect(page.get_by_role("link", name="Books")).to_be_visible()
    _pair(page, "app-index-375.png")

    page.goto(f"{base_url}/admin/password_change/")
    expect(page.locator("#id_old_password")).to_be_visible()
    _pair(page, "password-change-375.png")

    page.goto(f"{base_url}{catalog['list']}")
    toggle = page.locator("#toggle-nav-sidebar")
    sidebar = page.locator("#nav-sidebar")
    expect(toggle).to_be_visible()
    if sidebar.get_attribute("aria-expanded") != "true":
        toggle.click()
    expect(sidebar).to_be_visible()
    page.fill("#nav-filter", "Book")
    _pair(page, "nav-sidebar-375.png")
    toggle.click()
    expect(sidebar).to_be_hidden()

    page.goto(f"{base_url}{catalog['revisions']}")
    expect(page.locator("#result_list input[name$='-note']").first).to_be_visible()
    _pair(page, "changelist-editable-375.png")

    page.goto(f"{base_url}{catalog['payments']}")
    payer = page.locator("#result_list .field-payer .admin-mobile-value").first
    expect(payer).to_contain_text("vk.com/id123456789012345678")
    title = page.locator("#result_list .admin-mobile-card-title").first
    expect(title).to_be_visible()
    label_text = title.evaluate(
        "element => getComputedStyle(element, '::before').content"
    )
    assert label_text == "none"
    wrapped = payer.evaluate("element => getComputedStyle(element).overflowWrap")
    assert wrapped == "anywhere"
    price = page.locator("#result_list .field-amount input").first
    expect(price).to_be_visible()
    aligned = price.evaluate(
        """element => {
            const value = element.closest('.admin-mobile-value');
            const valueBox = value.getBoundingClientRect();
            const inputBox = element.getBoundingClientRect();
            return Math.abs(inputBox.right - valueBox.right) < 2
                && inputBox.left >= valueBox.left - 1;
        }"""
    )
    assert aligned is True
    save_edge = page.evaluate(
        """() => {
            const save = document.querySelector('.admin-mobile-save-model');
            const select = document.querySelector('#changelist .actions select');
            const run = document.querySelector('#changelist .actions button');
            const saveBox = save.getBoundingClientRect();
            const selectBox = select.getBoundingClientRect();
            const runBox = run.getBoundingClientRect();
            return Math.abs(saveBox.left - selectBox.left) <= 2
                && Math.abs(saveBox.right - runBox.right) <= 2
                && saveBox.height >= 40;
        }"""
    )
    assert save_edge is True
    expect(page.locator("#changelist .actions select")).to_be_visible()
    expect(page.locator(".admin-mobile-bulkbar")).to_be_hidden()
    _pair(page, "payments-375.png")
    page.locator("#result_list .action-checkbox input").first.check()
    bar = page.locator(".admin-mobile-bulkbar")
    expect(bar).to_be_visible()
    expect(page.locator("#changelist .actions select")).to_be_hidden()
    expect(page.locator("#admin-mobile-select-all")).to_be_visible()
    row_fit = bar.evaluate(
        """element => {
            const select = element.querySelector('select');
            const run = element.querySelector('button, input[type=submit]');
            const barBox = element.getBoundingClientRect();
            const selectBox = select.getBoundingClientRect();
            const runBox = run.getBoundingClientRect();
            return barBox.left >= -1
                && barBox.right <= window.innerWidth + 1
                && Math.abs(selectBox.top - runBox.top) < 4
                && Math.abs(selectBox.height - runBox.height) < 3
                && selectBox.height >= 40;
        }"""
    )
    assert row_fit is True
    tint = page.locator("#result_list tbody tr").first.evaluate(
        "element => getComputedStyle(element).backgroundColor"
    )
    assert tint != "rgb(228, 228, 228)"
    _pair(page, "payments-selected-375.png")

    page.goto(f"{base_url}{catalog['edition']}")
    expect(page.locator("input[name='series']")).to_be_visible()
    expect(page.locator(".selector").first).to_be_visible()
    expect(page.get_by_text("Currently:").first).to_be_visible()
    expect(page.locator(".inline-group[data-inline-type='stacked']")).to_be_visible()
    expect(page.locator(".readonly").first).to_be_visible()
    _pair(page, "edition-375.png")
    _pair(page, "camera-375.png")

    with page.expect_popup() as popup_info:
        page.locator("#add_id_publisher").click()
    popup = popup_info.value
    popup.set_viewport_size({"width": 375, "height": 812})
    expect(popup.locator("input[type='text']").first).to_be_visible()
    _pair(popup, "popup-375.png")
    popup.close()

    page.goto(f"{base_url}{catalog['edition_add']}")
    page.fill("#id_title", "Broken edition")
    page.locator("input[name$='-page']").first.fill("4")
    page.locator("input[name='_save']").click()
    expect(page.locator(".errornote, .errorlist").first).to_be_visible()
    _pair(page, "inline-errors-375.png")

    page.goto(f"{base_url}{catalog['history']}")
    expect(
        page.locator("#change-history tbody td, #change-history tbody th").first
    ).to_have_attribute(
        "data-label",
        "Date/time",
    )
    _pair(page, "history-375.png")

    page.goto(f"{base_url}{catalog['delete']}")
    expect(page.get_by_text("Note G")).to_be_visible()
    _pair(page, "delete-confirm-375.png")
    page.locator("input[type='submit']").click()
    expect(page.locator(".admin-mobile-slide")).to_be_visible()
    _pair(page, "slide-confirm-375.png")
    page.locator(".admin-mobile-slide").focus()
    for _ in range(5):
        page.keyboard.press("ArrowRight")
    expect(page.locator(".admin-mobile-toast")).to_be_visible()
    _pair(page, "undo-375.png")
    page.locator(".admin-mobile-toast button").click()

    page.goto(f"{base_url}{catalog['appointment']}")
    page.locator("#calendarlink0").click()
    expect(page.locator("#calendarbox0")).to_be_visible()
    _pair(page, "calendar-375.png")
    page.locator("#calendarbox0 .calendar-cancel").click()
    page.locator("#clocklink0").click()
    expect(page.locator("#clockbox0")).to_be_visible()
    _pair(page, "clock-375.png")

    page.goto(f"{base_url}/admin/doc/")
    expect(page.locator("#content")).to_be_visible()
    _pair(page, "admindocs-375.png")
    page.goto(f"{base_url}/admin/doc/models/library.book/")
    expect(page.locator("table.model")).to_be_visible()
    _pair(page, "admindocs-model-375.png")

    page.goto(f"{base_url}{catalog['change']}")
    page.locator("input[name='_save']").click()
    expect(page.locator(".messagelist")).to_be_visible()
    _pair(page, "message-375.png")
    _pair(page, "toast-375.png")

    page.goto(f"{base_url}{catalog['search']}")
    expect(page.locator("#admin-mobile-q")).to_be_visible()
    _pair(page, "search-375.png")
    page.goto(f"{base_url}{catalog['recent']}")
    _pair(page, "recent-375.png")

    page.goto(f"{base_url}{catalog['list']}")
    _pair(page, "pull-375.png")
    page.locator(".admin-mobile-save-model").click()
    page.locator(".admin-mobile-tabbar").get_by_role("button", name="Saved").click()
    expect(page.get_by_text("Saved models")).to_be_visible()
    _pair(page, "favorites-375.png")

    page.goto(f"{base_url}{catalog['list']}")
    row = page.locator("#result_list tbody tr").first
    box = row.bounding_box()
    assert box is not None
    page.mouse.move(box["x"] + box["width"] - 20, box["y"] + 24)
    page.mouse.down()
    page.mouse.move(box["x"] + 20, box["y"] + 24)
    page.mouse.up()
    expect(page.locator(".admin-mobile-swipe-actions").first).to_be_visible()
    _pair(page, "swipe-375.png")
    page.locator("#result_list .action-checkbox input").first.check()
    expect(page.locator(".admin-mobile-bulkbar")).to_be_visible()
    _pair(page, "bulk-375.png")
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(500)
    _pair(page, "infinite-scroll-375.png")

    page.goto(f"{base_url}{catalog['change']}")
    page.locator("#id_status").click()
    expect(page.locator(".admin-mobile-picker")).to_be_visible()
    _pair(page, "picker-375.png")
    page.keyboard.press("Escape")
    page.get_by_role("button", name="Sections").click()
    expect(page.locator(".admin-mobile-navigator")).to_be_visible()
    _pair(page, "navigator-375.png")

    page.goto(f"{base_url}{catalog['tag']}")
    expect(page.locator("input[name='_save']")).to_have_count(0)
    _pair(page, "readonly-375.png")

    page.goto(f"{base_url}{catalog['edition']}")
    thumb = page.locator(".readonly .admin-mobile-thumb")
    if thumb.count():
        thumb.click()
        expect(page.locator(".admin-mobile-lightbox-dialog")).to_be_visible()
        _pair(page, "lightbox-375.png")
        page.locator(".admin-mobile-lightbox-close").click()

    page.goto(f"{base_url}{catalog['list']}")
    page.evaluate("document.documentElement.setAttribute('dir', 'rtl')")
    expect(
        page.locator("#result_list tbody tr").first.locator("th, td").nth(1)
    ).to_have_attribute(
        "data-label",
        "Title",
    )
    _pair(page, "rtl-changelist-375.png")

    page.get_by_role("button", name="Account").click()
    page.locator("#logout-form button").click()
    expect(page.get_by_text("Logged out")).to_be_visible()
    _pair(page, "logged-out-375.png")
