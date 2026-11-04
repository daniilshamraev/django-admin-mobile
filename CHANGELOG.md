# Changelog

## 0.2.0

- Phone layout pass: compact header, aligned index rows, full-width fields, centered object-tool buttons, a Sort by control, and an 8px spacing scale.
- Bottom tabs, global staff search, recent log, saved models, swipe actions, pull-to-refresh, optional infinite scroll, filter bottom sheet, sticky bulk actions, unsaved-change guard, add-form drafts, camera capture, mobile keyboards, section navigator, and sheet pickers.
- Card hints on `MobileAdminMixin`: `mobile_card_title`, `mobile_card_subtitle`, `mobile_card_image`, `mobile_list_display`.
- Lightbox, deferred single-object delete (`UNDO_DELETE`, off by default), slide-to-confirm, and double-submit protection.
- `ACCENT` and `PALETTE` map onto Django admin CSS variables for light and dark (`data-theme` and `prefers-color-scheme`). No hardcoded light surfaces on the new chrome.
- `READONLY_MODELS` and `mobile_readonly` hide add/change/delete on a narrow viewport. This is a UX guard, not a permission check.
- PWA manifest, icons, live `theme-color` from `--header-bg`, and a service worker that caches `/static/` only.

## 0.1.0

- Phone layout for the native Django admin: changelist cards, stacked tabular inlines, sticky submit row, 44px targets, 16px inputs.
- Collapsible `#changelist-filter` toggle that does not depend on third-party filter packages.
- `NativeDateInput`, `NativeTimeInput`, `NativeSplitDateTimeWidget`, and `MobileAdminMixin`.
- Opt-in `ADMIN_MOBILE["USE_NATIVE_DATETIME"]` for every `ModelAdmin` and inline.
- Light and dark surfaces use Django admin CSS variables only.
- Phone layout for the rest of the built-in admin: login, password change, logout, index, nav sidebar, header, breadcrumbs, date hierarchy, pagination, list editing, select-all, sort links, facets and the empty filter, related-object widgets, raw id lookup, autocomplete, filter horizontal/vertical, radios, file clear, collapsed fieldsets, readonly fields, errors, stacked inlines, history, delete confirmation, popups, messages, calendar/clock, admindocs, and RTL.
