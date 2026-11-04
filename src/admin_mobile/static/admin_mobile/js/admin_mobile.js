/*
 * Labels come from column headers so card CSS can use attr(data-label).
 * The empty inline row is labeled too: inlines.js clones it, data-label included.
 * MOBILE_MQ must stay in sync with the 600px queries in admin_mobile.css.
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

    function cleanText(value) {
        return (value || "").replace(/\s+/g, " ").trim();
    }

    function selectLabel() {
        return root.getAttribute("data-admin-mobile-select-label") || "Select";
    }

    function filtersLabel() {
        return root.getAttribute("data-admin-mobile-filters-label") || "Filters";
    }

    function headerLabel(headerCell) {
        if (!headerCell) {
            return "";
        }
        if (headerCell.classList.contains("action-checkbox-column")) {
            return selectLabel();
        }
        var textRoot = headerCell.querySelector(".text") || headerCell;
        var text = cleanText(textRoot.textContent);
        if (text) {
            return text;
        }
        var input = headerCell.querySelector("input");
        if (input) {
            return cleanText(input.getAttribute("aria-label")) || selectLabel();
        }
        return "";
    }

    function headerLabels(table) {
        var headRow = table.querySelector("thead tr");
        if (!headRow) {
            return [];
        }
        return Array.prototype.map.call(
            headRow.querySelectorAll(":scope > th, :scope > td"),
            headerLabel
        );
    }

    function labelRow(row, labels) {
        var cells = row.querySelectorAll(":scope > th, :scope > td");
        Array.prototype.forEach.call(cells, function (cell, index) {
            var label = labels[index] || "";
            if (label) {
                cell.setAttribute("data-label", label);
            } else {
                cell.removeAttribute("data-label");
            }
        });
    }

    function labelTable(table) {
        var labels = headerLabels(table);
        if (!labels.length) {
            return;
        }
        Array.prototype.forEach.call(table.querySelectorAll("tbody tr"), function (row) {
            if (row.classList.contains("row-form-errors")) {
                return;
            }
            labelRow(row, labels);
        });
    }

    function safeHref(link) {
        var raw = link.getAttribute("href") || "";
        if (!raw || raw.indexOf("javascript:") === 0) {
            return "";
        }
        return raw;
    }

    function initSortBar(table) {
        var parent = table.parentElement;
        if (!parent || parent.querySelector(".admin-mobile-sort")) {
            return;
        }
        var links = table.querySelectorAll("thead a[href]");
        if (!links.length) {
            return;
        }
        var bar = document.createElement("label");
        bar.className = "admin-mobile-sort";
        var caption = document.createElement("span");
        caption.textContent = root.getAttribute("data-admin-mobile-sort-label") || "Sort by";
        var select = document.createElement("select");
        select.setAttribute("aria-label", caption.textContent || "Sort by");
        var placeholder = document.createElement("option");
        placeholder.value = "";
        placeholder.textContent = caption.textContent || "Sort by";
        select.appendChild(placeholder);
        var seen = {};
        Array.prototype.forEach.call(links, function (link) {
            var text = cleanText(link.textContent);
            var href = safeHref(link);
            if (!text || !href || seen[text]) {
                return;
            }
            seen[text] = true;
            var option = document.createElement("option");
            option.value = href;
            option.textContent = text;
            select.appendChild(option);
        });
        if (select.options.length < 2) {
            return;
        }
        select.addEventListener("change", function () {
            if (select.value) {
                window.location.assign(select.value);
            }
        });
        bar.appendChild(caption);
        bar.appendChild(select);
        table.insertAdjacentElement("beforebegin", bar);
    }

    function initSelectAll(table) {
        var toggle = document.getElementById("action-toggle");
        var parent = table.parentElement;
        if (!toggle || !parent || parent.querySelector(".admin-mobile-select-all")) {
            return;
        }
        var label = document.createElement("label");
        label.className = "admin-mobile-select-all";
        var input = document.createElement("input");
        input.type = "checkbox";
        input.id = "admin-mobile-select-all";
        label.appendChild(input);
        label.appendChild(document.createTextNode(" " + selectLabel()));
        table.insertAdjacentElement("beforebegin", label);
        input.addEventListener("change", function () {
            if (toggle.checked !== input.checked) {
                toggle.click();
            }
        });
        toggle.addEventListener("change", function () {
            input.checked = toggle.checked;
        });
    }

    function initChangelist() {
        if (!root.classList.contains("admin-mobile-cards")) {
            return;
        }
        var table = document.getElementById("result_list");
        if (!table) {
            return;
        }
        labelTable(table);
        initSortBar(table);
        initSelectAll(table);
    }

    function initRecordTables() {
        if (!root.classList.contains("admin-mobile-cards")) {
            return;
        }
        var tables = document.querySelectorAll("#change-history table, table.model");
        Array.prototype.forEach.call(tables, labelTable);
    }

    function initInlines() {
        if (!root.classList.contains("admin-mobile-inlines")) {
            return;
        }
        var tables = document.querySelectorAll(
            ".inline-group[data-inline-type='tabular'] table, .inline-related.tabular table"
        );
        Array.prototype.forEach.call(tables, labelTable);
    }

    function initNavDrawer() {
        var sidebar = document.getElementById("nav-sidebar");
        var main = document.getElementById("main");
        if (!sidebar || !main || !window.matchMedia(MOBILE_MQ).matches) {
            return;
        }
        // Django stores the drawer as open. On a phone that covers the page.
        main.classList.remove("shifted");
        sidebar.setAttribute("aria-expanded", "false");
    }

    function initFilters() {
        if (!root.classList.contains("admin-mobile-filters")) {
            return;
        }
        var sidebar = document.getElementById("changelist-filter");
        if (!sidebar || sidebar.getAttribute("data-admin-mobile-ready") === "1") {
            return;
        }
        sidebar.setAttribute("data-admin-mobile-ready", "1");

        var button = document.createElement("button");
        button.type = "button";
        button.className = "admin-mobile-filter-toggle";
        button.id = "admin-mobile-filter-toggle";
        button.setAttribute("aria-controls", "changelist-filter");
        var heading = sidebar.querySelector("h2, h3, summary");
        button.textContent = heading ? cleanText(heading.textContent) || filtersLabel() : filtersLabel();
        sidebar.insertAdjacentElement("beforebegin", button);

        var media = window.matchMedia(MOBILE_MQ);

        function sync(open) {
            if (!media.matches) {
                sidebar.hidden = false;
                sidebar.classList.remove("admin-mobile-open");
                button.hidden = true;
                button.setAttribute("aria-expanded", "true");
                return;
            }
            var isOpen = open === true;
            sidebar.classList.toggle("admin-mobile-open", isOpen);
            sidebar.hidden = !isOpen;
            button.hidden = false;
            button.setAttribute("aria-expanded", isOpen ? "true" : "false");
        }

        button.addEventListener("click", function () {
            sync(!sidebar.classList.contains("admin-mobile-open"));
        });

        if (typeof media.addEventListener === "function") {
            media.addEventListener("change", function () {
                sync(false);
            });
        } else if (typeof media.addListener === "function") {
            media.addListener(function () {
                sync(false);
            });
        }
        sync(false);
    }

    document.addEventListener("formset:added", function (event) {
        if (!root.classList.contains("admin-mobile-inlines")) {
            return;
        }
        var row = event.target;
        if (!row || typeof row.closest !== "function") {
            return;
        }
        var table = row.closest("table");
        if (table) {
            labelTable(table);
        }
    });

    onReady(function () {
        initChangelist();
        initRecordTables();
        initInlines();
        initFilters();
        initNavDrawer();
    });
})();
