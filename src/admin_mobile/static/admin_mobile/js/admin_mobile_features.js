/*
 * Optional phone behaviors. Each one checks admin-mobile-config and the
 * viewport. Colors stay on the stylesheet variables.
 */
(function () {
    "use strict";

    var MOBILE_MQ = "(max-width: 600px)";
    var root = document.documentElement;

    function onReady(callback) {
        if (document.readyState === "loading") {
            document.addEventListener("DOMContentLoaded", callback);
            return;
        }
        callback();
    }

    function readConfig() {
        var node = document.getElementById("admin-mobile-config");
        if (!node) {
            return {};
        }
        try {
            var parsed = JSON.parse(node.textContent || "{}");
            return parsed && typeof parsed === "object" ? parsed : {};
        } catch (error) {
            return {};
        }
    }

    function mobile() {
        return window.matchMedia(MOBILE_MQ).matches;
    }

    function vibrate(ms) {
        if (cfg.haptics && navigator.vibrate) {
            navigator.vibrate(ms);
        }
    }

    function cssColorToHex(value) {
        var match = /^\s*rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)/.exec(value || "");
        if (!match) {
            return /^#[0-9a-fA-F]{6}$/.test(value) ? value : "";
        }
        function hex(part) {
            var text = Number(part).toString(16);
            return text.length === 1 ? "0" + text : text;
        }
        return "#" + hex(match[1]) + hex(match[2]) + hex(match[3]);
    }

    function setCookie(name, value) {
        document.cookie = name + "=" + value + "; Path=/; SameSite=Lax";
    }

    function syncViewportCookie() {
        setCookie("admin_mobile_viewport", mobile() ? "mobile" : "desktop");
        var header = cssColorToHex(
            getComputedStyle(root).getPropertyValue("--header-bg")
        );
        if (header) {
            setCookie("admin_mobile_header", encodeURIComponent(header));
            var meta = document.getElementById("admin-mobile-theme-color");
            if (!meta) {
                meta = document.createElement("meta");
                meta.name = "theme-color";
                meta.id = "admin-mobile-theme-color";
                document.head.appendChild(meta);
            }
            meta.setAttribute("content", header);
        }
    }

    function sheet(className) {
        var node = document.createElement("div");
        node.className = className;
        node.hidden = true;
        node.setAttribute("role", "dialog");
        node.setAttribute("aria-modal", "true");
        document.body.appendChild(node);
        return node;
    }

    function closeOnEscape(node) {
        function onKey(event) {
            if (event.key === "Escape") {
                node.hidden = true;
                document.removeEventListener("keydown", onKey);
            }
        }
        document.addEventListener("keydown", onKey);
    }

    function initHeader() {
        var header = document.getElementById("header");
        var toggle = document.getElementById("toggle-nav-sidebar");
        if (header && toggle && mobile()) {
            header.prepend(toggle);
        }
        var tools = document.getElementById("user-tools");
        if (!tools || !mobile()) {
            return;
        }
        Array.prototype.slice.call(tools.childNodes).forEach(function (node) {
            if (node.nodeType === 3 && node.textContent.indexOf("/") !== -1) {
                node.textContent = " ";
            }
        });
    }

    function initTabs() {
        if (!cfg.tabs || !mobile() || document.querySelector(".admin-mobile-tabbar")) {
            return;
        }
        var bar = document.createElement("nav");
        bar.className = "admin-mobile-tabbar";
        bar.setAttribute("aria-label", "Admin");
        function link(href, text) {
            var anchor = document.createElement("a");
            anchor.href = href;
            anchor.textContent = text;
            return anchor;
        }
        function button(text, action) {
            var control = document.createElement("button");
            control.type = "button";
            control.textContent = text;
            control.addEventListener("click", action);
            return control;
        }
        bar.appendChild(link("/admin/", "Home"));
        if (cfg.searchUrl) {
            bar.appendChild(link(cfg.searchUrl, "Search"));
        }
        if (cfg.recentUrl) {
            bar.appendChild(link(cfg.recentUrl, "Recent"));
        }
        bar.appendChild(button("Saved", openFavorites));
        document.body.appendChild(bar);
    }

    function favoriteStore() {
        try {
            var parsed = JSON.parse(localStorage.getItem("admin-mobile-favorites") || "[]");
            return Array.isArray(parsed) ? parsed : [];
        } catch (error) {
            return [];
        }
    }

    function safeAdminPath(value) {
        return typeof value === "string" && value.indexOf("/admin/") === 0 && value.indexOf("//") === -1;
    }

    function openFavorites() {
        var panel = sheet("admin-mobile-sheet admin-mobile-navigator");
        panel.hidden = false;
        var title = document.createElement("p");
        title.textContent = "Saved models";
        panel.appendChild(title);
        favoriteStore().forEach(function (item) {
            if (!item || !safeAdminPath(item.href)) {
                return;
            }
            var anchor = document.createElement("a");
            anchor.href = item.href;
            anchor.textContent = String(item.label || item.href).slice(0, 80);
            panel.appendChild(anchor);
        });
        var close = document.createElement("button");
        close.type = "button";
        close.className = "admin-mobile-sheet-close";
        close.textContent = "Close";
        close.addEventListener("click", function () { panel.hidden = true; });
        panel.appendChild(close);
        closeOnEscape(panel);
        close.focus();
    }

    function initFavoriteButton() {
        if (!cfg.tabs || !document.body.classList.contains("change-list") || !mobile()) {
            return;
        }
        var button = document.createElement("button");
        button.type = "button";
        button.className = "button admin-mobile-save-model";
        button.textContent = "Save this list";
        button.addEventListener("click", function () {
            if (!safeAdminPath(location.pathname)) {
                return;
            }
            var items = favoriteStore().filter(function (item) {
                return item.href !== location.pathname;
            });
            items.unshift({ href: location.pathname, label: document.title });
            localStorage.setItem("admin-mobile-favorites", JSON.stringify(items.slice(0, 12)));
            button.textContent = "Saved";
        });
        var tools = document.querySelector(".object-tools");
        if (tools) {
            var item = document.createElement("li");
            item.appendChild(button);
            tools.appendChild(item);
        }
    }

    function initFilterBadge() {
        if (!cfg.filterSheet) {
            return;
        }
        var button = document.getElementById("admin-mobile-filter-toggle");
        var sidebar = document.getElementById("changelist-filter");
        if (!button || !sidebar || button.querySelector(".admin-mobile-filter-badge")) {
            return;
        }
        var count = sidebar.querySelectorAll("li.selected").length;
        if (count) {
            var badge = document.createElement("span");
            badge.className = "admin-mobile-filter-badge";
            badge.textContent = String(count);
            button.appendChild(badge);
        }
        if (sidebar.querySelector(".admin-mobile-filter-reset")) {
            return;
        }
        var reset = document.createElement("a");
        reset.className = "admin-mobile-filter-reset button";
        reset.textContent = "Reset";
        var clear = sidebar.querySelector("#changelist-filter-clear a, #changelist-filter-extra-actions a");
        reset.href = clear ? clear.href : location.pathname;
        sidebar.appendChild(reset);
    }

    function initBulk() {
        if (!cfg.bulk || !mobile()) {
            return;
        }
        var form = document.getElementById("changelist-form");
        var actions = document.querySelector("#changelist .actions");
        if (!form || !actions) {
            return;
        }
        var bar = document.createElement("div");
        bar.className = "admin-mobile-bulkbar";
        bar.hidden = true;
        var label = document.createElement("span");
        var select = actions.querySelector("select");
        var run = actions.querySelector("button, input[type=submit]");
        if (select) {
            bar.appendChild(label);
            bar.appendChild(select);
        }
        if (run) {
            bar.appendChild(run);
        }
        document.body.appendChild(bar);
        function refresh() {
            var selected = form.querySelectorAll("input.action-select:checked, .action-checkbox input:checked").length;
            label.textContent = "Selected " + selected;
            bar.hidden = selected === 0;
        }
        form.addEventListener("change", refresh);
        refresh();
    }

    function initSwipe() {
        if (!cfg.swipe || !mobile()) {
            return;
        }
        document.querySelectorAll("#result_list tbody tr").forEach(function (row) {
            if (row.querySelector(".admin-mobile-swipe-actions")) {
                return;
            }
            var actions = document.createElement("div");
            actions.className = "admin-mobile-swipe-actions";
            actions.hidden = true;
            var open = document.createElement("button");
            open.type = "button";
            open.dataset.act = "open";
            open.textContent = "Open";
            var remove = document.createElement("button");
            remove.type = "button";
            remove.dataset.act = "delete";
            remove.textContent = "Delete";
            actions.appendChild(open);
            actions.appendChild(remove);
            row.appendChild(actions);
            var startX = 0;
            row.addEventListener("pointerdown", function (event) {
                startX = event.clientX;
            });
            row.addEventListener("pointerup", function (event) {
                var delta = event.clientX - startX;
                if (delta > 70) {
                    var anchor = row.querySelector("a[href]");
                    if (anchor) {
                        window.location.assign(anchor.href);
                    }
                } else if (delta < -70) {
                    actions.hidden = false;
                }
            }, { passive: true });
            open.addEventListener("click", function () {
                var anchor = row.querySelector("a[href]");
                if (anchor) {
                    window.location.assign(anchor.href);
                }
            });
            remove.addEventListener("click", function () {
                var box = row.querySelector("input[type=checkbox]");
                var form = document.getElementById("changelist-form");
                var action = form && form.querySelector("select[name=action]");
                if (!box || !form || !action) {
                    return;
                }
                if (!window.confirm("Delete this record?")) {
                    return;
                }
                box.checked = true;
                action.value = "delete_selected";
                form.submit();
            });
        });
    }

    function initPull() {
        if (!cfg.pullToRefresh || !document.getElementById("result_list")) {
            return;
        }
        var hint = document.createElement("div");
        hint.className = "admin-mobile-ptr";
        hint.textContent = "Pull to refresh";
        hint.hidden = false;
        var list = document.getElementById("result_list");
        list.parentElement.insertBefore(hint, list);
        var startY = 0;
        document.addEventListener("touchstart", function (event) {
            if (window.scrollY <= 0 && event.touches && event.touches[0]) {
                startY = event.touches[0].clientY;
                hint.hidden = false;
            }
        }, { passive: true });
        document.addEventListener("touchend", function (event) {
            if (!event.changedTouches || !event.changedTouches[0]) {
                return;
            }
            if (window.scrollY <= 0 && event.changedTouches[0].clientY - startY > 80) {
                window.location.reload();
            } else {
                hint.hidden = true;
            }
        }, { passive: true });
    }

    function initInfinite() {
        if (!cfg.infiniteScroll || !mobile()) {
            return;
        }
        var table = document.getElementById("result_list");
        var paginator = document.querySelector(".paginator");
        if (!table || !paginator) {
            return;
        }
        var current = paginator.querySelector(".this-page");
        var page = current ? parseInt(current.textContent, 10) : 1;
        var next = null;
        Array.prototype.forEach.call(paginator.querySelectorAll("a[href]"), function (link) {
            if (link.href.indexOf("p=" + String(page + 1)) !== -1) {
                next = link.href;
            }
        });
        if (!next || next.indexOf(location.origin) !== 0) {
            return;
        }
        var skeleton = document.createElement("div");
        skeleton.className = "admin-mobile-skeleton";
        skeleton.textContent = "Loading";
        skeleton.hidden = true;
        table.parentElement.appendChild(skeleton);
        var busy = false;
        function load() {
            if (busy || !next) {
                return;
            }
            busy = true;
            skeleton.hidden = false;
            fetch(next, { credentials: "same-origin" }).then(function (response) {
                return response.text();
            }).then(function (html) {
                var parsed = new DOMParser().parseFromString(html, "text/html");
                var rows = parsed.querySelectorAll("#result_list tbody tr");
                var body = table.querySelector("tbody");
                Array.prototype.forEach.call(rows, function (row) {
                    body.appendChild(document.importNode(row, true));
                });
                document.dispatchEvent(new Event("admin-mobile:rows-added"));
                next = null;
                paginator.hidden = true;
            }).finally(function () {
                skeleton.hidden = true;
                busy = false;
            });
        }
        window.addEventListener("scroll", function () {
            if (window.innerHeight + window.scrollY > document.body.offsetHeight - 120) {
                load();
            }
        }, { passive: true });
    }

    function applyCardConfig() {
        var node = document.getElementById("admin-mobile-card-config");
        if (!node) {
            return;
        }
        var cfgCard;
        try {
            cfgCard = JSON.parse(node.textContent || "{}");
        } catch (error) {
            return;
        }
        function fieldOf(cell) {
            var match = /(?:^|\s)field-([A-Za-z0-9_]+)/.exec(cell.className || "");
            return match ? match[1] : "";
        }
        document.querySelectorAll("#result_list tbody tr").forEach(function (row) {
            Array.prototype.forEach.call(row.children, function (cell) {
                var name = fieldOf(cell);
                if (!name) {
                    return;
                }
                if (name === cfgCard.title) {
                    cell.classList.add("admin-mobile-card-title");
                }
                if (name === cfgCard.subtitle) {
                    cell.classList.add("admin-mobile-card-subtitle");
                }
                if (name === cfgCard.image) {
                    cell.classList.add("admin-mobile-card-image");
                }
                var keep = !cfgCard.fields || !cfgCard.fields.length || cfgCard.fields.indexOf(name) !== -1 || name === cfgCard.title || name === cfgCard.subtitle || name === cfgCard.image;
                if (!keep) {
                    cell.classList.add("admin-mobile-card-extra");
                }
            });
        });
    }

    function initKeyboards() {
        if (!cfg.keyboards || !mobile()) {
            return;
        }
        document.querySelectorAll("input").forEach(function (el) {
            var name = (el.getAttribute("name") || "").toLowerCase();
            if (el.type === "email") {
                el.setAttribute("inputmode", "email");
                el.setAttribute("autocomplete", "email");
            } else if (el.type === "url") {
                el.setAttribute("inputmode", "url");
                el.setAttribute("autocomplete", "url");
            } else if (el.classList.contains("vIntegerField") || el.classList.contains("vBigIntegerField")) {
                el.setAttribute("inputmode", "numeric");
            } else if (el.classList.contains("vDecimalField") || el.classList.contains("vFloatField")) {
                el.setAttribute("inputmode", "decimal");
            } else if (name.indexOf("phone") !== -1 || name.indexOf("tel") !== -1) {
                el.setAttribute("inputmode", "tel");
                el.setAttribute("autocomplete", "tel");
            }
        });
    }

    function initGuard() {
        if (!cfg.unsaved && !cfg.drafts) {
            return;
        }
        document.querySelectorAll("form").forEach(function (form) {
            if (form.id === "logout-form" || form.id === "changelist-form") {
                return;
            }
            var fields = Array.prototype.filter.call(form.elements, function (el) {
                return el.name && el.type !== "hidden" && el.type !== "password" && el.type !== "file";
            });
            function snapshot() {
                return fields.map(function (el) {
                    var stored = el.type === "checkbox" ? String(el.checked) : el.value;
                return el.name + "=" + encodeURIComponent(stored);
                }).join("&");
            }
            var initial = snapshot();
            var key = "admin-mobile-draft:" + location.pathname;
            if (cfg.drafts && location.pathname.indexOf("/add/") !== -1) {
                var saved = localStorage.getItem(key);
                if (saved && saved !== initial) {
                    var banner = document.createElement("div");
                    banner.className = "admin-mobile-toast";
                    banner.textContent = "Restore the saved draft?";
                    var restore = document.createElement("button");
                    restore.type = "button";
                    restore.textContent = "Restore";
                    restore.addEventListener("click", function () {
                        var parts = {};
                        saved.split("&").forEach(function (pair) {
                            var bits = pair.split("=");
                            parts[bits[0]] = decodeURIComponent(bits.slice(1).join("="));
                        });
                        fields.forEach(function (el) {
                            if (Object.prototype.hasOwnProperty.call(parts, el.name)) {
                                if (el.type === "checkbox") {
                                    el.checked = parts[el.name] === "true";
                                } else {
                                    el.value = parts[el.name];
                                }
                            }
                        });
                        banner.remove();
                    });
                    banner.appendChild(restore);
                    document.body.appendChild(banner);
                }
            }
            var dirty = false;
            form.addEventListener("input", function () {
                dirty = snapshot() !== initial;
                if (cfg.drafts) {
                    localStorage.setItem(key, snapshot());
                }
            });
            if (cfg.unsaved) {
                window.addEventListener("beforeunload", function (event) {
                    if (dirty && form.dataset.adminMobileSubmitting !== "1") {
                        event.preventDefault();
                        event.returnValue = "";
                    }
                });
            }
            form.addEventListener("submit", function () {
                form.dataset.adminMobileSubmitting = "1";
                dirty = false;
                if (cfg.drafts) {
                    localStorage.removeItem(key);
                }
            });
        });
    }

    function initDoubleSubmit() {
        if (!cfg.doubleSubmit) {
            return;
        }
        document.addEventListener("submit", function (event) {
            if (event.defaultPrevented) {
                return;
            }
            var form = event.target;
            if (!(form instanceof HTMLFormElement) || form.dataset.adminMobileGuard === "1") {
                return;
            }
            form.dataset.adminMobileGuard = "1";
            Array.prototype.forEach.call(form.querySelectorAll("[type=submit]"), function (button) {
                button.disabled = true;
                button.classList.add("admin-mobile-busy");
            });
        });
        window.addEventListener("pageshow", function (event) {
            if (!event.persisted) {
                return;
            }
            document.querySelectorAll("form").forEach(function (form) {
                delete form.dataset.adminMobileGuard;
                Array.prototype.forEach.call(form.querySelectorAll("[type=submit]"), function (button) {
                    button.disabled = false;
                    button.classList.remove("admin-mobile-busy");
                });
            });
        });
    }

    function initUndoAndSlide() {
        if (!cfg.undoDelete && !cfg.swipeConfirm) {
            return;
        }
        document.addEventListener("submit", function (event) {
            var form = event.target;
            if (!(form instanceof HTMLFormElement) || form.dataset.adminMobileBypass === "1") {
                return;
            }
            var deletePage = document.body.classList.contains("delete-confirmation");
            var action = form.querySelector("[name=action]");
            var actionName = action ? action.value : "";
            var needsSlide = cfg.swipeConfirm && (deletePage || (cfg.swipeConfirmActions || []).indexOf(actionName) !== -1);
            var needsUndo = cfg.undoDelete && deletePage && form.querySelector("input[name=post]");
            if (needsSlide && form.dataset.adminMobileSlideOk !== "1") {
                event.preventDefault();
                openSlide(function () {
                    form.dataset.adminMobileSlideOk = "1";
                    if (needsUndo) {
                        startUndo(form);
                    } else {
                        form.dataset.adminMobileBypass = "1";
                        form.submit();
                    }
                });
                return;
            }
            if (needsUndo && form.dataset.adminMobileUndoOk !== "1") {
                event.preventDefault();
                startUndo(form);
            }
        }, true);
    }

    function openSlide(done) {
        var panel = sheet("admin-mobile-sheet");
        panel.hidden = false;
        var control = document.createElement("div");
        control.className = "admin-mobile-slide";
        control.tabIndex = 0;
        control.setAttribute("role", "slider");
        control.setAttribute("aria-valuemin", "0");
        control.setAttribute("aria-valuemax", "100");
        control.setAttribute("aria-valuenow", "0");
        control.setAttribute("aria-label", "Slide to confirm");
        var label = document.createElement("span");
        label.textContent = "Slide to confirm";
        var knob = document.createElement("span");
        knob.className = "admin-mobile-slide-knob";
        control.appendChild(label);
        control.appendChild(knob);
        panel.appendChild(control);
        var value = 0;
        function setValue(next) {
            value = Math.max(0, Math.min(100, next));
            control.setAttribute("aria-valuenow", String(value));
            knob.style.transform = "translateX(" + (value * 2) + "px)";
            if (value >= 100) {
                panel.hidden = true;
                done();
            }
        }
        control.addEventListener("keydown", function (event) {
            if (event.key === "ArrowRight") {
                setValue(value + 20);
            }
            if (event.key === "Enter" && value >= 100) {
                done();
            }
        });
        var origin = 0;
        control.addEventListener("pointerdown", function (event) {
            origin = event.clientX;
            control.setPointerCapture(event.pointerId);
        });
        control.addEventListener("pointermove", function (event) {
            if (!control.hasPointerCapture(event.pointerId)) {
                return;
            }
            setValue((event.clientX - origin) / 2);
        });
        closeOnEscape(panel);
        control.focus();
    }

    function startUndo(form) {
        var toast = document.createElement("div");
        toast.className = "admin-mobile-toast";
        toast.textContent = "Удалено — ";
        var undo = document.createElement("button");
        undo.type = "button";
        undo.textContent = "Отменить";
        toast.appendChild(undo);
        document.body.appendChild(toast);
        vibrate(20);
        var seconds = Number(cfg.undoSeconds) || 8;
        var timer = window.setTimeout(function () {
            form.dataset.adminMobileUndoOk = "1";
            form.dataset.adminMobileBypass = "1";
            form.submit();
        }, Math.min(10, Math.max(5, seconds)) * 1000);
        undo.addEventListener("click", function () {
            window.clearTimeout(timer);
            toast.remove();
        });
    }

    function initLightbox() {
        if (!cfg.lightbox) {
            return;
        }
        document.addEventListener("click", function (event) {
            var image = event.target.closest ? event.target.closest("img") : null;
            if (!image || image.closest("#header, .calendarbox, .clockbox")) {
                return;
            }
            if (image.width < 40 && !image.classList.contains("admin-mobile-thumb")) {
                return;
            }
            event.preventDefault();
            var dialog = sheet("admin-mobile-lightbox-dialog");
            dialog.hidden = false;
            var close = document.createElement("button");
            close.type = "button";
            close.className = "admin-mobile-lightbox-close";
            close.textContent = "Close";
            var preview = document.createElement("img");
            preview.src = image.currentSrc || image.src;
            preview.alt = image.alt || "";
            dialog.appendChild(close);
            dialog.appendChild(preview);
            var scale = 1;
            var start = 0;
            preview.addEventListener("touchstart", function (touchEvent) {
                if (touchEvent.touches.length === 2) {
                    var dx = touchEvent.touches[0].clientX - touchEvent.touches[1].clientX;
                    var dy = touchEvent.touches[0].clientY - touchEvent.touches[1].clientY;
                    start = Math.hypot(dx, dy);
                }
            }, { passive: true });
            preview.addEventListener("touchmove", function (touchEvent) {
                if (touchEvent.touches.length === 2 && start) {
                    var dx = touchEvent.touches[0].clientX - touchEvent.touches[1].clientX;
                    var dy = touchEvent.touches[0].clientY - touchEvent.touches[1].clientY;
                    scale = Math.min(4, Math.max(1, Math.hypot(dx, dy) / start));
                    preview.style.transform = "scale(" + scale + ")";
                } else if (touchEvent.touches.length === 1 && scale === 1 && touchEvent.touches[0].clientY > 120) {
                    dialog.hidden = true;
                }
            }, { passive: true });
            close.addEventListener("click", function () { dialog.hidden = true; });
            closeOnEscape(dialog);
            close.focus();
        });
    }

    function initNavigator() {
        if (!cfg.navigator || !mobile()) {
            return;
        }
        var headings = document.querySelectorAll("fieldset h2, .inline-heading, .inline-group > h2, .inline-related h2");
        if (headings.length < 2) {
            return;
        }
        var button = document.createElement("button");
        button.type = "button";
        button.className = "admin-mobile-sheet-close";
        button.textContent = "Sections";
        button.style.position = "fixed";
        button.style.zIndex = "50";
        button.style.right = "12px";
        button.style.bottom = "calc(var(--am-bar) + 12px)";
        button.addEventListener("click", function () {
            var panel = sheet("admin-mobile-navigator");
            panel.hidden = false;
            Array.prototype.forEach.call(headings, function (heading) {
                var jump = document.createElement("button");
                jump.type = "button";
                jump.textContent = (heading.textContent || "").trim().slice(0, 80);
                jump.addEventListener("click", function () {
                    heading.scrollIntoView({ block: "start" });
                    panel.hidden = true;
                });
                panel.appendChild(jump);
            });
            closeOnEscape(panel);
        });
        document.body.appendChild(button);
    }

    function initPickers() {
        if (!cfg.pickers || !mobile()) {
            return;
        }
        document.addEventListener("pointerdown", function (event) {
            var select = event.target.closest ? event.target.closest("select") : null;
            if (!select || select.multiple || select.name === "action" || select.closest(".admin-mobile-sort, .admin-mobile-picker, #changelist-filter")) {
                return;
            }
            event.preventDefault();
            if (select.classList.contains("admin-autocomplete")) {
                openAutocomplete(select);
            } else {
                openSelect(select);
            }
        }, true);
    }

    function openSelect(select) {
        var panel = sheet("admin-mobile-picker");
        panel.hidden = false;
        var search = document.createElement("input");
        search.type = "search";
        search.setAttribute("aria-label", "Filter choices");
        panel.appendChild(search);
        function render() {
            Array.prototype.slice.call(panel.querySelectorAll("button")).forEach(function (node) {
                node.remove();
            });
            var query = search.value.toLowerCase();
            Array.prototype.forEach.call(select.options, function (option) {
                if (query && option.text.toLowerCase().indexOf(query) === -1) {
                    return;
                }
                var choice = document.createElement("button");
                choice.type = "button";
                choice.textContent = option.text;
                choice.addEventListener("click", function () {
                    select.value = option.value;
                    select.dispatchEvent(new Event("change", { bubbles: true }));
                    panel.hidden = true;
                });
                panel.appendChild(choice);
            });
        }
        search.addEventListener("input", render);
        render();
        closeOnEscape(panel);
        search.focus();
    }

    function openAutocomplete(select) {
        var panel = sheet("admin-mobile-picker");
        panel.hidden = false;
        var search = document.createElement("input");
        search.type = "search";
        search.setAttribute("aria-label", "Search records");
        panel.appendChild(search);
        var endpoint = select.getAttribute("data-ajax--url");
        function render(items) {
            Array.prototype.slice.call(panel.querySelectorAll("button")).forEach(function (node) {
                node.remove();
            });
            items.forEach(function (item) {
                var choice = document.createElement("button");
                choice.type = "button";
                choice.textContent = item.text;
                choice.addEventListener("click", function () {
                    var option = new Option(item.text, item.id, true, true);
                    select.appendChild(option);
                    select.dispatchEvent(new Event("change", { bubbles: true }));
                    panel.hidden = true;
                });
                panel.appendChild(choice);
            });
        }
        function query() {
            var local = endpoint.charAt(0) === "/";
            var same = endpoint.indexOf(location.origin) === 0;
            if (!endpoint || (!local && !same)) {
                return;
            }
            var url = new URL(endpoint, location.origin);
            url.searchParams.set("term", search.value);
            url.searchParams.set("page", "1");
            url.searchParams.set("app_label", select.dataset.appLabel || "");
            url.searchParams.set("model_name", select.dataset.modelName || "");
            url.searchParams.set("field_name", select.dataset.fieldName || "");
            fetch(url.toString(), {
                credentials: "same-origin",
                headers: { "X-Requested-With": "XMLHttpRequest" }
            }).then(function (response) {
                return response.json();
            }).then(function (payload) {
                render(payload.results || []);
            }).catch(function () {
                render([]);
            });
        }
        search.addEventListener("input", query);
        closeOnEscape(panel);
        search.focus();
    }

    function initCamera() {
        if (!cfg.camera || !mobile()) {
            return;
        }
        document.querySelectorAll("input[type=file]").forEach(function (input) {
            if (input.dataset.adminMobileCamera === "1") {
                return;
            }
            input.dataset.adminMobileCamera = "1";
            var camera = document.createElement("input");
            camera.type = "file";
            camera.accept = "image/*";
            camera.capture = "environment";
            camera.hidden = true;
            var button = document.createElement("button");
            button.type = "button";
            button.className = "button";
            button.textContent = "Camera";
            button.addEventListener("click", function () { camera.click(); });
            var preview = document.createElement("img");
            preview.className = "admin-mobile-thumb";
            preview.alt = "";
            preview.hidden = true;
            function show(file) {
                if (!file || file.type.indexOf("image/") !== 0) {
                    return;
                }
                var reader = new FileReader();
                reader.onload = function () {
                    preview.src = String(reader.result || "");
                    preview.hidden = false;
                };
                reader.readAsDataURL(file);
            }
            function assign(file) {
                var transfer = new DataTransfer();
                transfer.items.add(file);
                input.files = transfer.files;
                show(file);
            }
            camera.addEventListener("change", function () {
                var file = camera.files && camera.files[0];
                if (!file) {
                    return;
                }
                if (!cfg.compress || file.type.indexOf("image/") !== 0) {
                    assign(file);
                    return;
                }
                var image = new Image();
                image.onload = function () {
                    var scale = Math.min(1, 1600 / Math.max(image.width, image.height));
                    var canvas = document.createElement("canvas");
                    canvas.width = Math.max(1, Math.round(image.width * scale));
                    canvas.height = Math.max(1, Math.round(image.height * scale));
                    var context = canvas.getContext("2d");
                    if (!context) {
                        assign(file);
                        return;
                    }
                    context.drawImage(image, 0, 0, canvas.width, canvas.height);
                    canvas.toBlob(function (blob) {
                        if (!blob) {
                            assign(file);
                            return;
                        }
                        assign(new File([blob], "capture.jpg", { type: "image/jpeg" }));
                    }, "image/jpeg", 0.8);
                };
                image.src = URL.createObjectURL(file);
            });
            input.addEventListener("change", function () {
                show(input.files && input.files[0]);
            });
            input.insertAdjacentElement("afterend", preview);
            input.insertAdjacentElement("afterend", button);
            input.insertAdjacentElement("afterend", camera);
        });
    }

    function initToasts() {
        if (!cfg.haptics) {
            return;
        }
        document.querySelectorAll(".messagelist").forEach(function (list) {
            list.classList.add("admin-mobile-toast-list");
            vibrate(12);
            window.setTimeout(function () { list.remove(); }, 4000);
        });
        document.addEventListener("click", function (event) {
            var target = event.target.closest ? event.target.closest("[name=_save], [name=_continue], [name=_addanother]") : null;
            if (target) {
                vibrate(10);
            }
        });
    }

    function initServiceWorker() {
        if (!cfg.pwa || !cfg.swUrl || !("serviceWorker" in navigator) || !mobile()) {
            return;
        }
        navigator.serviceWorker.register(cfg.swUrl, { scope: "/admin/" }).catch(function () {
            return null;
        });
    }

    var cfg = {};

    onReady(function () {
        cfg = readConfig();
        syncViewportCookie();
        var media = window.matchMedia(MOBILE_MQ);
        if (media.addEventListener) {
            media.addEventListener("change", syncViewportCookie);
        }
        var observer = new MutationObserver(syncViewportCookie);
        observer.observe(root, { attributes: true, attributeFilter: ["data-theme"] });
        initHeader();
        initTabs();
        initFavoriteButton();
        initFilterBadge();
        initBulk();
        initSwipe();
        initPull();
        initInfinite();
        applyCardConfig();
        initKeyboards();
        initGuard();
        initDoubleSubmit();
        initUndoAndSlide();
        initLightbox();
        initNavigator();
        initPickers();
        initCamera();
        initToasts();
        initServiceWorker();
        document.addEventListener("admin-mobile:rows-added", function () {
            applyCardConfig();
            initSwipe();
        });
    });
})();
