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

    def __init__(self, parent: QWidget | None = None,
                 buttons_at_top: bool = True,
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
        self._buttons_at_top = buttons_at_top
        self._search_in_popup = search_in_popup
        self._string_only = string_only

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

        self._btn_row_widget = QWidget(self)
        btn_row = QHBoxLayout(self._btn_row_widget)
        btn_row.setContentsMargins(0, 0, 0, 0)
        btn_row.setSpacing(4)
        self._select_all_btn = QPushButton("全选", self._btn_row_widget)
        self._select_all_btn.setObjectName("primary")
        self._invert_btn = QPushButton("反选", self._btn_row_widget)
        self._clear_btn = QPushButton("重置", self._btn_row_widget)
        btn_row.addWidget(self._select_all_btn)
        btn_row.addWidget(self._invert_btn)
        btn_row.addWidget(self._clear_btn)
        btn_row.addStretch(1)
        self._count_label = QPushButton("已选 0 项", self._btn_row_widget)
        self._count_label.setObjectName("hint")
        self._count_label.setEnabled(False)
        btn_row.addWidget(self._count_label)
        # NOTE: ``string_only`` no longer hides the button row -- the popup's
        # multi-select behaviour is unchanged in that mode.  The only
        # thing string_only affects is whether the main line edit stays
        # user-editable.

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

        if self._buttons_at_top:
            outer.addWidget(self._btn_row_widget)
            outer.addWidget(self._search_edit)        # search is always in
            outer.addWidget(self._list)               # the middle slot
        else:
            outer.addWidget(self._list)
            outer.addWidget(self._search_edit)
            outer.addWidget(self._btn_row_widget)

        # Make every other child non-focusable so the popup never steals
        # focus from the parent QLineEdit.  The search edit is the only
        # exception -- it accepts click-focus on demand.
        for w in self.findChildren(QWidget):
            if w is self._search_edit:
                continue
            w.setFocusPolicy(Qt.NoFocus)

        self._select_all_btn.clicked.connect(self._select_all_visible)
        self._invert_btn.clicked.connect(self._invert_visible)
        self._clear_btn.clicked.connect(self._clear_visible)
        self._list.itemChanged.connect(self._on_item_changed)

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

    def selected_values(self) -> list:
        return [self._list.item(i).data(Qt.UserRole)
                for i in range(self._list.count())
                if self._list.item(i).checkState() == Qt.Checked]

    def selected_labels(self) -> list[str]:
        return [self._list.item(i).text()
                for i in range(self._list.count())
                if self._list.item(i).checkState() == Qt.Checked]

    def enterEvent(self, event) -> None:
        if self._owner is not None:
            self._owner._on_popup_hover_enter()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        if self._owner is not None:
            self._owner._on_popup_hover_leave()
        super().leaveEvent(event)

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

    def _select_all_visible(self) -> None:
        self._list.blockSignals(True)
        changed = False
        for i in range(self._list.count()):
            item = self._list.item(i)
            if not item.isHidden() and item.checkState() != Qt.Checked:
                item.setCheckState(Qt.Checked)
                changed = True
        self._list.blockSignals(False)
        if changed:
            self._update_count()
            self.selectionChanged.emit(self.selected_values())

    def _invert_visible(self) -> None:
        """Toggle every currently visible item's check state."""
        self._list.blockSignals(True)
        changed = False
        for i in range(self._list.count()):
            item = self._list.item(i)
            if item.isHidden():
                continue
            new_state = (Qt.Unchecked if item.checkState() == Qt.Checked
                         else Qt.Checked)
            item.setCheckState(new_state)
            changed = True
        self._list.blockSignals(False)
        if changed:
            self._update_count()
            self.selectionChanged.emit(self.selected_values())

    def _clear_visible(self) -> None:
        """Uncheck every currently visible item. Does **not** close the popup."""
        self._list.blockSignals(True)
        changed = False
        for i in range(self._list.count()):
            item = self._list.item(i)
            if not item.isHidden() and item.checkState() == Qt.Checked:
                item.setCheckState(Qt.Unchecked)
                changed = True
        self._list.blockSignals(False)
        if changed:
            self._update_count()
            self.selectionChanged.emit(self.selected_values())

    def _on_item_changed(self, _item: QListWidgetItem) -> None:
        self._update_count()
        self.selectionChanged.emit(self.selected_values())

    def _update_count(self) -> None:
        count = sum(
            1 for i in range(self._list.count())
            if self._list.item(i).checkState() == Qt.Checked
        )
        self._count_label.setText(f"已选 {count} 项")


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
                 buttons_position: str = "top",
                 theme: dict | None = None,
                 search_in_popup: bool = True,
                 string_only: bool = False) -> None:
        super().__init__(parent)
        if buttons_position not in {"top", "bottom"}:
            raise ValueError("buttons_position must be 'top' or 'bottom'")
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
                                        buttons_at_top=(buttons_position == "top"),
                                        theme=self._theme,
                                        search_in_popup=search_in_popup,
                                        string_only=string_only)
        self._popup.selectionChanged.connect(self._on_popup_selection_changed)
        self._popup.requestClose.connect(self.hide_popup)

        # Global click-outside watcher -- attached only while popup is open.
        self._outside_filter = _OutsideClickFilter(self, self._on_outside_click)

        # Hover-to-close: when the user moves the mouse OUT of both the popup
        # AND the main line-edit, the popup closes itself after a short delay.
        # Keyboard users that open the popup from afar never trigger
        # leaveEvent on the main widget (cursor never entered it), so the
        # popup stays open until they click outside or press Esc.
        self._leave_close_timer = QTimer(self)
        self._leave_close_timer.setSingleShot(True)
        self._leave_close_timer.setInterval(220)
        self._leave_close_timer.timeout.connect(self._check_close_on_hover_leave)
        self.setMouseTracking(True)

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
        self._leave_close_timer.stop()
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
        self._leave_close_timer.stop()
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

    # ---- hover-to-close --------------------------------------------------
    def _on_popup_hover_enter(self) -> None:
        """Called from the popup's enterEvent -- cancels any pending close."""
        if not self._popup_open:
            return
        self._leave_close_timer.stop()

    def _on_popup_hover_leave(self) -> None:
        """Called from the popup's leaveEvent -- arms the close timer."""
        if not self._popup_open:
            return
        self._leave_close_timer.start()

    def enterEvent(self, event) -> None:    # main combo box
        if self._popup_open:
            self._leave_close_timer.stop()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:    # main combo box
        if self._popup_open:
            self._leave_close_timer.start()
        super().leaveEvent(event)

    def _check_close_on_hover_leave(self) -> None:
        """Close the popup only if the cursor is now outside BOTH regions."""
        if not self._popup_open:
            return
        pos = QCursor.pos()
        w = QApplication.widgetAt(pos)
        while w is not None:
            if w is self._popup or w is self:
                return
            w = w.parentWidget()
        self.hide_popup()

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
