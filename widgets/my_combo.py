from __future__ import annotations

from typing import Iterable

from PySide6.QtCore import (
    QEvent,
    QObject,
    QPoint,
    QRect,
    QSize,
    Qt,
    QTimer,
    Signal,
)
from PySide6.QtGui import (
    QCursor,
    QFocusEvent,
    QFontMetrics,
    QKeyEvent,
    QMouseEvent,
    QPainter,
    QPen,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSizePolicy,
    QStyle,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


class _CheckListWidget(QListWidget):
    """List widget where a click anywhere on a row toggles the check state."""

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            item = self.itemAt(event.position().toPoint())
            if item is not None and item.flags() & Qt.ItemIsUserCheckable:
                new_state = (Qt.Unchecked if item.checkState() == Qt.Checked
                             else Qt.Checked)
                item.setCheckState(new_state)
                self.setCurrentItem(item)
                event.accept()
                return
        super().mousePressEvent(event)


# --------------------------------------------------------------------------
# Default theme for :class:`MyCombo`. Pass a dict to ``__init__``
# (or :py:meth:`MyCombo.set_theme`) to override any subset.
# --------------------------------------------------------------------------
DEFAULT_THEME: dict[str, object] = {
    # -- main line edit / outer frame -------------------------------------
    "background":             "#ffffff",
    "text_color":             "#202124",
    "placeholder_color":      "#80868b",
    "border_color":           "#dadce0",   # outer frame, unfocused
    "border_color_focus":     "#1a73e8",   # outer frame, focused
    "border_width":           1,           # px
    "border_radius":          6,           # px
    "underline_color":        "#e8eaed",   # bottom line, unfocused
    "underline_color_focus":  "#1a73e8",   # bottom line, focused
    "underline_width":        2,           # px
    "arrow_color":            "#5f6368",
    "arrow_color_hover":      "#1a73e8",
    "selection_bg":           "#d2e3fc",
    "font_size":              13,          # px
    "padding":                "4px 6px 2px 10px",
    # -- popup frame ------------------------------------------------------
    "popup_background":       "#ffffff",
    "popup_border_color":     "#dadce0",
    "popup_border_width":     1,           # px
    "popup_border_radius":    8,           # px
    # -- list (checkable items) -------------------------------------------
    "list_background":        "#ffffff",
    "list_border_color":      "#e8eaed",
    "list_border_radius":     6,           # px
    "list_font_size":         13,          # px
    "list_item_padding":      "5px 6px",
    "list_item_hover_bg":     "#f1f3f4",
    "list_item_selected_bg":  "#e8f0fe",
    "list_item_selected_fg":  "#1a73e8",
    # -- popup buttons (全选/ 反选/ 取消) ------------------------------
    "btn_background":         "#ffffff",
    "btn_hover_bg":           "#f1f3f4",
    "btn_border_color":       "#dadce0",
    "btn_border_radius":      6,           # px
    "btn_padding":            "5px 12px",
    "btn_font_size":          13,          # px
    # primary = the "全选" button
    "btn_primary_bg":         "#1a73e8",
    "btn_primary_hover_bg":   "#1765cc",
    "btn_primary_color":      "white",
    "btn_primary_border":     "#1a73e8",
    # count label ("已选 N 项")
    "btn_hint_color":         "#5f6368",
    # -- popup search box (only shown when search_in_popup=True) -----------
    "search_background":      "#ffffff",
    "search_border_color":    "#dadce0",
    "search_border_focus":    "#1a73e8",
    "search_border_radius":   4,           # px
    "search_padding":         "4px 8px",
    "search_height":          28,          # px
}


# --------------------------------------------------------------------------
# Preset themes -- aliases of :data:`DEFAULT_THEME` plus a few overrides.
# Import them and pass to ``MyCombo(theme=...)`` or
# ``combo.set_theme(...)``.  Every preset is a *complete* dict, so once you
# import a preset you may freely tweak a single key without losing any
# other value.  See :data:`THEMES` for a ``name -> dict`` aggregator.
# --------------------------------------------------------------------------

# Google Material -- same as DEFAULT_THEME, kept for symmetry.
GOOGLE_THEME: dict[str, object] = {**DEFAULT_THEME}

# 腾讯蓝 (Tencent blue) -- squarer corners, larger font, blue accent
# evoking 腾讯文档 / TDesign.

TENCENT_THEME: dict[str, object] = {
    **DEFAULT_THEME,
    "text_color":             "#1f2329",
    "border_color":           "#dcdee2",
    "border_color_focus":     "#3370ff",   # 腾讯蓝
    "border_radius":          4,
    "underline_color":        "#dcdee2",
    "underline_color_focus":  "#3370ff",
    "arrow_color":            "#8c939c",
    "arrow_color_hover":      "#3370ff",
    "selection_bg":           "#d6e4ff",
    "font_size":              14,
    "padding":                "4px 11px 4px 11px",
    "popup_border_color":     "#dcdee2",
    "popup_border_radius":    4,
    "list_border_color":      "#ebeef5",
    "list_border_radius":     4,
    "list_font_size":         14,
    "list_item_padding":      "0 12px",
    "list_item_hover_bg":     "#f5f7fa",
    "list_item_selected_bg":  "#ecf5ff",
    "list_item_selected_fg":  "#3370ff",
    "btn_hover_bg":           "#f5f7fa",
    "btn_border_color":       "#dcdfe6",
    "btn_border_radius":      4,
    "btn_padding":            "7px 15px",
    "btn_primary_bg":         "#3370ff",
    "btn_primary_hover_bg":   "#2861d5",
    "btn_primary_color":      "#ffffff",
    "btn_primary_border":     "#3370ff",
    "btn_hint_color":         "#909399",
    "search_border_color":    "#dcdee2",
    "search_border_focus":    "#3370ff",
    "search_border_radius":   4,
}

# GitHub Primer -- neutral grey chrome, blue focus ring, green primary
# button matching the GitHub "merge" / "commit" CTA.
GITHUB_THEME: dict[str, object] = {
    **DEFAULT_THEME,
    "text_color":             "#24292f",
    "border_color":           "#d0d7de",
    "border_color_focus":     "#0969da",
    "border_radius":          6,
    "underline_color":        "#d0d7de",
    "underline_color_focus":  "#0969da",
    "arrow_color":            "#656d76",
    "arrow_color_hover":      "#0969da",
    "selection_bg":           "#b6e3ff",
    "font_size":              13,
    "padding":                "4px 8px 4px 10px",
    "popup_border_color":     "#d0d7de",
    "popup_border_radius":    6,
    "list_border_color":      "#d8dee4",
    "list_border_radius":     6,
    "list_item_padding":      "4px 8px",
    "list_item_hover_bg":     "#f3f4f6",
    "list_item_selected_bg":  "#ddf4ff",
    "list_item_selected_fg":  "#0969da",
    "btn_background":         "#f6f8fa",
    "btn_hover_bg":           "#f3f4f6",
    "btn_border_color":       "#d0d7de",
    "btn_padding":            "3px 12px",
    "btn_primary_bg":         "#2da44e",
    "btn_primary_hover_bg":   "#2c974b",
    "btn_primary_color":      "#ffffff",
    "btn_primary_border":     "#2c974b",
    "btn_hint_color":         "#656d76",
    "search_border_color":    "#d0d7de",
    "search_border_focus":    "#0969da",
    "search_border_radius":   6,
}

# Aggregator: ``"name" -> theme dict``.  Use as
# ``combo.set_theme(THEMES["github"])``.
THEMES: dict[str, dict] = {
    "default": DEFAULT_THEME,
    "google":  GOOGLE_THEME,
    "tencent": TENCENT_THEME,
    "github":  GITHUB_THEME,
}


class _MultiSelectPopup(QFrame):
    """Drop-down list shown by :class:`MyCombo`.

    The popup is a top-level :class:`QFrame` flagged as ``Qt.Tool`` and built
    with ``WA_ShowWithoutActivating`` + ``Qt.NoFocus`` on every child widget.
    That way the parent ``QLineEdit`` keeps the keyboard focus and IME
    composition while the user clicks check-boxes in the drop-down -- editing
    and the drop-down never fight for focus.
    """

    selectionChanged = Signal(list)   # current list of selected values
    requestClose = Signal()
    filterOnlyThis = Signal(object)  # emit single value: "filter to only this item"

    def __init__(self, parent: QWidget | None = None,
                 theme: dict | None = None,
                 search_in_popup: bool = True,
                 string_only: bool = False) -> None:
        super().__init__(None, Qt.Tool | Qt.FramelessWindowHint
                         | Qt.NoDropShadowWindowHint)
        self._owner = parent
        self._theme: dict = dict(theme) if theme else dict(DEFAULT_THEME)
        self.setObjectName("MultiSelectPopup")
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setFocusPolicy(Qt.NoFocus)
        self.setFrameShape(QFrame.NoFrame)
        self.setMouseTracking(True)
        self._search_in_popup = search_in_popup
        self._string_only = string_only
        self._snapshot: list[Qt.CheckState] | None = None
        self._ok_clicked: bool = False

        self._apply_style()
        self._build_widgets()

    def _apply_style(self) -> None:
        t = self._theme
        self.setStyleSheet(f"""
            QFrame#MultiSelectPopup {{
                background: {t['popup_background']};
                border: {t['popup_border_width']}px solid {t['popup_border_color']};
                border-radius: {t['popup_border_radius']}px;
            }}
            QListWidget {{
                border: 1px solid {t['list_border_color']};
                border-radius: {t['list_border_radius']}px;
                background: {t['list_background']};
                outline: 0;
                font-size: {t['list_font_size']}px;
            }}
            QListWidget::item {{ padding: {t['list_item_padding']}; }}
            QListWidget::item:hover {{ background: {t['list_item_hover_bg']}; }}
            QListWidget::item:selected {{
                background: {t['list_item_selected_bg']};
                color: {t['list_item_selected_fg']};
            }}
            QPushButton {{
                border: 1px solid {t['btn_border_color']};
                border-radius: {t['btn_border_radius']}px;
                padding: {t['btn_padding']};
                background: {t['btn_background']};
                font-size: {t['btn_font_size']}px;
            }}
            QPushButton:hover {{ background: {t['btn_hover_bg']}; }}
            QPushButton#primary {{
                background: {t['btn_primary_bg']};
                color: {t['btn_primary_color']};
                border-color: {t['btn_primary_border']};
            }}
            QPushButton#primary:hover {{ background: {t['btn_primary_hover_bg']}; }}
            QPushButton#hint {{
                border: none;
                background: transparent;
                color: {t['btn_hint_color']};
            }}
            QLineEdit#PopupSearch {{
                background: {t['search_background']};
                border: 1px solid {t['search_border_color']};
                border-radius: {t['search_border_radius']}px;
                padding: {t['search_padding']};
                min-height: {t['search_height']}px;
            }}
            QLineEdit#PopupSearch:focus {{
                border-color: {t['search_border_focus']};
            }}
            QToolButton#HoverOnly {{
                background: {t['btn_primary_bg']};
                color: {t['btn_primary_color']};
                border: 1px solid {t['btn_primary_border']};
                border-radius: 10px;
                padding: 1px 8px;
                font-size: 11px;
            }}
            QToolButton#HoverOnly:hover {{
                background: {t['btn_primary_hover_bg']};
            }}
        """)

    def _build_widgets(self) -> None:
        """Build the popup's child widget tree. Called once from __init__.

        Kept separate from :py:meth:`_apply_style` so that re-applying the
        stylesheet at runtime (via :py:meth:`MyCombo.set_theme`) does NOT
        recreate the QVBoxLayout -- which would otherwise trigger
        Qt's "QLayout: Attempting to add QLayout to widget that already
        has a layout" warning.
        """
        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(6)

        # -- sort row (升序 / 降序) ---------------------------------------
        sort_row = QHBoxLayout()
        sort_row.setSpacing(4)
        self._sort_asc_btn = QPushButton("\u2191 升序", self)
        self._sort_desc_btn = QPushButton("\u2193 降序", self)
        sort_row.addWidget(self._sort_asc_btn)
        sort_row.addWidget(self._sort_desc_btn)
        sort_row.addStretch(1)
        outer.addLayout(sort_row)

        # -- 全选 checkbox (tristate, above the list) ----------------------
        # Mirrors the MyTable filter-popup layout where the "全选" widget
        # is a QCheckBox (not a button) placed between the sort row and
        # the search box.  Its tristate visual (Unchecked / Partially
        # Checked / Checked) gives the user immediate feedback on the
        # current selection state.
        self._select_all_cb = QCheckBox("全选", self)
        self._select_all_cb.setTristate(True)
        outer.addWidget(self._select_all_cb)

        # -- bottom button row (反选 / 重置     已选 N 项     取消 / 确定) --
        self._btn_row_widget = QWidget(self)
        btn_row = QHBoxLayout(self._btn_row_widget)
        btn_row.setContentsMargins(0, 0, 0, 0)
        btn_row.setSpacing(4)
        self._invert_btn = QPushButton("反选", self._btn_row_widget)
        self._clear_btn = QPushButton("重置", self._btn_row_widget)
        btn_row.addWidget(self._invert_btn)
        btn_row.addWidget(self._clear_btn)
        btn_row.addStretch(1)
        self._count_label = QPushButton("已选 0 项", self._btn_row_widget)
        self._count_label.setObjectName("hint")
        self._count_label.setEnabled(False)
        btn_row.addWidget(self._count_label)
        btn_row.addSpacing(8)
        self._cancel_btn = QPushButton("取消", self._btn_row_widget)
        self._ok_btn = QPushButton("确定", self._btn_row_widget)
        self._ok_btn.setObjectName("primary")
        btn_row.addWidget(self._cancel_btn)
        btn_row.addWidget(self._ok_btn)

        # -- search box (optional) ----------------------------------------
        self._search_edit = QLineEdit(self)
        self._search_edit.setObjectName("PopupSearch")
        self._search_edit.setPlaceholderText("搜索...")
        self._search_edit.setClearButtonEnabled(True)
        # Accept click-focus only: typing into the main line edit is still
        # the primary way to filter, but the user can also click here when
        # there are many items.  Other popup children stay NoFocus below.
        self._search_edit.setFocusPolicy(Qt.ClickFocus)
        self._search_edit.textEdited.connect(self._on_search_text_edited)
        if not self._search_in_popup:
            self._search_edit.hide()

        self._list = _CheckListWidget(self)
        self._list.setSelectionMode(QAbstractItemView.NoSelection)
        self._list.setMinimumHeight(180)
        self._list.setMaximumHeight(320)
        self._list.setUniformItemSizes(True)
        self._list.setMouseTracking(True)

        # Unified layout: sort row already added above, then 全选 checkbox above.
        outer.addWidget(self._search_edit)
        outer.addWidget(self._list)
        outer.addWidget(self._btn_row_widget)

        # Make every other child non-focusable so the popup never steals
        # focus from the parent QLineEdit.  The search edit is the only
        # exception -- it accepts click-focus on demand.
        for w in self.findChildren(QWidget):
            if w is self._search_edit:
                continue
            w.setFocusPolicy(Qt.NoFocus)

        # -- hover-only "仅筛此项" overlay --------------------------------
        # A floating QToolButton that re-positions to whichever item the
        # cursor is over, and disappears when the cursor leaves the list.
        # Click → emit ``filterOnlyThis`` with that single value; the
        # owner replaces the selection with that one item and closes.
        # Parent to the list viewport so the button is part of the scrolling
        # surface — mouse movement between a list item and the overlay does
        # NOT trigger viewport Leave (which would otherwise hide the button
        # the instant the user tries to click it, causing flicker).
        self._hover_only_btn = QToolButton(self._list.viewport())
        self._hover_only_btn.setText("仅筛此项")
        self._hover_only_btn.setObjectName("HoverOnly")
        self._hover_only_btn.setCursor(Qt.PointingHandCursor)
        self._hover_only_btn.setToolTip("把筛选替换为只看这一项")
        self._hover_only_btn.hide()
        self._hover_only_btn.setFocusPolicy(Qt.NoFocus)
        self._hover_only_btn.clicked.connect(self._on_hover_only_clicked)
        self._hover_only_target: object | None = None

        self._select_all_cb.clicked.connect(self._on_select_all_cb_clicked)
        self._invert_btn.clicked.connect(self._invert_visible)
        self._clear_btn.clicked.connect(self._clear_visible)
        self._ok_btn.clicked.connect(self._on_ok)
        self._cancel_btn.clicked.connect(self._on_cancel)
        self._sort_asc_btn.clicked.connect(lambda: self._sort_visible(Qt.AscendingOrder))
        self._sort_desc_btn.clicked.connect(lambda: self._sort_visible(Qt.DescendingOrder))
        self._list.itemChanged.connect(self._on_item_changed)
        self._list.setMouseTracking(True)
        self._list.itemEntered.connect(self._on_list_item_entered)
        self._list.viewport().installEventFilter(self)

    # ---- public API for the owner ---------------------------------------
    def set_items(self, items: Iterable[tuple[str, object, bool]]) -> None:
        self._list.blockSignals(True)
        self._list.clear()
        for label, value, checked in items:
            it = QListWidgetItem(label)
            it.setFlags(it.flags() | Qt.ItemIsUserCheckable)
            it.setCheckState(Qt.Checked if checked else Qt.Unchecked)
            it.setData(Qt.UserRole, value)
            self._list.addItem(it)
        self._list.blockSignals(False)
        self._update_count()
        self._sync_select_all_cb()
        self._snapshot = [self._list.item(i).checkState()
                          for i in range(self._list.count())]
        self._ok_clicked = False

    def selected_values(self) -> list:
        return [self._list.item(i).data(Qt.UserRole)
                for i in range(self._list.count())
                if self._list.item(i).checkState() == Qt.Checked]

    def selected_labels(self) -> list[str]:
        return [self._list.item(i).text()
                for i in range(self._list.count())
                if self._list.item(i).checkState() == Qt.Checked]

    def hideEvent(self, event) -> None:
        # If the popup is closing without "确定" (e.g. outside-click, Esc,
        # hover-leave timer), restore the snapshot so buffered changes are
        # discarded automatically — just like "取消".
        if not self._ok_clicked:
            self._restore_snapshot()
        self._ok_clicked = False
        # Reset the hover overlay.
        self._hover_only_btn.hide()
        self._hover_only_target = None
        super().hideEvent(event)

    def apply_filter(self, text: str) -> int:
        """Show only items containing ``text`` (case-insensitive). Returns visible count."""
        q = text.strip().lower()
        visible = 0
        for i in range(self._list.count()):
            item = self._list.item(i)
            hide = bool(q) and q not in item.text().lower()
            item.setHidden(hide)
            if not hide:
                visible += 1
        # The previously hovered item may have just been hidden, so the
        # "仅筛此项" overlay would be pointing at nothing.
        if self._hover_only_target is not None and self._hover_only_target.isHidden():
            self._hover_only_btn.hide()
            self._hover_only_target = None
        self._sync_select_all_cb()
        return visible

    def _on_search_text_edited(self, text: str) -> None:
        """Mirror the popup search box text to the owner's main line edit
        and re-apply the filter.  Both textEdited sources converge on
        :py:meth:`apply_filter`; blockSignals prevents the round-trip from
        re-entering this method.
        """
        owner = self._owner
        if owner is not None:
            edit = owner.line_edit()
            if edit.text() != text:
                edit.blockSignals(True)
                edit.setText(text)
                edit.blockSignals(False)
                owner._editing = True
        self.apply_filter(text)

    def has_visible_items(self) -> bool:
        return any(not self._list.item(i).isHidden()
                   for i in range(self._list.count()))

    def _on_select_all_cb_clicked(self) -> None:
        # Toggle: if every visible item is checked, un-check them; else
        # check them all. Mirrors the MyTable filter-popup "全选" behaviour
        # (click twice = "反选效果" / uncheck all). Buffered mode — does
        # NOT emit ``selectionChanged``; the user must click 确定 to apply.
        self._list.blockSignals(True)
        visible = [i for i in range(self._list.count())
                   if not self._list.item(i).isHidden()]
        all_checked = bool(visible) and all(
            self._list.item(i).checkState() == Qt.Checked for i in visible
        )
        new_state = Qt.Unchecked if all_checked else Qt.Checked
        for i in visible:
            self._list.item(i).setCheckState(new_state)
        self._list.blockSignals(False)
        if visible:
            self._update_count()

    def _sync_select_all_cb(self) -> None:
        """Sync the tristate "全选" checkbox with the visible items' state."""
        total = self._list.count()
        visible_idx = [i for i in range(total)
                       if not self._list.item(i).isHidden()]
        visible_count = len(visible_idx)
        if visible_count == 0:
            self._select_all_cb.setCheckState(Qt.Unchecked)
            return
        checked_count = sum(1 for i in visible_idx
                            if self._list.item(i).checkState() == Qt.Checked)
        self._select_all_cb.blockSignals(True)
        if checked_count == 0:
            self._select_all_cb.setCheckState(Qt.Unchecked)
        elif checked_count == visible_count:
            self._select_all_cb.setCheckState(Qt.Checked)
        else:
            self._select_all_cb.setCheckState(Qt.PartiallyChecked)
        self._select_all_cb.blockSignals(False)

    def _invert_visible(self) -> None:
        """Toggle every currently visible item's check state. Buffered — no signal."""
        self._list.blockSignals(True)
        for i in range(self._list.count()):
            item = self._list.item(i)
            if item.isHidden():
                continue
            new_state = (Qt.Unchecked if item.checkState() == Qt.Checked
                         else Qt.Checked)
            item.setCheckState(new_state)
        self._list.blockSignals(False)
        self._update_count()

    def _clear_visible(self) -> None:
        """Uncheck every currently visible item. Buffered — no signal, does not close."""
        self._list.blockSignals(True)
        for i in range(self._list.count()):
            item = self._list.item(i)
            if not item.isHidden() and item.checkState() == Qt.Checked:
                item.setCheckState(Qt.Unchecked)
        self._list.blockSignals(False)
        self._update_count()

    def _on_item_changed(self, _item: QListWidgetItem) -> None:
        # Buffered mode: update UI state only, no signal until 确定.
        self._update_count()

    # ---- buffered 确定 / 取消 -------------------------------------------
    def _on_ok(self) -> None:
        """Apply buffered selection changes and close the popup."""
        current = [self._list.item(i).checkState()
                   for i in range(self._list.count())]
        if current != self._snapshot:
            self.selectionChanged.emit(self.selected_values())
            self._snapshot = current
        self._ok_clicked = True
        self.requestClose.emit()

    def _on_cancel(self) -> None:
        """Discard buffered changes, restore snapshot, and close."""
        self._restore_snapshot()
        self.requestClose.emit()

    def _restore_snapshot(self) -> None:
        if self._snapshot is None:
            return
        self._list.blockSignals(True)
        for i, state in enumerate(self._snapshot):
            if i < self._list.count():
                self._list.item(i).setCheckState(state)
        self._list.blockSignals(False)
        self._update_count()

    # ---- in-popup sort (matches the MyTable filter popup) ---------------
    def _sort_visible(self, order: Qt.SortOrder) -> None:
        # Sort only the *visible* (search-filtered) items. Hidden items keep
        # their original position so toggling the search box on/off doesn't
        # jumble the underlying list. Sorting is by display text, case
        # insensitive; ties are stable.
        #
        # Implementation: detach all items into a Python list, split into
        # visible/hidden, sort the visible part, then re-insert in the new
        # order. ``takeItem`` is index-sensitive (subsequent rows shift
        # up), so we cannot sort in-place via take/insertItem.
        reverse = (order == Qt.DescendingOrder)
        items = [self._list.takeItem(0) for _ in range(self._list.count())]
        visible = [it for it in items if not it.isHidden()]
        hidden = [it for it in items if it.isHidden()]
        visible.sort(key=lambda it: it.text().lower(), reverse=reverse)
        self._list.blockSignals(True)
        for it in visible + hidden:
            self._list.addItem(it)
        self._list.blockSignals(False)

    # ---- hover "仅筛此项" overlay --------------------------------------
    def _on_list_item_entered(self, item: QListWidgetItem) -> None:
        if item is None or item.isHidden():
            self._hover_only_btn.hide()
            self._hover_only_target = None
            return
        # Position the floating button over the right edge of the item row.
        # ``visualItemRect`` already returns viewport-local coordinates and
        # the button is parented to ``self._list.viewport()``, so we can
        # use these directly — no need for ``self._list.x()`` offsets.
        rect = self._list.visualItemRect(item)
        if rect.isNull():
            self._hover_only_btn.hide()
            self._hover_only_target = None
            return
        btn = self._hover_only_btn
        btn.adjustSize()
        bw, bh = btn.sizeHint().width(), btn.sizeHint().height()
        # Anchor to the right edge of the item row, vertically centered
        x = rect.right() - bw - 4
        y = rect.top() + (rect.height() - bh) // 2
        btn.move(max(2, x), max(2, y))
        btn.show()
        btn.raise_()
        self._hover_only_target = item

    def _on_hover_only_clicked(self) -> None:
        item = self._hover_only_target
        self._hover_only_btn.hide()
        self._hover_only_target = None
        if item is None:
            return
        value = item.data(Qt.UserRole)
        # Apply immediately: replace selection with only this value, update
        # snapshot, and close (bypasses the 确定/取消 buffer).
        self._list.blockSignals(True)
        for i in range(self._list.count()):
            it = self._list.item(i)
            it.setCheckState(Qt.Checked if it.data(Qt.UserRole) == value
                             else Qt.Unchecked)
        self._list.blockSignals(False)
        self._update_count()
        self._snapshot = [self._list.item(i).checkState()
                          for i in range(self._list.count())]
        self._ok_clicked = True
        self.filterOnlyThis.emit(value)
        # The owner processes the signal (replaces selection + closes popup).
        # We do NOT call requestClose here — the owner's filterOnlyThis
        # handler already calls hide_popup(), which triggers hideEvent.

    def eventFilter(self, watched, event):
        # Hide the floating "仅筛此项" button when the mouse leaves the
        # list viewport or the button itself is hidden by something else.
        if watched is self._list.viewport() and event.type() == QEvent.Leave:
            self._hover_only_btn.hide()
            self._hover_only_target = None
        return super().eventFilter(watched, event)

    def _update_count(self) -> None:
        count = sum(
            1 for i in range(self._list.count())
            if self._list.item(i).checkState() == Qt.Checked
        )
        self._count_label.setText(f"已选 {count} 项")
        self._sync_select_all_cb()


class MyCombo(QWidget):
    """Editable multi-select combo box with a checkable drop-down list.
    The main widget is a real ``QLineEdit`` -- the user may type, select,
    copy and paste exactly like in any input field. Typing automatically
    opens the drop-down and filters the list by what was typed. The drop-down
    never steals focus from the line edit, so editing and selecting cannot
    conflict.

    Behaviour
    ---------
    * **Click / focus / arrow-key down** on the line edit -- opens the popup.
    * **Typing** -- filters the popup. The typed text is the search query
      while the popup is open.
    * **Clicking an item in the popup** -- toggles its check state. Focus
      stays on the line edit (popup never activates).
    * **All / Clear buttons** -- apply to *visible* items only, so combined
      with typing you can "select all matching".
    * **Closing the popup** (Esc, click outside, arrow button) -- the line
      edit goes back to showing the comma-joined labels of the current
      selection.
    """

    selectionChanged = Signal(list)
    popupShown = Signal()
    popupHidden = Signal()

    def __init__(self, parent: QWidget | None = None,
                 placeholder: str = "请选择...",
                 theme: dict | None = None,
                 search_in_popup: bool = True,
                 string_only: bool = False) -> None:
        super().__init__(parent)
        self._placeholder = placeholder
        self._items: list[tuple[str, object]] = []
        self._selected_values: list = []
        self._popup_open = False
        self._editing = False    # True while user is typing a search query
        self._theme: dict = dict(DEFAULT_THEME)
        self._search_in_popup = search_in_popup
        self._string_only = string_only
        if theme:
            self._theme.update(theme)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(34)

        # ---- main line-edit + arrow button --------------------------------
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._edit = QLineEdit(self)
        self._edit.setPlaceholderText(placeholder)
        self._edit.setClearButtonEnabled(False)
        self._edit.installEventFilter(self)
        self._edit.textEdited.connect(self._on_text_edited)

        self._arrow = QToolButton(self)
        self._arrow.setText("\u25be")           # 下三角
        self._arrow.setCursor(Qt.PointingHandCursor)
        self._arrow.setFocusPolicy(Qt.NoFocus)
        self._arrow.setAutoRaise(True)
        self._arrow.setFixedWidth(26)
        self._arrow.clicked.connect(self._toggle_popup)

        layout.addWidget(self._edit, 1)
        layout.addWidget(self._arrow)
        self.setFocusProxy(self._edit)

        self.setStyleSheet(
            f"""
            MyCombo {{
                background: {self._theme['background']};
                border: {self._theme['border_width']}px solid {self._theme['border_color']};
                border-radius: {self._theme['border_radius']}px;
            }}
            MyCombo:focus-within {{
                border-color: {self._theme['border_color_focus']};
            }}
            /* The line edit shows a bottom border to make the caret /
               focus location obvious. The colour goes from neutral grey to
               brand blue when the edit has keyboard focus. Border is kept
               at the same width in both states so the text never shifts. */
            QLineEdit {{
                color: {self._theme['text_color']};
                border: none;
                border-bottom: {self._theme['underline_width']}px solid {self._theme['underline_color']};
                background: transparent;
                padding: {self._theme['padding']};
                selection-background-color: {self._theme['selection_bg']};
                font-size: {self._theme['font_size']}px;
            }}
            QLineEdit:focus {{
                border-bottom: {self._theme['underline_width']}px solid {self._theme['underline_color_focus']};
            }}
            QToolButton {{
                border: none;
                background: transparent;
                color: {self._theme['arrow_color']};
                font-size: 12px;
                padding: 0 4px 2px 0;
            }}
            QToolButton:hover {{ color: {self._theme['arrow_color_hover']}; }}
            """
        )

        # ---- popup --------------------------------------------------------
        self._popup = _MultiSelectPopup(self,
                                        theme=self._theme,
                                        search_in_popup=search_in_popup,
                                        string_only=string_only)
        self._popup.selectionChanged.connect(self._on_popup_selection_changed)
        self._popup.requestClose.connect(self.hide_popup)
        self._popup.filterOnlyThis.connect(self._on_filter_only_this)

        # Global click-outside watcher -- attached only while popup is open.
        self._outside_filter = _OutsideClickFilter(self, self._on_outside_click)

    # ---- public API ------------------------------------------------------
    def line_edit(self) -> QLineEdit:
        """Expose the underlying QLineEdit (e.g. for validators)."""
        return self._edit

    def theme(self) -> dict:
        """Return a copy of the current theme dict."""
        return dict(self._theme)

    def is_search_in_popup(self) -> bool:
        """Return whether the popup shows its own search box."""
        return self._search_in_popup

    def set_search_in_popup(self, enabled: bool) -> None:
        """Toggle the optional search box *inside* the drop-down panel.

        The popup keeps one search ``QLineEdit`` always built; visibility
        is what changes.  When ``enabled`` is True (the default) the search
        box sits between the button row and the list, with its text kept
        in sync with the main line edit so the user can filter from
        either place.  When ``enabled`` is False the popup becomes a pure
        check-list, and the main line edit is the only place where the
        filter can be typed.

        Takes effect on the *next* ``show_popup``; if the popup is
        currently open it will close and reopen.
        """
        self._search_in_popup = bool(enabled)
        self._popup._search_edit.setVisible(self._search_in_popup)
        if self._popup_open:
            self.hide_popup()

    def is_string_only(self) -> bool:
        """Return whether the line edit is unlocked (free-form input).

        In string-only mode the popup's multi-select behaviour is unchanged:
        ``selected_values()`` still returns the list of checked items and
        ``selectionChanged`` still fires only on check-state changes.
        The *only* difference is that the line edit stays editable --
        the comma-joined "labels" view is suppressed -- so the caller can
        read the user-typed string via :py:meth:`value`.
        """
        return self._string_only

    def set_string_only(self, enabled: bool) -> None:
        """Unlock / lock the line edit (free-form input toggle).

        Enabling string-only does **not** change any of the multi-select
        semantics: ``selected_values()``, ``set_selected_values()``,
        ``clear_selection()``, ``select_all()``, the (全选/ 反选/ 取消) buttons, and ``selectionChanged`` all behave exactly as in
        the default mode.  The line edit simply stops being overwritten
        with the comma-joined labels of the current selection, so the
        user can type any free-form string and :py:meth:`value` returns
        it as a single string.

        Toggling this on a non-empty line edit is a no-op: the existing
        text is preserved either way.  Toggling *off* (back to
        multi-select) will overwrite the line edit with the joined
        labels of the current selection immediately.
        """
        self._string_only = bool(enabled)
        self._popup._string_only = self._string_only
        if not self._string_only:
            # Re-render the current selection into the line edit now that
            # we are back in the labels-display mode.  Clear the editing
            # flag first -- otherwise _render_selection_to_edit's guard
            # would skip the overwrite.
            self._editing = False
            self._render_selection_to_edit()

    def set_theme(self, theme: dict) -> None:
        """Merge ``theme`` into the current theme dict and re-apply styles.

        Pass any subset of the keys in :data:`DEFAULT_THEME`; values not
        present in ``theme`` keep their previous setting. Useful both at
        construction time and for runtime theme switching.
        """
        self._theme.update(theme)
        # Re-emit the stylesheet. We rebuild from the current theme by
        # injecting the relevant values back into the f-string the
        # constructor used; the constructor already ran, so re-run it via
        # a small helper:
        bg = self._theme['background']
        bw = self._theme['border_width']
        bc = self._theme['border_color']
        br = self._theme['border_radius']
        bcf = self._theme['border_color_focus']
        tc = self._theme['text_color']
        uc = self._theme['underline_color']
        uw = self._theme['underline_width']
        ucf = self._theme['underline_color_focus']
        pad = self._theme['padding']
        sbg = self._theme['selection_bg']
        fs = self._theme['font_size']
        ac = self._theme['arrow_color']
        ach = self._theme['arrow_color_hover']
        self.setStyleSheet(f"""
            MyCombo {{
                background: {bg};
                border: {bw}px solid {bc};
                border-radius: {br}px;
            }}
            MyCombo:focus-within {{
                border-color: {bcf};
            }}
            QLineEdit {{
                color: {tc};
                border: none;
                border-bottom: {uw}px solid {uc};
                background: transparent;
                padding: {pad};
                selection-background-color: {sbg};
                font-size: {fs}px;
            }}
            QLineEdit:focus {{
                border-bottom: {uw}px solid {ucf};
            }}
            QToolButton {{
                border: none;
                background: transparent;
                color: {ac};
                font-size: 12px;
                padding: 0 4px 2px 0;
            }}
            QToolButton:hover {{ color: {ach}; }}
        """)
        # Re-apply popup styles so its buttons / list / frame match.
        self._popup._theme = dict(self._theme)
        self._popup._apply_style()

    def set_items(self, items: Iterable) -> None:
        normalized: list[tuple[str, object]] = []
        for it in items:
            if isinstance(it, tuple) and len(it) == 2:
                normalized.append((str(it[0]), it[1]))
            else:
                normalized.append((str(it), it))
        self._items = normalized
        # drop selected values that no longer exist
        valid_keys = {self._key(v) for _, v in normalized}
        self._selected_values = [v for v in self._selected_values
                                 if self._key(v) in valid_keys]
        self._refresh_popup_items()
        self._render_selection_to_edit()

    def set_dict_items(self, d: dict, *, swap: bool = False) -> None:
        """Populate the combo from a ``{key: value}`` mapping.

        By default the dict's *value* becomes the user-visible label and the
        *key* becomes the programmatic value passed through
        :py:meth:`selectionChanged` / :py:meth:`selected_values` -- so
        callers who have a code-to-display table can write::

            cb.set_dict_items({"name": "中国", "towname": "华夏"})

        and the dropdown shows "中国" / "华夏" while callbacks receive
        ``"name"`` / ``"towname"``.

        Pass ``swap=True`` to flip the mapping: the key becomes the label
        and the value becomes the programmatic value.  Duplicate values
        are fine: items are tracked by their value (the key in the
        default direction), so two entries with the same display text
        can be checked independently.
        """
        if swap:
            items = [(str(k), v) for k, v in d.items()]
        else:
            items = [(str(v), k) for k, v in d.items()]
        self.set_items(items)

    def items(self) -> list[tuple[str, object]]:
        return list(self._items)

    def selected_values(self) -> list:
        """Return the list of currently selected item values.

        In ``string_only`` mode this *still* reflects the popup's multi-select
        state -- the input box is just unlocked.  Call :py:meth:`value`
        if you want the free-form string the user has typed.
        """
        return list(self._selected_values)

    def selected_labels(self) -> list[str]:
        sel_keys = {self._key(v) for v in self._selected_values}
        return [label for label, value in self._items
                if self._key(value) in sel_keys]

    def value(self) -> str:
        """Return the current line-edit text.

        This is the primary way to read the user-editable string in
        :py:attr:`string_only` mode -- the popup's multi-select state is
        independent of the line edit in that mode.  Equivalent to
        :py:meth:`input_text`; kept short for ergonomic call sites:

            cb.selectionChanged.connect(lambda _: print("text:", cb.value()))
        """
        return self._edit.text()

    def input_text(self) -> str:
        """Alias for :py:meth:`value`."""
        return self._edit.text()

    def set_selected_values(self, values: Iterable) -> None:
        valid = {self._key(v) for v in values}
        new_selected = [value for _, value in self._items
                        if self._key(value) in valid]
        if new_selected != self._selected_values:
            self._selected_values = new_selected
            self._refresh_popup_items()
            self._render_selection_to_edit()
            self.selectionChanged.emit(list(self._selected_values))

    def clear_selection(self) -> None:
        if self._selected_values:
            self._selected_values = []
            self._refresh_popup_items()
            self._render_selection_to_edit()
            self.selectionChanged.emit([])

    def select_all(self) -> None:
        all_values = [v for _, v in self._items]
        if self._selected_values != all_values:
            self._selected_values = all_values
            self._refresh_popup_items()
            self._render_selection_to_edit()
            self.selectionChanged.emit(list(self._selected_values))

    # ---- helpers ---------------------------------------------------------
    @staticmethod
    def _key(value):
        if isinstance(value, (str, int, float, bool, type(None))):
            return value
        return id(value)

    def _refresh_popup_items(self) -> None:
        sel = {self._key(v) for v in self._selected_values}
        self._popup.set_items(
            (label, value, self._key(value) in sel) for label, value in self._items
        )

    def _render_selection_to_edit(self) -> None:
        """Display the current selection inside the line edit (read-only state).

        Guarded only by ``self._editing``: if the user has typed into the
        line edit (i.e. the input is the user's free-form text right now)
        we leave it alone.  Otherwise the comma-joined labels of the
        current selection are written into the line edit.  This works
        identically in ``string_only`` mode -- in that mode the
        :py:meth:`hide_popup` method simply skips calling this on close,
        so a user's edits are preserved, but item clicks still update
        the line edit *until* the user types.
        """
        if self._editing:
            return
        labels = self.selected_labels()
        text = ", ".join(labels)
        self._edit.blockSignals(True)
        self._edit.setText(text)
        self._edit.setCursorPosition(0)
        self._edit.blockSignals(False)

    def _on_popup_selection_changed(self, values: list) -> None:
        if values != self._selected_values:
            self._selected_values = list(values)
            self.selectionChanged.emit(list(self._selected_values))
            # While the popup is open and the user is *not* editing, refresh
            # the line edit so they see the selection live.
            if not self._editing:
                self._render_selection_to_edit()

    def _on_filter_only_this(self, value: object) -> None:
        """User clicked the hover-only "仅筛此项" badge on an item.
        Replace the current selection with just that single value, refresh
        the line edit, and close the popup.
        """
        if value in self._selected_values and len(self._selected_values) == 1:
            # Already the only selection — close is enough.
            self.hide_popup()
            return
        self._selected_values = [value]
        self.selectionChanged.emit(list(self._selected_values))
        self._editing = False  # selection now drives the line edit
        self._render_selection_to_edit()
        self.hide_popup()

    def _on_text_edited(self, text: str) -> None:
        # The user actually typed something -> enter editing mode and filter.
        self._editing = True
        if not self._popup_open:
            self.show_popup()
        # Mirror the text to the popup's search box (if visible) without
        # round-tripping through its textEdited signal.
        if self._search_in_popup and self._popup._search_edit.text() != text:
            self._popup._search_edit.blockSignals(True)
            self._popup._search_edit.setText(text)
            self._popup._search_edit.blockSignals(False)
        self._popup.apply_filter(text)

    # ---- popup open / close ---------------------------------------------
    def show_popup(self) -> None:
        if self._popup_open:
            return
        self._popup_open = True
        # Re-apply the search_in_popup switch each time the popup opens --
        # this lets :py:meth:`set_search_in_popup` take effect immediately
        # even after the popup widget has already been built.
        self._popup._search_edit.setVisible(self._search_in_popup)
        self._refresh_popup_items()
        if self._editing:
            text = self._edit.text()
            if self._search_in_popup and self._popup._search_edit.text() != text:
                self._popup._search_edit.blockSignals(True)
                self._popup._search_edit.setText(text)
                self._popup._search_edit.blockSignals(False)
            self._popup.apply_filter(text)
        else:
            self._popup.apply_filter("")

        bottom_left = self.mapToGlobal(QPoint(0, self.height()))
        width = max(self.width(), 260)
        screen = QApplication.screenAt(bottom_left)
        rect = screen.availableGeometry() if screen else QRect(0, 0, 1920, 1080)
        self._popup.adjustSize()
        height = max(self._popup.sizeHint().height(), 240)
        x = bottom_left.x()
        y = bottom_left.y() + 2
        if x + width > rect.right():
            x = max(rect.left(), rect.right() - width)
        if y + height > rect.bottom():
            y = self.mapToGlobal(QPoint(0, 0)).y() - height - 2
        self._popup.setGeometry(x, y, width, height)
        self._popup.show()

        QApplication.instance().installEventFilter(self._outside_filter)
        self.popupShown.emit()
        self.update()

    def hide_popup(self) -> None:
        if not self._popup_open:
            return
        self._popup_open = False
        self._popup.hide()
        try:
            QApplication.instance().removeEventFilter(self._outside_filter)
        except Exception:
            pass
        # Clear the popup's search box so the next open starts fresh.
        if self._search_in_popup:
            self._popup._search_edit.clear()
        # Leave editing mode.  In string_only mode we deliberately skip the
        # labels-render so a user's free-form text survives a popup
        # round-trip; in normal mode we restore the joined labels view.
        self._editing = False
        if not self._string_only:
            self._render_selection_to_edit()
        self.popupHidden.emit()
        self.update()

    def _toggle_popup(self) -> None:
        if self._popup_open:
            self.hide_popup()
        else:
            self._edit.setFocus()
            self.show_popup()

    def _on_outside_click(self, obj: QObject) -> None:
        """Close the popup if ``obj`` (the event target) is outside the popup
        *and* outside the combo's own widget tree.

        We deliberately do **not** use ``QPoint.contains(geometry)``: when the
        popup is a tool window the global geometry can be reported in ways
        that misclassify clicks that happen exactly on a child widget border.
        Walking the parent chain is robust regardless of window flags.
        """
        if not isinstance(obj, QWidget):
            return
        w = obj
        while w is not None:
            if w is self._popup or w is self:
                return
            w = w.parentWidget()
        self.hide_popup()

    def _geometry_contains_global(self, gp: QPoint) -> bool:
        top_left = self.mapToGlobal(QPoint(0, 0))
        return QRect(top_left, self.size()).contains(gp)

    # ---- event filter on the QLineEdit ----------------------------------
    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if obj is self._edit:
            t = event.type()
            if t == QEvent.MouseButtonPress:
                if not self._popup_open:
                    QTimer.singleShot(0, self.show_popup)
            elif t == QEvent.FocusOut:
                # Intentionally do NOT close the popup on focus-out.
                #
                # When the user clicks anywhere inside the popup, every child
                # widget there has Qt.NoFocus, which means QApplication's
                # focusWidget() becomes None and the line edit fires a
                # FocusOut event. Treating that as "user left the combo box"
                # would close the popup after every checkbox click -- the
                # exact bug we are fixing.
                #
                # Popup-close is handled exclusively by the outside-click
                # filter (which walks the widget tree) and by Esc / arrow
                # button / clicking the wrapper again.
                pass
            elif t == QEvent.KeyPress and isinstance(event, QKeyEvent):
                if event.key() == Qt.Key_Escape:
                    if self._popup_open:
                        self.hide_popup()
                        return True
                elif event.key() in (Qt.Key_Down, Qt.Key_Up):
                    if not self._popup_open:
                        self.show_popup()
                        return True
                elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
                    if self._popup_open:
                        self._enter_toggle_first_visible()
                        return True
        return super().eventFilter(obj, event)

    def _is_descendant_of_popup(self, w: QWidget) -> bool:
        p = w
        while p is not None:
            if p is self._popup:
                return True
            p = p.parentWidget()
        return False

    def _enter_toggle_first_visible(self) -> None:
        list_w = self._popup._list
        for i in range(list_w.count()):
            item = list_w.item(i)
            if not item.isHidden():
                new_state = (Qt.Unchecked if item.checkState() == Qt.Checked
                             else Qt.Checked)
                item.setCheckState(new_state)
                return

    # ---- key/mouse on the outer widget (delegates to the edit) ----------
    def mousePressEvent(self, event: QMouseEvent) -> None:
        # Clicking the wrapper (e.g. its border) should focus the line edit.
        if event.button() == Qt.LeftButton:
            self._edit.setFocus()
            if not self._popup_open:
                self.show_popup()
            event.accept()
            return
        super().mousePressEvent(event)

    def sizeHint(self) -> QSize:
        fm = QFontMetrics(self.font())
        return QSize(max(200, fm.horizontalAdvance(self._placeholder) + 60), 34)


class _OutsideClickFilter(QObject):
    """Application-wide event filter that closes the popup on outside clicks.

    Decides "inside vs outside" by inspecting the event's *target widget*
    (its parent chain), not by hit-testing global coordinates. This avoids
    fragile geometry math under various window flags (Qt.Tool, frameless,
    high-DPI scaling, multi-monitor setups, etc.) and -- more importantly --
    correctly recognises clicks landing on items whose own ``mousePressEvent``
    has already swallowed coordinates.
    """

    def __init__(self, owner: "MyCombo", callback) -> None:
        super().__init__(owner)
        self._callback = callback

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.MouseButtonPress:
            self._callback(obj)
        return False
