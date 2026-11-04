# Changelog

## 0.1.0

- Phone layout for the native Django admin: changelist cards, stacked tabular inlines, sticky submit row, 44px targets, 16px inputs.
- Collapsible `#changelist-filter` toggle that does not depend on third-party filter packages.
- `NativeDateInput`, `NativeTimeInput`, `NativeSplitDateTimeWidget`, and `MobileAdminMixin`.
- Opt-in `ADMIN_MOBILE["USE_NATIVE_DATETIME"]` for every `ModelAdmin` and inline.
- Light and dark surfaces use Django admin CSS variables only.
- Phone layout for the rest of the built-in admin: login, password change, logout, index, nav sidebar, header, breadcrumbs, date hierarchy, pagination, list editing, select-all, sort links, facets and the empty filter, related-object widgets, raw id lookup, autocomplete, filter horizontal/vertical, radios, file clear, collapsed fieldsets, readonly fields, errors, stacked inlines, history, delete confirmation, popups, messages, calendar/clock, admindocs, and RTL.
