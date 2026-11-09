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

    function iconSvg(paths) {
        return (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="22" height="22" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
            paths +
            "</svg>"
        );
    }

    var TAB_ICONS = {
        home: iconSvg('<path d="M4 10.5 12 4l8 6.5V20a1 1 0 0 1-1 1h-5v-6H10v6H5a1 1 0 0 1-1-1z"/>'),
        search: iconSvg('<circle cx="11" cy="11" r="6"/><path d="m20 20-3.5-3.5"/>'),
        recent: iconSvg('<circle cx="12" cy="12" r="8"/><path d="M12 8v5l3 2"/>'),
        saved: iconSvg('<path d="m12 3 2.6 5.3L20 9.2l-4 3.9.9 5.6L12 16.8 7.1 18.7 8 13.1 4 9.2l5.4-.9z"/>'),
        account: iconSvg('<circle cx="12" cy="8" r="3.2"/><path d="M5 19.2c1.4-3 3.8-4.4 7-4.4s5.6 1.4 7 4.4"/>')
    };

    function fillIconButton(control, iconName, label) {
        control.innerHTML = TAB_ICONS[iconName] + "<span></span>";
        var caption = control.querySelector("span");
        if (caption) {
            caption.textContent = label;
        }
    }

    function initHeader() {
        var header = document.getElementById("header");
        if (!header || !mobile() || header.querySelector(".admin-mobile-user")) {
            return;
        }
        var toggle = document.getElementById("toggle-nav-sidebar");
        if (toggle) {
            header.insertBefore(toggle, header.firstChild);
        }
        var tools = document.getElementById("user-tools");
        if (!tools) {
            return;
        }
        var theme = tools.querySelector(".theme-toggle");
        var panel = sheet("admin-mobile-sheet admin-mobile-user-sheet");
        var welcome = document.createElement("p");
        welcome.className = "admin-mobile-welcome";
        var welcomeText = [];
        Array.prototype.slice.call(tools.childNodes).forEach(function (node) {
            if (theme && node === theme) {
                return;
            }
            if (node.nodeType === 3 || (node.nodeType === 1 && node.tagName === "STRONG")) {
                var text = (node.textContent || "").replace(/\s*\/\s*/g, " ").replace(/\s+/g, " ").trim();
                if (text) {
                    welcomeText.push(text);
                }
                return;
            }
            if (node.nodeType === 1) {
                panel.appendChild(node);
            }
        });
        if (welcomeText.length) {
            welcome.textContent = welcomeText.join(" ").replace(/\s+\./g, ".").replace(/\s+/g, " ").trim();
            panel.insertBefore(welcome, panel.firstChild);
        }
        var close = document.createElement("button");
        close.type = "button";
        close.className = "admin-mobile-sheet-close";
        close.textContent = "Close";
        close.addEventListener("click", function () {
            panel.hidden = true;
        });
        panel.appendChild(close);
        var menu = document.createElement("button");
        menu.type = "button";
        menu.className = "admin-mobile-user";
        menu.setAttribute("aria-label", "Account");
        menu.setAttribute("aria-expanded", "false");
        menu.innerHTML = TAB_ICONS.account;
        menu.addEventListener("click", function () {
            panel.hidden = false;
            menu.setAttribute("aria-expanded", "true");
            closeOnEscape(panel);
            close.focus();
        });
        tools.classList.add("admin-mobile-user-source");
        tools.hidden = true;
        header.appendChild(menu);
        if (theme) {
            header.appendChild(theme);
        }
    }

    function samePath(href) {
        try {
            return new URL(href, location.origin).pathname === location.pathname;
        } catch (error) {
            return false;
        }
    }

    function initTabs() {
        if (!cfg.tabs || !mobile() || document.querySelector(".admin-mobile-tabbar")) {
            return;
        }
        var bar = document.createElement("nav");
        bar.id = "admin-mobile-tabbar";
        bar.className = "admin-mobile-tabbar";
        bar.setAttribute("aria-label", "Admin");
        function link(href, text, iconName) {
            var anchor = document.createElement("a");
            anchor.href = href;
            anchor.className = "admin-mobile-tab";
            fillIconButton(anchor, iconName, text);
            if (samePath(href)) {
                anchor.setAttribute("aria-current", "page");
            }
            return anchor;
        }
        bar.appendChild(link("/admin/", "Home", "home"));
        if (cfg.searchUrl) {
            bar.appendChild(link(cfg.searchUrl, "Search", "search"));
        }
        if (cfg.recentUrl) {
            bar.appendChild(link(cfg.recentUrl, "Recent", "recent"));
        }
        var saved = document.createElement("button");
        saved.type = "button";
        saved.className = "admin-mobile-tab";
        fillIconButton(saved, "saved", "Saved");
        saved.addEventListener("click", function () {
            saved.setAttribute("aria-pressed", "true");
            openFavorites();
        });
        bar.appendChild(saved);
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
        var changelist = document.getElementById("changelist");
        var toolbar = document.getElementById("toolbar");
        if (toolbar) {
            toolbar.insertAdjacentElement("afterend", button);
            return;
        }
        if (changelist) {
            changelist.insertAdjacentElement("afterbegin", button);
            return;
        }
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
        var count = sidebar.querySelectorAll("li.selected a").length;
        if (!count) {
            return;
        }
        var badge = document.createElement("span");
        badge.className = "admin-mobile-filter-badge";
        badge.textContent = String(count);
        button.appendChild(badge);
    }

    function splitFilterCounts(sidebar) {
        Array.prototype.forEach.call(sidebar.querySelectorAll("li a"), function (link) {
            if (link.querySelector(".admin-mobile-filter-count")) {
                return;
            }
            var text = (link.textContent || "").replace(/\s+/g, " ").trim();
            var match = /^(.*)\s\((\d+)\)$/.exec(text);
            if (!match) {
                return;
            }
            link.textContent = "";
            var name = document.createElement("span");
            name.className = "admin-mobile-filter-choice";
            name.textContent = match[1];
            var count = document.createElement("span");
            count.className = "admin-mobile-filter-count";
            count.textContent = match[2];
            link.appendChild(name);
            link.appendChild(count);
        });
    }

    function addFilterSearch(sidebar) {
        Array.prototype.forEach.call(sidebar.querySelectorAll("details"), function (details) {
            var list = details.querySelector("ul");
            if (!list || details.querySelector(".admin-mobile-filter-search")) {
                return;
            }
            var items = Array.prototype.filter.call(list.children, function (node) {
                return node.tagName === "LI";
            });
            if (items.length < 6) {
                return;
            }
            var input = document.createElement("input");
            input.type = "search";
            input.className = "admin-mobile-filter-search";
            input.placeholder = "Search";
            input.setAttribute("aria-label", "Search filters");
            input.addEventListener("input", function () {
                var query = input.value.trim().toLowerCase();
                items.forEach(function (item) {
                    var label = (item.textContent || "").toLowerCase();
                    item.hidden = query !== "" && label.indexOf(query) === -1;
                });
            });
            list.insertAdjacentElement("beforebegin", input);
        });
    }

    function initFilterSheet() {
        if (!cfg.filterSheet) {
            return;
        }
        var button = document.getElementById("admin-mobile-filter-toggle");
        var sidebar = document.getElementById("changelist-filter");
        if (!button || !sidebar || sidebar.getAttribute("data-admin-mobile-sheet") === "1") {
            return;
        }
        sidebar.setAttribute("data-admin-mobile-sheet", "1");

        var backdrop = document.createElement("div");
        backdrop.className = "admin-mobile-filter-backdrop";
        backdrop.hidden = true;
        document.body.appendChild(backdrop);

        var chrome = document.createElement("div");
        chrome.className = "admin-mobile-filter-chrome";
        var handle = document.createElement("span");
        handle.className = "admin-mobile-filter-handle";
        handle.setAttribute("aria-hidden", "true");
        var head = document.createElement("div");
        head.className = "admin-mobile-filter-head";
        var title = document.createElement("p");
        title.className = "admin-mobile-filter-title";
        title.id = "admin-mobile-filter-title";
        title.textContent = root.getAttribute("data-admin-mobile-filters-label") || "Filters";
        var reset = document.createElement("a");
        reset.className = "admin-mobile-filter-reset";
        reset.textContent = "Reset";
        var clear = sidebar.querySelector(
            "#changelist-filter-clear a, #changelist-filter-extra-actions a"
        );
        reset.href = clear ? clear.href : location.pathname;
        var close = document.createElement("button");
        close.type = "button";
        close.className = "admin-mobile-filter-close";
        close.setAttribute("aria-label", "Close");
        close.textContent = "\u00d7";
        head.appendChild(title);
        head.appendChild(reset);
        head.appendChild(close);
        chrome.appendChild(handle);
        chrome.appendChild(head);

        var body = document.createElement("div");
        body.className = "admin-mobile-filter-body";
        while (sidebar.firstChild) {
            body.appendChild(sidebar.firstChild);
        }
        var foot = document.createElement("div");
        foot.className = "admin-mobile-filter-foot";
        var apply = document.createElement("button");
        apply.type = "button";
        apply.className = "admin-mobile-filter-apply";
        apply.textContent = "Show results";
        foot.appendChild(apply);
        sidebar.appendChild(chrome);
        sidebar.appendChild(body);
        sidebar.appendChild(foot);
        sidebar.setAttribute("aria-labelledby", "admin-mobile-filter-title");

        splitFilterCounts(body);
        addFilterSearch(body);

        function closeSheet() {
            if (sidebar.classList.contains("admin-mobile-open")) {
                button.click();
            }
        }

        function sync() {
            var open = sidebar.classList.contains("admin-mobile-open") && mobile();
            backdrop.hidden = !open;
            document.body.classList.toggle("admin-mobile-filter-locked", open);
        }

        button.addEventListener("click", function () {
            window.setTimeout(sync, 0);
        });
        close.addEventListener("click", closeSheet);
        apply.addEventListener("click", closeSheet);
        backdrop.addEventListener("click", closeSheet);
        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape") {
                closeSheet();
            }
        });
        var media = window.matchMedia(MOBILE_MQ);
        if (typeof media.addEventListener === "function") {
            media.addEventListener("change", sync);
        }
        sync();
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
        label.className = "admin-mobile-bulk-count";
        var select = actions.querySelector("select");
        var run = actions.querySelector("button, input[type=submit]");
        if (select) {
            var clone = select.cloneNode(true);
            clone.removeAttribute("id");
            clone.addEventListener("change", function () {
                select.value = clone.value;
            });
            bar.appendChild(label);
            bar.appendChild(clone);
        }
        if (run) {
            var runClone = run.cloneNode(true);
            runClone.type = "button";
            runClone.addEventListener("click", function () {
                var chosen = bar.querySelector("select");
                if (select && chosen) {
                    select.value = chosen.value;
                }
                if (typeof form.requestSubmit === "function") {
                    form.requestSubmit(run);
                } else {
                    run.click();
                }
            });
            bar.appendChild(runClone);
        }
        document.body.appendChild(bar);
        var actionRows = document.querySelectorAll("#changelist .actions");
        function refresh() {
            var selected = form.querySelectorAll("input.action-select:checked, .action-checkbox input:checked").length;
            label.textContent = "Selected " + selected;
            bar.hidden = selected === 0;
            Array.prototype.forEach.call(actionRows, function (row) {
                row.classList.toggle("admin-mobile-actions-delegated", selected > 0);
            });
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
        hint.hidden = true;
        var list = document.getElementById("result_list");
        list.parentElement.insertBefore(hint, list);
        var startY = 0;
        document.addEventListener("touchstart", function (event) {
            if (window.scrollY <= 0 && event.touches && event.touches[0]) {
                startY = event.touches[0].clientY;
            } else {
                startY = 0;
            }
        }, { passive: true });
        document.addEventListener("touchmove", function (event) {
            if (!startY || window.scrollY > 0 || !event.touches || !event.touches[0]) {
                return;
            }
            hint.hidden = event.touches[0].clientY - startY < 16;
        }, { passive: true });
        document.addEventListener("touchend", function (event) {
            if (!event.changedTouches || !event.changedTouches[0]) {
                return;
            }
            if (startY && window.scrollY <= 0 && event.changedTouches[0].clientY - startY > 80) {
                window.location.reload();
                return;
            }
            hint.hidden = true;
            startY = 0;
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

    function ensureCardTitle(row) {
        if (row.querySelector(":scope > .admin-mobile-card-title")) {
            return;
        }
        var link = row.querySelector(":scope > th a[href], :scope > td a[href]");
        var cell = link ? link.closest("th, td") : null;
        if (!cell || cell.classList.contains("action-checkbox")) {
            cell = null;
            Array.prototype.forEach.call(row.children, function (item) {
                if (!cell && (item.tagName === "TH" || item.tagName === "TD") && !item.classList.contains("action-checkbox")) {
                    cell = item;
                }
            });
        }
        if (cell) {
            cell.classList.add("admin-mobile-card-title");
        }
    }

    function applyCardConfig() {
        var node = document.getElementById("admin-mobile-card-config");
        var cfgCard = {};
        if (node) {
            try {
                cfgCard = JSON.parse(node.textContent || "{}");
            } catch (error) {
                cfgCard = {};
            }
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
            ensureCardTitle(row);
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
            var needsSlide = cfg.swipeConfirm && mobile() && (
                deletePage || (cfg.swipeConfirmActions || []).indexOf(actionName) !== -1
            );
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
        if (!mobile()) {
            done();
            return;
        }
        var panel = sheet("admin-mobile-sheet admin-mobile-slide-sheet");
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
        button.className = "admin-mobile-formnav";
        button.textContent = "Sections";
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

    var cameraFields = [];
    var cameraSubmitBound = false;

    function releaseClear(input) {
        if (!input.name) {
            return;
        }
        var clearName = input.name + "-clear";
        var boxes = [];
        function add(node) {
            if (!node) {
                return;
            }
            if (typeof node.length === "number" && node.type === undefined) {
                Array.prototype.forEach.call(node, add);
                return;
            }
            if (node.type === "checkbox" && boxes.indexOf(node) === -1) {
                boxes.push(node);
            }
        }
        if (input.form && input.form.elements) {
            add(input.form.elements.namedItem(clearName));
        }
        var root = input.closest(".iuw-root, .clearable-file-input");
        if (root) {
            Array.prototype.forEach.call(root.querySelectorAll("input[type=checkbox]"), function (box) {
                if (box.name === clearName) {
                    add(box);
                }
            });
        }
        boxes.forEach(function (box) {
            box.checked = false;
        });
    }

    function showCameraError(entry) {
        if (!entry.error) {
            entry.error = document.createElement("p");
            entry.error.className = "admin-mobile-camera-error";
            entry.error.setAttribute("role", "alert");
            entry.button.insertAdjacentElement("afterend", entry.error);
        }
        entry.error.textContent = "Could not attach this photo.";
    }

    function clearCameraError(entry) {
        if (!entry.error) {
            return;
        }
        entry.error.remove();
        entry.error = null;
    }

    function assignCameraFile(entry, file) {
        if (!file) {
            throw new Error("missing file");
        }
        var transfer = new DataTransfer();
        transfer.items.add(file);
        entry.input.files = transfer.files;
        if (!entry.input.files || !entry.input.files.length) {
            throw new Error("unassigned");
        }
        releaseClear(entry.input);
        // ImageUploaderWidget listens on document for a bubbling change and
        // reads the first file input inside .iuw-root.
        entry.input.dispatchEvent(new Event("change", { bubbles: true }));
        clearCameraError(entry);
    }

    function compressImage(file) {
        return new Promise(function (resolve, reject) {
            var url = URL.createObjectURL(file);
            var image = new Image();
            var settled = false;
            var timer = window.setTimeout(function () {
                fail(new Error("decode"));
            }, 8000);
            function finish(failed, value) {
                if (settled) {
                    return;
                }
                settled = true;
                window.clearTimeout(timer);
                URL.revokeObjectURL(url);
                if (failed) {
                    reject(value);
                    return;
                }
                resolve(value);
            }
            function fail(error) {
                finish(true, error);
            }
            image.onload = function () {
                if (settled) {
                    return;
                }
                try {
                    var width = image.naturalWidth || image.width;
                    var height = image.naturalHeight || image.height;
                    var canBlob = typeof HTMLCanvasElement !== "undefined"
                        && typeof HTMLCanvasElement.prototype.toBlob === "function";
                    if (!width || !height || !canBlob) {
                        finish(false, file);
                        return;
                    }
                    var scale = Math.min(1, 1600 / Math.max(width, height));
                    var canvas = document.createElement("canvas");
                    canvas.width = Math.max(1, Math.round(width * scale));
                    canvas.height = Math.max(1, Math.round(height * scale));
                    var context = canvas.getContext("2d");
                    if (!context || typeof canvas.toBlob !== "function") {
                        finish(false, file);
                        return;
                    }
                    context.drawImage(image, 0, 0, canvas.width, canvas.height);
                    canvas.toBlob(function (blob) {
                        if (!blob) {
                            finish(false, file);
                            return;
                        }
                        finish(false, new File([blob], "capture.jpg", { type: "image/jpeg" }));
                    }, "image/jpeg", 0.8);
                } catch (error) {
                    fail(error);
                }
            };
            image.onerror = function () {
                fail(new Error("decode"));
            };
            image.src = url;
        });
    }

    function bindCamera(input) {
        input.dataset.adminMobileCamera = "1";
        var camera = document.createElement("input");
        camera.type = "file";
        camera.accept = "image/*";
        camera.capture = "environment";
        camera.hidden = true;
        camera.dataset.adminMobileCameraSource = "1";
        // Nameless and after the real input. A name would be posted, and
        // ImageUploaderWidget always uses the first file input in .iuw-root.
        camera.removeAttribute("name");
        var button = document.createElement("button");
        button.type = "button";
        button.className = "button";
        button.textContent = "Camera";
        button.addEventListener("click", function () {
            camera.click();
        });
        var entry = {
            input: input,
            button: button,
            pending: null,
            generation: 0,
            error: null
        };
        cameraFields.push(entry);
        input.addEventListener("change", function (event) {
            if (!event.isTrusted) {
                return;
            }
            entry.generation += 1;
            entry.pending = null;
        });
        camera.addEventListener("change", function (event) {
            event.stopPropagation();
            var file = camera.files && camera.files[0];
            if (!file) {
                return;
            }
            var ticket = ++entry.generation;
            function commit(preferred) {
                if (ticket !== entry.generation || entry.pending !== file) {
                    return;
                }
                try {
                    assignCameraFile(entry, preferred);
                    entry.pending = null;
                } catch (error) {
                    if (preferred !== file) {
                        commit(file);
                        return;
                    }
                    showCameraError(entry);
                }
            }
            if (!cfg.compress || !file.type || file.type.indexOf("image/") !== 0) {
                entry.pending = file;
                commit(file);
                return;
            }
            entry.pending = file;
            compressImage(file).then(function (ready) {
                commit(ready || file);
            }).catch(function () {
                commit(file);
            });
        });
        input.insertAdjacentElement("afterend", button);
        input.insertAdjacentElement("afterend", camera);
    }

    function cancelCameraDrop(event) {
        var target = event.target;
        if (!target || !target.closest) {
            return;
        }
        var dropped = event.dataTransfer && event.dataTransfer.files;
        if (!dropped || !dropped.length) {
            return;
        }
        var root = target.closest(".iuw-root, .form-row");
        if (!root) {
            return;
        }
        cameraFields.forEach(function (entry) {
            if (!root.contains(entry.input)) {
                return;
            }
            entry.generation += 1;
            entry.pending = null;
        });
    }

    function flushCameraSubmit(event) {
        var form = event.target;
        if (!(form instanceof HTMLFormElement)) {
            return;
        }
        // The POST body is built after this event. Copy any photo still
        // waiting on decode or canvas so an empty ImageField cannot be saved.
        var blocked = false;
        cameraFields.forEach(function (entry) {
            if (!entry.pending || entry.input.form !== form || !entry.input.isConnected) {
                return;
            }
            var file = entry.pending;
            entry.generation += 1;
            try {
                assignCameraFile(entry, file);
                entry.pending = null;
            } catch (error) {
                blocked = true;
                showCameraError(entry);
            }
        });
        if (blocked) {
            event.preventDefault();
        }
    }

    function initCamera() {
        if (!cfg.camera || !mobile()) {
            return;
        }
        if (!cameraSubmitBound) {
            document.addEventListener("submit", flushCameraSubmit, true);
            document.addEventListener("drop", cancelCameraDrop, true);
            cameraSubmitBound = true;
        }
        document.querySelectorAll("input[type=file]").forEach(function (input) {
            if (input.dataset.adminMobileCamera === "1" || input.dataset.adminMobileCameraSource === "1") {
                return;
            }
            if (!input.name || input.closest(".empty-form")) {
                return;
            }
            bindCamera(input);
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

    function syncChromeStack() {
        var height = 0;
        if (mobile()) {
            var rows = document.querySelectorAll("#content-main > form .submit-row");
            var row = rows.length ? rows[rows.length - 1] : null;
            if (!row) {
                row = document.querySelector("body.delete-confirmation #content > form");
            }
            if (row) {
                height = Math.ceil(row.getBoundingClientRect().height);
            }
        }
        root.style.setProperty("--am-submit", height + "px");
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
        initFilterSheet();
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
        syncChromeStack();
        window.addEventListener("resize", syncChromeStack);
        window.requestAnimationFrame(syncChromeStack);
        initPickers();
        initCamera();
        initToasts();
        initServiceWorker();
        document.addEventListener("formset:added", function () {
            initCamera();
        });
        document.addEventListener("admin-mobile:rows-added", function () {
            applyCardConfig();
            initSwipe();
            initCamera();
        });
    });
})();
