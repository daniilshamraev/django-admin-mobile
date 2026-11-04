# Changelog

## 0.2.5

- A selected changelist card uses a light accent tint and outline instead of Django’s flat selected-row fill.
- The checkbox and the linked column share one left-aligned title line. Field labels stay on the rows below, about 40% wide, with values wrapping in the rest of the row.
- Rich cell HTML and list-editable inputs stay inside the value column. The sticky bulk bar is full width above the tab bar: the count, the action menu, and Run share one row.

## 0.2.4

- The action menu and Run share one 44px row and the same corner radius. Run stays only as wide as its label.
- “Select all” sits in that actions block. Each card keeps one checkbox, on the same line as the title.

## 0.2.3

- Changelist controls share one left and right edge. The action menu and Sort by are the same full-width select with 16px of inner padding. The card no longer repeats a second “Select” label.

## 0.2.2

- Tab labels no longer pick up Django’s link underline. The current tab uses a stronger pill and a bottom bar.
- Index module captions and model rows are inset 16px. Captions keep the card’s top radius.
- Changelist “Save this list” and “Run” use button colors in light and dark. Date chips use the page surface. The filter label, action row, and selection count share the 16px content edge. Pull to refresh stays hidden until a pull starts.
- “Add another” keeps the plus icon and the label together, centered in the row.
- Search results, breadcrumbs, field rows, and the close button use the same 16px inset and button colors.

## 0.2.1

- Header is one row: sidebar icon, ellipsized title in `--header-branding-color`, account sheet, theme toggle. `ACCENT` no longer sets `--accent`, so the title stays readable on `--header-bg`.
- Index rows are full-width with one border. Add, Change, and View share a fixed width.
- Bottom tabs use an icon and a label, with an active state and no underline. The submit bar sits above the tab bar. The section button sits above both.
- Changelist: search submit uses button colors, the action select stays in place, date hierarchy is a chip row, “Save this list” is a secondary toolbar button, and “Sort by” is labeled once.
- Related-object icons are 44px and left-aligned. History is a compact secondary button.
- Changelist: the filter count sits on the trailing side of the Filter control, with padding from the edges, and uses button colors in dark mode. Add stays fixed at the bottom-right, above the tab bar.

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
