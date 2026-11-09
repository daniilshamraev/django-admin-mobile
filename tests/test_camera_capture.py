"""Phone camera capture must land in the named file input once."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

playwright_sync = pytest.importorskip("playwright.sync_api")
Page = playwright_sync.Page
Route = playwright_sync.Route
expect = playwright_sync.expect

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.playwright]

PACKAGE = Path(__file__).resolve().parents[1] / "src" / "admin_mobile"
FEATURES_JS = PACKAGE / "static/admin_mobile/js/admin_mobile_features.js"

# 1x1 PNG. Chromium can decode it; a HEIC stand-in cannot.
PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000001000000010802000000907753de"
    "0000000c4944415408d763f8cfc00000000300010005fed4ef0000000049454e44ae426082"
)

CAMERA_PAGE = """<!DOCTYPE html>
<html class="admin-mobile">
<head><meta charset="utf-8"></head>
<body>
<script type="application/json" id="admin-mobile-config">{config}</script>
<form id="mailing" method="post" enctype="multipart/form-data" action="/admin/x/add/">
  <div class="form-row">
    <div class="iuw-root empty">
      <input type="file" name="photo" id="id_photo" accept="image/*">
      <input type="checkbox" name="send_now" id="id_send_now" checked>
      <input type="checkbox" name="photo-clear" id="photo-clear_id" checked>
      <div class="iuw-image-preview"></div>
    </div>
  </div>
  <div class="form-row">
    <p class="file-upload">
      <input type="file" name="notes" id="id_notes">
      <input type="checkbox" name="notes-clear" id="notes-clear_id" checked>
    </p>
  </div>
  <div class="inline-group">
    <div class="empty-form">
      <input type="file" name="shots-__prefix__-image" id="id_shots-empty">
    </div>
  </div>
  <button type="submit" name="_save" value="Save">Save</button>
</form>
<script>
document.addEventListener("change", function (event) {{
  var target = event.target;
  if (!target || target.id !== "id_photo") {{
    return;
  }}
  window.__photoChanges = (window.__photoChanges || 0) + 1;
  var root = target.closest(".iuw-root");
  if (!root || !target.files || !target.files.length) {{
    return;
  }}
  var preview = root.querySelector(".iuw-image-preview");
  var img = preview.querySelector("img");
  if (!img) {{
    img = document.createElement("img");
    img.alt = "";
    preview.appendChild(img);
  }}
  img.dataset.shown = target.files[0].name;
  root.classList.remove("empty");
}});
</script>
</body>
</html>
"""


def _markup(*, compress: bool) -> str:
    payload = {
        "camera": True,
        "compress": compress,
        "tabs": False,
        "pwa": False,
        "haptics": False,
        "lightbox": False,
        "pickers": False,
        "navigator": False,
        "filterSheet": False,
        "unsaved": False,
        "drafts": False,
        "doubleSubmit": True,
        "swipeConfirm": False,
        "undoDelete": False,
        "keyboards": False,
        "bulk": False,
        "swipe": False,
        "pullToRefresh": False,
        "infiniteScroll": False,
    }
    return CAMERA_PAGE.format(config=json.dumps(payload))


def _open(
    page: Page,
    base_url: str,
    *,
    width: int = 375,
    compress: bool = True,
) -> None:
    # set_content is an opaque origin: document.cookie throws and aborts
    # onReady before initCamera. Serve the fixture from the live server.
    page.set_viewport_size({"width": width, "height": 812})
    html = _markup(compress=compress)

    def fulfill(route: Route) -> None:
        route.fulfill(
            status=200,
            content_type="text/html; charset=utf-8",
            body=html,
        )

    page.route("**/__camera_fixture__", fulfill)
    page.goto(f"{base_url}/__camera_fixture__")
    page.add_script_tag(path=str(FEATURES_JS))


def _pick(page: Page, *, name: str, mime: str, payload: bytes) -> None:
    page.evaluate(
        """([name, mime, bytes]) => {
          const input = document.getElementById("id_photo");
          const camera = input.parentElement.querySelector(
            "input[type=file]:not([name])"
          );
          if (!camera) {
            throw new Error("camera input missing");
          }
          const transfer = new DataTransfer();
          transfer.items.add(new File([new Uint8Array(bytes)], name, { type: mime }));
          camera.files = transfer.files;
          camera.dispatchEvent(new Event("change", { bubbles: true }));
        }""",
        [name, mime, list(payload)],
    )


def _hold_compression(page: Page) -> None:
    page.evaluate(
        """() => {
          const original = HTMLCanvasElement.prototype.toBlob;
          HTMLCanvasElement.prototype.toBlob = function (callback, type, quality) {
            window.__held = { canvas: this, callback, type, quality, original };
          };
        }"""
    )


def test_save_copies_pending_photo_before_the_post(
    page: Page, live_server: object
) -> None:
    _open(page, str(live_server.url))
    _hold_compression(page)
    _pick(page, name="shot.png", mime="image/png", payload=PNG)
    page.wait_for_function("() => window.__held", timeout=3000)
    empty = page.evaluate("() => document.getElementById('id_photo').files.length")
    assert empty == 0

    saved = page.evaluate(
        """() => {
          const form = document.getElementById("mailing");
          const input = document.getElementById("id_photo");
          let seen = null;
          form.addEventListener("submit", (event) => {
            const file = input.files[0];
            const body = new FormData(form);
            seen = {
              prevented: event.defaultPrevented,
              files: input.files.length,
              name: file ? file.name : "",
              type: file ? file.type : "",
              clear: document.getElementById("photo-clear_id").checked,
              sendNow: document.getElementById("id_send_now").checked,
              notesClear: document.getElementById("notes-clear_id").checked,
              posted: body.getAll("photo").length,
              helperPosted: [...body.keys()].includes(""),
            };
            event.preventDefault();
          });
          form.requestSubmit();
          return seen;
        }"""
    )
    assert saved is not None
    assert saved["prevented"] is False
    assert saved["files"] == 1
    assert saved["name"] == "shot.png"
    assert saved["type"] == "image/png"
    assert saved["posted"] == 1
    assert saved["helperPosted"] is False
    assert saved["clear"] is False
    assert saved["sendNow"] is True
    assert saved["notesClear"] is True

    page.evaluate(
        """() => new Promise((resolve) => {
          const held = window.__held;
          held.original.call(held.canvas, (blob) => {
            held.callback(blob);
            resolve(true);
          }, held.type, held.quality);
        })"""
    )
    kept = page.evaluate(
        """() => {
          const file = document.getElementById("id_photo").files[0];
          return file ? file.name : "";
        }"""
    )
    assert kept == "shot.png"
    expect(page.locator("img.admin-mobile-thumb")).to_have_count(0)
    expect(page.locator(".iuw-image-preview img")).to_have_attribute(
        "data-shown", "shot.png"
    )


def test_save_is_blocked_when_the_photo_cannot_be_assigned(
    page: Page, live_server: object
) -> None:
    _open(page, str(live_server.url))
    seen = page.evaluate(
        """() => {
          const input = document.getElementById("id_photo");
          const camera = input.parentElement.querySelector(
            "input[type=file]:not([name])"
          );
          const transfer = new DataTransfer();
          transfer.items.add(new File(["x"], "shot.png", { type: "image/png" }));
          camera.files = transfer.files;
          window.DataTransfer = class {
            constructor() { throw new Error("nope"); }
          };
          camera.dispatchEvent(new Event("change", { bubbles: true }));
          const form = document.getElementById("mailing");
          let result = null;
          form.addEventListener("submit", (event) => {
            result = {
              prevented: event.defaultPrevented,
              files: input.files.length,
            };
            event.preventDefault();
          });
          form.requestSubmit();
          return result;
        }"""
    )
    assert seen is not None
    assert seen["prevented"] is True
    assert seen["files"] == 0
    expect(page.locator(".admin-mobile-camera-error")).to_have_text(
        "Could not attach this photo."
    )


def test_decode_error_uses_the_original_and_one_preview(
    page: Page, live_server: object
) -> None:
    _open(page, str(live_server.url))
    page.evaluate(
        """() => {
          window.Image = class {
            constructor() {
              this.onload = null;
              this.onerror = null;
              this.width = 0;
              this.height = 0;
            }
            set src(_value) {
              const image = this;
              queueMicrotask(() => {
                if (typeof image.onerror === "function") {
                  image.onerror(new Event("error"));
                }
              });
            }
          };
        }"""
    )
    _pick(page, name="photo.heic", mime="image/heic", payload=b"not-a-heic")
    page.wait_for_function(
        """() => {
          const input = document.getElementById("id_photo");
          const file = input.files[0];
          return Boolean(file)
            && file.name === "photo.heic"
            && file.type === "image/heic"
            && window.__photoChanges >= 1;
        }""",
        timeout=3000,
    )
    expect(page.locator("#photo-clear_id")).not_to_be_checked()
    expect(page.locator("#id_send_now")).to_be_checked()
    expect(page.locator("#notes-clear_id")).to_be_checked()
    expect(page.locator("img.admin-mobile-thumb")).to_have_count(0)
    expect(page.locator(".admin-mobile-camera-error")).to_have_count(0)
    expect(page.locator(".iuw-image-preview img")).to_have_count(1)
    expect(page.locator(".iuw-image-preview img")).to_have_attribute(
        "data-shown", "photo.heic"
    )
    helper = page.evaluate(
        """() => {
          const input = document.getElementById("id_photo");
          const camera = input.parentElement.querySelector(
            "input[type=file]:not([name])"
          );
          const first = input.closest(".iuw-root").querySelector("input[type=file]");
          return {
            named: camera.hasAttribute("name"),
            firstIsPhoto: first === input,
            buttonType: input.parentElement.querySelector("button").type,
          };
        }"""
    )
    assert helper["named"] is False
    assert helper["firstIsPhoto"] is True
    assert helper["buttonType"] == "button"


def test_successful_compress_notifies_the_widget_once(
    page: Page, live_server: object
) -> None:
    _open(page, str(live_server.url))
    _pick(page, name="shot.png", mime="image/png", payload=PNG)
    page.wait_for_function(
        """() => {
          const input = document.getElementById("id_photo");
          const file = input.files[0];
          const img = document.querySelector(".iuw-image-preview img");
          return Boolean(file)
            && file.type === "image/jpeg"
            && file.name === "capture.jpg"
            && window.__photoChanges === 1
            && img && img.dataset.shown === "capture.jpg";
        }""",
        timeout=3000,
    )
    expect(page.locator("img.admin-mobile-thumb")).to_have_count(0)
    expect(page.locator(".iuw-image-preview img")).to_have_count(1)
    expect(page.locator("#photo-clear_id")).not_to_be_checked()
    expect(page.locator("#id_send_now")).to_be_checked()
    expect(page.locator(".empty-form button")).to_have_count(0)
    expect(page.locator(".empty-form input[type=file]:not([name])")).to_have_count(0)


def test_native_pick_is_not_overwritten_or_previewed_twice(
    page: Page, live_server: object, tmp_path: Path
) -> None:
    _open(page, str(live_server.url))
    _hold_compression(page)
    _pick(page, name="shot.png", mime="image/png", payload=PNG)
    page.wait_for_function("() => window.__held", timeout=3000)
    native = tmp_path / "native.png"
    native.write_bytes(PNG)
    page.set_input_files("#id_photo", str(native))
    page.evaluate(
        """() => new Promise((resolve) => {
          const held = window.__held;
          held.original.call(held.canvas, (blob) => {
            held.callback(blob);
            resolve(true);
          }, held.type, held.quality);
        })"""
    )
    kept = page.evaluate(
        """() => {
          const input = document.getElementById("id_photo");
          const file = input.files[0];
          return {
            name: file ? file.name : "",
            thumbs: document.querySelectorAll("img.admin-mobile-thumb").length,
            changes: window.__photoChanges || 0,
          };
        }"""
    )
    assert kept["name"] == "native.png"
    assert kept["thumbs"] == 0
    assert kept["changes"] >= 1


def test_desktop_width_does_not_add_camera_controls(
    page: Page, live_server: object
) -> None:
    _open(page, str(live_server.url), width=601)
    expect(page.get_by_role("button", name="Camera")).to_have_count(0)
    expect(page.locator("input[type=file]:not([name])")).to_have_count(0)
    expect(page.locator("img.admin-mobile-thumb")).to_have_count(0)
    expect(page.locator("input[type=file]")).to_have_count(3)


def test_added_inline_row_gets_its_own_camera(page: Page, live_server: object) -> None:
    _open(page, str(live_server.url))
    added = page.evaluate(
        """() => {
          const row = document.createElement("div");
          row.className = "form-row";
          row.innerHTML = '<input type="file" name="shots-0-image" id="id_shots-0">';
          document.querySelector(".inline-group").appendChild(row);
          row.dispatchEvent(new CustomEvent("formset:added", { bubbles: true }));
          const input = document.getElementById("id_shots-0");
          const camera = input.parentElement.querySelector(
            "input[type=file]:not([name])"
          );
          return {
            hasCamera: Boolean(camera),
            named: camera ? camera.hasAttribute("name") : true,
            emptyStillPlain: document.querySelector(".empty-form button") === null,
          };
        }"""
    )
    assert added["hasCamera"] is True
    assert added["named"] is False
    assert added["emptyStillPlain"] is True
