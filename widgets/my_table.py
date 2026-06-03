from __future__ import annotations

from typing import Any, Iterable, Sequence

from PySide6.QtCore import (
    QEvent,
    QModelIndex,
    QPoint,
    QRect,
    QSize,
    QSortFilterProxyModel,
    Qt,
    Signal,
)
from PySide6.QtGui import (
    QAction,
    QColor,
    QIcon,
    QMouseEvent,
    QPainter,
    QPen,
    QPixmap,
    QStandardItem,
    QStandardItemModel,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QStyle,
    QStyleOptionViewItem,
    QStyledItemDelegate,
    QTableView,
    QToolButton,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QStyle,
    QStyleOptionButton,
    QStyleOptionHeader,
    QStyledItemDelegate,
    QTableView,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


_FILTER_ICON_SVG_OUTLINE = """
<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'>
  <path d='M2 3h12l-4.5 6V14l-3-1.5V9L2 3z'
        fill='none' stroke='{color}' stroke-width='1.4'
        stroke-linejoin='round' stroke-linecap='round'/>
</svg>
"""

_FILTER_ICON_SVG_FILLED = """
<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'>
  <path d='M2 3h12l-4.5 6V14l-3-1.5V9L2 3z'
        fill='{fill}' stroke='{stroke}' stroke-width='1.2'
        stroke-linejoin='round' stroke-linecap='round'/>
  <circle cx='12.5' cy='3.5' r='2.6' fill='{dot}' stroke='white' stroke-width='1'/>
</svg>
"""

# A compact "up + down" arrow stack used as a sort indicator.
# Each arrow can be coloured independently so we can highlight the active
# sort direction while keeping the other arrow visible but muted.
_SORT_ICON_SVG = """
<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 8 14'>
  <path d='M4 0 L7.2 4.2 L0.8 4.2 Z' fill='{up}'/>
  <path d='M4 14 L7.2 9.8 L0.8 9.8 Z' fill='{down}'/>
</svg>
"""


def _render_svg(svg: str, width: int = 16, height: int | None = None) -> QIcon:
    from PySide6.QtCore import QByteArray
    from PySide6.QtSvg import QSvgRenderer

    if height is None:
        height = width
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    pixmap = QPixmap(width, height)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)


def _filter_icon_normal() -> QIcon:
    return _render_svg(_FILTER_ICON_SVG_OUTLINE.format(color="#80868b"))


def _filter_icon_active() -> QIcon:
    return _render_svg(_FILTER_ICON_SVG_FILLED.format(
        fill="#1a73e8", stroke="#1a73e8", dot="#ea4335"
    ))


_SORT_MUTED = "#bdc1c6"     # neutral arrow colour
_SORT_ACTIVE = "#1a73e8"    # highlighted arrow colour


def _sort_icon(up_active: bool = False, down_active: bool = False) -> QIcon:
    up = _SORT_ACTIVE if up_active else _SORT_MUTED
    down = _SORT_ACTIVE if down_active else _SORT_MUTED
    return _render_svg(_SORT_ICON_SVG.format(up=up, down=down), width=8, height=14)


class _MultiColumnFilterProxy(QSortFilterProxyModel):
    """Proxy model that filters multiple columns by a set of allowed values
    or by one or more numeric comparisons (>, <, =, >=, <=, !=) combined with
    logical AND — e.g. ``[(">", 200), ("<", 300)]`` keeps rows whose cell is
    in the open interval (200, 300)."""

    NUMERIC_OPS: tuple[str, ...] = ("=", "!=", ">", ">=", "<", "<=")

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._allowed: dict[int, set[str]] = {}
        # column -> list of (op, value) combined with AND
        self._numeric: dict[int, list[tuple[str, float]]] = {}

    # ---- text filters ----------------------------------------------------
    def set_column_filter(self, column: int, allowed_values: set[str] | None) -> None:
        if allowed_values is None:
            self._allowed.pop(column, None)
        else:
            self._allowed[column] = set(allowed_values)
        self.invalidateFilter()

    def column_filter(self, column: int) -> set[str] | None:
        return self._allowed.get(column)

    # ---- numeric filters -------------------------------------------------
    def set_column_numeric_filter(self, column: int,
                                  conditions: Sequence[tuple[str, float]] | None) -> None:
        """Replace the numeric filter for *column* with the given conditions.

        Pass ``None`` or an empty list to clear. Each condition is
        ``(op, value)``; all conditions are combined with logical AND.
        """
        if conditions is None:
            self._numeric.pop(column, None)
        else:
            cleaned: list[tuple[str, float]] = []
            for op, value in conditions:
                if op not in self.NUMERIC_OPS:
                    raise ValueError(
                        f"unsupported op {op!r}; expected one of {self.NUMERIC_OPS}"
                    )
                cleaned.append((op, float(value)))
            if cleaned:
                self._numeric[column] = cleaned
            else:
                self._numeric.pop(column, None)
        self.invalidateFilter()

    def add_numeric_condition(self, column: int, op: str, value: float) -> None:
        if op not in self.NUMERIC_OPS:
            raise ValueError(f"unsupported op {op!r}; expected one of {self.NUMERIC_OPS}")
        self._numeric.setdefault(column, []).append((op, float(value)))
        self.invalidateFilter()

    def clear_column_numeric_filter(self, column: int) -> None:
        if self._numeric.pop(column, None) is not None:
            self.invalidateFilter()

    def column_numeric_filter(self, column: int) -> list[tuple[str, float]] | None:
        """Return a copy of the numeric conditions for *column*, or ``None``."""
        lst = self._numeric.get(column)
        return list(lst) if lst is not None else None

    # ---- shared ----------------------------------------------------------
    def active_filter_columns(self) -> set[int]:
        return set(self._allowed.keys()) | set(self._numeric.keys())

    def clear_filters(self) -> None:
        self._allowed.clear()
        self._numeric.clear()
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        model = self.sourceModel()
        if model is None:
            return True
        for column, allowed in self._allowed.items():
            idx = model.index(source_row, column, source_parent)
            text = "" if not idx.isValid() else str(idx.data(Qt.DisplayRole) or "")
            if text not in allowed:
                return False
        for column, conditions in self._numeric.items():
            idx = model.index(source_row, column, source_parent)
            raw = "" if not idx.isValid() else idx.data(Qt.DisplayRole)
            try:
                cell = float(raw)
            except (TypeError, ValueError):
                return False
            for op, value in conditions:
                if not self._compare(cell, op, value):
                    return False   # any failing condition excludes the row
        return True

    @staticmethod
    def _compare(cell: float, op: str, value: float) -> bool:
        if op == "=":  return cell == value
        if op == "!=": return cell != value
        if op == ">":  return cell >  value
        if op == ">=": return cell >= value
        if op == "<":  return cell <  value
        if op == "<=": return cell <= value
        return True


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


class _NumericConditionRow(QWidget):
    """A single row in the numeric filter popup: ``[op] [value] [×]``.

    Emits :attr:`removeRequested` when the user clicks the small × button.
    """

    removeRequested = Signal(object)   # emits self

    def __init__(self, op: str = "=", value: float = 0.0,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._op = QComboBox(self)
        for label, data in [("等于 =", "="), ("不等于 ≠", "!="),
                            ("大于 >", ">"), ("大于等于 ≥", ">="),
                            ("小于 <", "<"), ("小于等于 ≤", "<=")]:
            self._op.addItem(label, data)
        idx = self._op.findData(op)
        if idx >= 0:
            self._op.setCurrentIndex(idx)

        self._value = QDoubleSpinBox(self)
        self._value.setRange(-1e15, 1e15)
        self._value.setDecimals(2)
        self._value.setSingleStep(1.0)
        self._value.setMinimumWidth(120)
        self._value.setValue(value)

        self._remove = QToolButton(self)
        self._remove.setText("×")
        self._remove.setToolTip("删除该条件")
        self._remove.setFixedSize(24, 24)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addWidget(self._op)
        layout.addWidget(self._value, 1)
        layout.addWidget(self._remove)
        self._remove.clicked.connect(lambda: self.removeRequested.emit(self))

    def condition(self) -> tuple[str, float]:
        return (self._op.currentData(), self._value.value())


class _FilterPopup(QFrame):
    """Excel-style column filter popup with search + checkable values
    or numeric comparison (one or more AND-combined conditions).

    Numeric mode lets the user add multiple ``(op, value)`` conditions —
    e.g. ``(> 200)`` AND ``(< 300)`` — and remove them individually.

    Implemented as a :class:`QFrame` with the ``Qt.Popup`` window flag rather
    than as a :class:`QMenu`, because ``QMenu` interferes with IME composition
    (typing Chinese / Japanese / Korean inside the search box did not work).

    Default semantics: when no prior filter exists, the popup opens with all
    list items visually checked but is treated as "no filter active" until
    the user un-checks at least one item. This makes the empty filter the
    most natural default (selecting the funnel icon should not hide rows).
    """

    filterChanged = Signal(int, object)            # column, set or None
    numericFilterChanged = Signal(int, object)     # column, list[(op, value)] or None
    filterOnlyThis = Signal(int, object)           # column, value: "filter to only this item"

    def __init__(self, column: int, values: Iterable[str],
                 selected: set[str] | None,
                 *,
                 numeric: bool = False,
                 numeric_filter: Sequence[tuple[str, float]] | None = None,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent, Qt.Popup)
        self.setFrameShape(QFrame.NoFrame)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self._column = column
        self._all_values = sorted({str(v) for v in values},
                                  key=lambda s: (s == "", s.lower()))
        # Text-mode state.
        # Default: nothing checked (Excel-like — user explicitly checks the
        # values they want to keep). An empty selection at "确定" time is
        # treated as "no filter / show all", matching the natural workflow
        # "click what to filter". If a prior filter exists, restore it
        # verbatim so re-opening the popup shows the active filter set.
        if selected is None:
            self._selected: set[str] = set()
        else:
            self._selected = set(selected)
        # Numeric-mode state.
        self._numeric_mode = numeric
        self._condition_rows: list[_NumericConditionRow] = []

        self.setStyleSheet(
            """
            QFrame {
                background: #ffffff;
                border: 1px solid #dadce0;
                border-radius: 8px;
            }
            QLineEdit, QDoubleSpinBox, QComboBox {
                border: 1px solid #dadce0;
                border-radius: 6px;
                padding: 5px 8px;
                background: #f8f9fa;
            }
            QLineEdit:focus, QDoubleSpinBox:focus, QComboBox:focus {
                border-color: #1a73e8; background: #ffffff;
            }
            QListWidget {
                border: 1px solid #e8eaed;
                border-radius: 6px;
                background: #ffffff;
                outline: 0;
            }
            QListWidget::item { padding: 4px 6px; }
            QListWidget::item:hover { background: #f1f3f4; }
            QListWidget::item:selected { background: #e8f0fe; color: #1a73e8; }
            QPushButton {
                border: 1px solid #dadce0;
                border-radius: 6px;
                padding: 4px 12px;
                background: #ffffff;
            }
            QPushButton:hover { background: #f1f3f4; }
            QPushButton#primary {
                background: #1a73e8; color: white; border-color: #1a73e8;
            }
            QPushButton#primary:hover { background: #1765cc; }
            QCheckBox { padding: 2px; }
            QToolButton {
                border: 1px solid #dadce0;
                border-radius: 4px;
                background: #ffffff;
                padding: 0;
            }
            QToolButton:hover { background: #fce8e6; color: #c5221f; }
            QToolButton#HoverOnly {
                background: #1a73e8;
                color: #ffffff;
                border: 1px solid #1a73e8;
                border-radius: 10px;
                padding: 1px 8px;
                font-size: 11px;
            }
            QToolButton#HoverOnly:hover { background: #1765cc; border-color: #1765cc; }
            """
        )

        v = QVBoxLayout(self)
        v.setContentsMargins(8, 8, 8, 8)
        v.setSpacing(6)

        sort_row = QHBoxLayout()
        sort_row.setSpacing(4)
        self._sort_asc = QPushButton("\u2191 升序")
        self._sort_desc = QPushButton("\u2193 降序")
        sort_row.addWidget(self._sort_asc)
        sort_row.addWidget(self._sort_desc)
        v.addLayout(sort_row)

        # Numeric-mode toggle (only when column is registered as numeric).
        self._numeric_toggle: QCheckBox | None = None
        self._numeric_container: QWidget | None = None
        self._numeric_layout: QVBoxLayout | None = None
        if numeric:
            self._numeric_toggle = QCheckBox("按数字比较", self)
            v.addWidget(self._numeric_toggle)

            self._numeric_container = QWidget(self)
            self._numeric_layout = QVBoxLayout(self._numeric_container)
            self._numeric_layout.setContentsMargins(0, 0, 0, 0)
            self._numeric_layout.setSpacing(4)
            v.addWidget(self._numeric_container)

            # Seed with prior conditions, or a single default row.
            if numeric_filter:
                for op, val in numeric_filter:
                    self._add_condition_row(op, val)
                self._numeric_toggle.setChecked(True)
            else:
                self._add_condition_row("=", 0.0)

            self._add_btn = QPushButton("+ 添加条件", self._numeric_container)
            self._add_btn.setToolTip("再增加一个比较条件(AND 关系)")
            self._numeric_layout.addWidget(self._add_btn)
            self._add_btn.clicked.connect(lambda: (self._add_condition_row("=", 0.0),
                                                   self._sync_remove_buttons()))

        # Text-mode widgets: 全选 checkbox → search box → list.
        self._select_all = QCheckBox("全选", self)
        self._select_all.setTristate(True)
        v.addWidget(self._select_all)

        self._search = QLineEdit(self)
        self._search.setPlaceholderText("搜索...")
        self._search.setClearButtonEnabled(True)
        v.addWidget(self._search)

        self._list = _CheckListWidget(self)
        self._list.setSelectionMode(QAbstractItemView.NoSelection)
        self._list.setMinimumHeight(180)
        self._list.setMaximumHeight(280)
        self._list.setMinimumWidth(220)
        v.addWidget(self._list)

        btn_row = QHBoxLayout()
        self._invert_btn = QPushButton("反选")
        self._reset_btn = QPushButton("重置")
        btn_row.addWidget(self._invert_btn)
        btn_row.addWidget(self._reset_btn)
        btn_row.addStretch(1)
        self._cancel_btn = QPushButton("取消")
        self._ok_btn = QPushButton("确定")
        self._ok_btn.setObjectName("primary")
        btn_row.addWidget(self._cancel_btn)
        btn_row.addWidget(self._ok_btn)
        v.addLayout(btn_row)

        # -- hover-only "仅筛此项" overlay -------------------------------
        # Parented to the list viewport so that mouse movement between a
        # list item and the button does NOT trigger viewport Leave (which
        # would instantly hide the button, causing flicker when the user
        # tries to click it).
        self._hover_only_btn = QToolButton(self._list.viewport())
        self._hover_only_btn.setText("仅筛此项")
        self._hover_only_btn.setObjectName("HoverOnly")
        self._hover_only_btn.setCursor(Qt.PointingHandCursor)
        self._hover_only_btn.setToolTip("把筛选替换为只看这一项")
        self._hover_only_btn.hide()
        self._hover_only_btn.setFocusPolicy(Qt.NoFocus)
        self._hover_only_btn.clicked.connect(self._on_hover_only_clicked)
        self._hover_only_target: QListWidgetItem | None = None
        self._list.setMouseTracking(True)
        self._list.itemEntered.connect(self._on_list_item_entered)
        self._list.viewport().installEventFilter(self)

        self._populate_list("")

        self._search.textChanged.connect(self._populate_list)
        self._select_all.clicked.connect(self._on_select_all_clicked)
        self._list.itemChanged.connect(self._on_item_changed)
        self._sort_asc.clicked.connect(lambda: self._on_popup_sort(Qt.AscendingOrder))
        self._sort_desc.clicked.connect(lambda: self._on_popup_sort(Qt.DescendingOrder))
        self._invert_btn.clicked.connect(self._on_invert)
        self._reset_btn.clicked.connect(self._on_reset)
        self._ok_btn.clicked.connect(self._on_ok)
        self._cancel_btn.clicked.connect(self.close)
        if self._numeric_toggle is not None:
            self._numeric_toggle.toggled.connect(self._on_numeric_toggled)
            self._apply_numeric_visibility()
            self._sync_remove_buttons()

    # ---- numeric rows ----------------------------------------------------
    def _add_condition_row(self, op: str, value: float) -> _NumericConditionRow:
        assert self._numeric_layout is not None
        row = _NumericConditionRow(op, value, self._numeric_container)
        row.removeRequested.connect(self._on_remove_row)
        # insert *before* the "+ 添加条件" button (which is the last item)
        self._numeric_layout.insertWidget(self._numeric_layout.count() - 1, row)
        self._condition_rows.append(row)
        return row

    def _on_remove_row(self, row: _NumericConditionRow) -> None:
        if len(self._condition_rows) <= 1:
            # Never leave the popup with zero rows; the last row is reset instead.
            row._op.setCurrentIndex(0)
            row._value.setValue(0.0)
            return
        self._condition_rows.remove(row)
        self._numeric_layout.removeWidget(row)
        row.setParent(None)
        row.deleteLater()
        self._sync_remove_buttons()

    def _sync_remove_buttons(self) -> None:
        # Disable the × button when there's only one row left so the user
        # always has at least one condition to fill in.
        for r in self._condition_rows:
            r._remove.setEnabled(len(self._condition_rows) > 1)

    def _collect_conditions(self) -> list[tuple[str, float]]:
        return [r.condition() for r in self._condition_rows]

    # ---- numeric toggle --------------------------------------------------
    def _on_numeric_toggled(self, checked: bool) -> None:
        self._apply_numeric_visibility()

    def _apply_numeric_visibility(self) -> None:
        if self._numeric_toggle is None:
            return
        numeric_on = self._numeric_toggle.isChecked()
        for w in (self._search, self._select_all, self._list):
            (w.show if not numeric_on else w.hide)()
        if self._numeric_container is not None:
            (self._numeric_container.show if numeric_on else self._numeric_container.hide)()
        # 触发 layout 重算
        self.layout().invalidate()

    # ---- list population -------------------------------------------------
    def _populate_list(self, query: str) -> None:
        self._list.blockSignals(True)
        self._list.clear()
        q = query.strip().lower()
        for value in self._all_values:
            display = value if value != "" else "(空白)"
            if q and q not in display.lower():
                continue
            item = QListWidgetItem(display)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if value in self._selected else Qt.Unchecked)
            item.setData(Qt.UserRole, value)
            self._list.addItem(item)
        self._list.blockSignals(False)
        self._update_select_all_state()
        # The previously hovered item is gone after a clear()/repopulate().
        if self._hover_only_target is not None:
            self._hover_only_btn.hide()
            self._hover_only_target = None

    def _update_select_all_state(self) -> None:
        total = self._list.count()
        checked = sum(
            1 for i in range(total)
            if self._list.item(i).checkState() == Qt.Checked
        )
        self._select_all.blockSignals(True)
        if total == 0 or checked == 0:
            self._select_all.setCheckState(Qt.Unchecked)
        elif checked == total:
            self._select_all.setCheckState(Qt.Checked)
        else:
            self._select_all.setCheckState(Qt.PartiallyChecked)
        self._select_all.blockSignals(False)

    def _on_select_all_clicked(self) -> None:
        # Toggle based on the *list* state, not the QCheckBox's own state.
        # Rationale: a QCheckBox with ``setTristate(True)`` runs a 3-state
        # cycle internally (Unchecked → PartiallyChecked → Checked → ...),
        # and our explicit ``setCheckState`` call in this handler can put
        # the box out of sync with Qt's "next click" machinery — the
        # second click on an all-checked list then appears to do nothing.
        # Looking at the list (the actual data) is the only robust way:
        # all checked → uncheck all; any unchecked → check all.
        n = self._list.count()
        all_checked = n > 0 and all(
            self._list.item(i).checkState() == Qt.Checked for i in range(n)
        )
        state = Qt.Unchecked if all_checked else Qt.Checked
        self._select_all.setCheckState(state)
        self._list.blockSignals(True)
        for i in range(n):
            self._list.item(i).setCheckState(state)
        self._list.blockSignals(False)
        self._sync_selected_from_list()

    def _on_item_changed(self, _item: QListWidgetItem) -> None:
        self._sync_selected_from_list()
        self._update_select_all_state()

    def _sync_selected_from_list(self) -> None:
        for i in range(self._list.count()):
            item = self._list.item(i)
            value = item.data(Qt.UserRole)
            if item.checkState() == Qt.Checked:
                self._selected.add(value)
            else:
                self._selected.discard(value)

    def _on_popup_sort(self, order: Qt.SortOrder) -> None:
        # Sort the *visible* items in the popup (not the main table).
        # The main table's column sort lives on the header arrows; the
        # popup's 升序/降序 are an internal convenience for finding
        # values in long lists. Empty strings ("(空白)") are always pinned
        # to the end so they don't break a-z/ z-a order.
        n = self._list.count()
        if n <= 1:
            return
        items: list[dict] = []
        for i in range(n):
            it = self._list.item(i)
            items.append({
                "display": it.text(),
                "value": it.data(Qt.UserRole),
                "checked": it.checkState() == Qt.Checked,
            })
        reverse = (order == Qt.DescendingOrder)
        empties = [x for x in items if x["display"] == "(空白)"]
        non_empty = [x for x in items if x["display"] != "(空白)"]
        non_empty.sort(key=lambda x: x["display"].lower(), reverse=reverse)
        items = non_empty + empties  # "(空白)" always at end

        self._list.blockSignals(True)
        self._list.clear()
        for it in items:
            li = QListWidgetItem(it["display"])
            li.setFlags(li.flags() | Qt.ItemIsUserCheckable)
            li.setCheckState(Qt.Checked if it["checked"] else Qt.Unchecked)
            li.setData(Qt.UserRole, it["value"])
            self._list.addItem(li)
        self._list.blockSignals(False)
        self._update_select_all_state()

    def _on_invert(self) -> None:
        # Invert every visible item's check state (mirror of MyCombo's
        # ``反选`` button). Local to the popup — does not apply / close.
        self._list.blockSignals(True)
        for i in range(self._list.count()):
            it = self._list.item(i)
            if it.isHidden():
                continue
            it.setCheckState(Qt.Unchecked if it.checkState() == Qt.Checked
                             else Qt.Checked)
        self._list.blockSignals(False)
        self._sync_selected_from_list()
        self._update_select_all_state()

    def _on_reset(self) -> None:
        # 重置: uncheck every visible item in the popup. Local action —
        # does NOT close, does NOT emit any filter signal. The user can
        # pick again. To actually apply the empty selection (= "no
        # filter / show all") they still need to click 确定.
        self._list.blockSignals(True)
        for i in range(self._list.count()):
            it = self._list.item(i)
            if not it.isHidden() and it.checkState() == Qt.Checked:
                it.setCheckState(Qt.Unchecked)
        self._list.blockSignals(False)
        self._sync_selected_from_list()
        self._update_select_all_state()

    def _on_ok(self) -> None:
        if self._numeric_toggle is not None and self._numeric_toggle.isChecked():
            conditions = self._collect_conditions()
            self.numericFilterChanged.emit(self._column, conditions)
            # 同时清理文本 filter
            self.filterChanged.emit(self._column, None)
        else:
            # Excel-like semantics: empty selection = no filter (show all).
            # The user sees an unchecked list and "确定" without picking
            # anything → fall back to the un-filtered default. Non-empty
            # selection → keep only the checked values.
            if not self._selected:
                self.filterChanged.emit(self._column, None)
            else:
                self.filterChanged.emit(self._column, set(self._selected))
            # 清理 numeric filter (回到纯文本模式)
            self.numericFilterChanged.emit(self._column, None)
        self.close()

    def show_at(self, global_pos: QPoint) -> None:
        from PySide6.QtWidgets import QApplication

        self.adjustSize()
        size = self.sizeHint()
        screen = QApplication.screenAt(global_pos)
        rect = screen.availableGeometry() if screen else QRect(0, 0, 1920, 1080)
        x = min(global_pos.x(), rect.right() - size.width())
        x = max(x, rect.left())
        y = global_pos.y()
        if y + size.height() > rect.bottom():
            y = max(rect.top(), global_pos.y() - size.height())
        self.move(x, y)
        self.show()
        if self._numeric_toggle is not None and self._numeric_toggle.isChecked() \
                and self._condition_rows:
            self._condition_rows[0]._value.setFocus()
            self._condition_rows[0]._value.selectAll()
        else:
            self._search.setFocus()

    # ---- hover-only "仅筛此项" overlay ---------------------------------
    def _on_list_item_entered(self, item: QListWidgetItem) -> None:
        if item is None or item.isHidden():
            self._hover_only_btn.hide()
            self._hover_only_target = None
            return
        rect = self._list.visualItemRect(item)
        if rect.isNull():
            self._hover_only_btn.hide()
            self._hover_only_target = None
            return
        btn = self._hover_only_btn
        btn.adjustSize()
        bw, bh = btn.sizeHint().width(), btn.sizeHint().height()
        # ``visualItemRect`` is viewport-local, and the button is now
        # parented to the viewport, so offset-free positioning works.
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
        self.filterOnlyThis.emit(self._column, value)
        # Self-close so the user doesn't need to dismiss the popup — this
        # is a one-click shortcut for "filter to this single value".
        self.close()

    def hideEvent(self, event) -> None:
        # Reset hover overlay state on close so the next open starts clean.
        self._hover_only_btn.hide()
        self._hover_only_target = None
        super().hideEvent(event)

    def eventFilter(self, watched, event):
        # Hide the floating "仅筛此项" button when the cursor leaves the
        # list viewport — the item is no longer the one the user is
        # looking at.
        if watched is self._list.viewport() and event.type() == QEvent.Leave:
            self._hover_only_btn.hide()
            self._hover_only_target = None
        return super().eventFilter(watched, event)


class _FilterHeaderView(QHeaderView):
    """Header view that draws a clickable filter icon for each column.

    Layout per section (left to right)::

        |  text  |   ↕ sort   |   filter  |
                              ^^^^^^^^^^^^^
                              fixed-width zone reserved by the right padding

    The native sort indicator is disabled (``setSortIndicatorShown(False)``)
    and replaced by a custom up/down arrow stack so that:
      * both arrows are always visible (active direction highlighted blue),
      * the sort indicator sits to the **left** of the filter funnel and never
        overlaps it.
    """

    filterClicked = Signal(int, QPoint)
    checkAllClicked = Signal(int)  # emitted when the 全选 header checkbox is clicked

    # geometry constants for the right-side icon area
    FILTER_SIZE = 16
    FILTER_MARGIN = 6
    SORT_W = 8
    SORT_H = 14
    SORT_GAP = 6           # gap between sort arrows and filter funnel
    SORT_TEXT_GAP = 6      # min gap between text and sort arrows

    def __init__(self, orientation: Qt.Orientation, parent: QWidget | None = None) -> None:
        super().__init__(orientation, parent)
        self.setSectionsClickable(True)
        self.setSectionsMovable(True)
        self.setHighlightSections(True)
        # Disable Qt's built-in indicator -- we draw our own dual-arrow icon.
        self.setSortIndicatorShown(False)
        self.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.setMouseTracking(True)
        self._hover_section = -1
        self._active_columns: set[int] = set()
        self._skip_filter_columns: set[int] = set()
        self._icon_normal = _filter_icon_normal()
        self._icon_active = _filter_icon_active()
        self._sort_neutral = _sort_icon(False, False)
        self._sort_asc = _sort_icon(up_active=True)
        self._sort_desc = _sort_icon(down_active=True)
        self._check_column = -1       # column index for the 全选 header checkbox
        self._all_checked = False     # visual state of the header checkbox
        self.setMinimumSectionSize(80)
        self.setDefaultSectionSize(140)

    def set_active(self, column: int, active: bool) -> None:
        if active:
            self._active_columns.add(column)
        else:
            self._active_columns.discard(column)
        self.viewport().update()

    def set_filter_skipped(self, column: int, skipped: bool) -> None:
        """When True, the filter icon will not be drawn / clickable for the column."""
        if skipped:
            self._skip_filter_columns.add(column)
        else:
            self._skip_filter_columns.discard(column)
        self.viewport().update()

    def set_check_column(self, column: int) -> None:
        """Designate ``column`` as the row-checkbox column (draws 全选 in header)."""
        self._check_column = column
        self.viewport().update()

    def set_all_checked(self, checked: bool) -> None:
        """Update the visual state of the 全选 header checkbox."""
        self._all_checked = checked
        self.viewport().update()

    @property
    def check_column(self) -> int:
        return self._check_column

    # ---- geometry helpers ------------------------------------------------
    def _filter_rect(self, logical_index: int) -> QRect:
        size = self.FILTER_SIZE
        margin = self.FILTER_MARGIN
        x = (self.sectionViewportPosition(logical_index)
             + self.sectionSize(logical_index) - size - margin)
        return QRect(x, (self.height() - size) // 2, size, size)

    def _sort_rect(self, logical_index: int) -> QRect:
        skip_filter = logical_index in self._skip_filter_columns
        section_right = (self.sectionViewportPosition(logical_index)
                         + self.sectionSize(logical_index))
        if skip_filter:
            right_anchor = section_right - self.FILTER_MARGIN
        else:
            right_anchor = (section_right - self.FILTER_MARGIN
                            - self.FILTER_SIZE - self.SORT_GAP)
        x = right_anchor - self.SORT_W
        y = (self.height() - self.SORT_H) // 2
        return QRect(x, y, self.SORT_W, self.SORT_H)

    def _icon_rect(self, logical_index: int) -> QRect:
        # Kept for backwards compatibility (used by mousePressEvent).
        return self._filter_rect(logical_index)

    # ---- painting --------------------------------------------------------
    def paintSection(self, painter: QPainter, rect: QRect, logical_index: int) -> None:
        painter.save()
        super().paintSection(painter, rect, logical_index)
        painter.restore()

        # ---- 全选 checkbox for the check column --------------------------
        if logical_index == self._check_column:
            cb_sz = 14
            margin_left = 8
            cb_x = rect.x() + margin_left
            cb_y = rect.y() + (rect.height() - cb_sz) // 2
            cb_opt = QStyleOptionButton()
            cb_opt.rect = QRect(cb_x, cb_y, cb_sz, cb_sz)
            cb_opt.state = QStyle.State_Enabled
            if self._all_checked:
                cb_opt.state |= QStyle.State_On
            else:
                cb_opt.state |= QStyle.State_Off
            self.style().drawPrimitive(QStyle.PE_IndicatorCheckBox, cb_opt, painter)
            # "全选" text to the right of the checkbox
            text_x = cb_x + cb_sz + 3
            text_rect = QRect(text_x, rect.y(), rect.right() - text_x, rect.height())
            painter.save()
            painter.setPen(self.palette().windowText().color())
            painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, "全选")
            painter.restore()

        sort_col = self.sortIndicatorSection()
        sort_order = self.sortIndicatorOrder()
        is_sorted = (sort_col == logical_index)
        hover = (logical_index == self._hover_section)

        # ---- sort indicator (always-on when sorted, otherwise on hover) --
        if is_sorted or hover:
            if is_sorted:
                sort_icon = (self._sort_asc
                             if sort_order == Qt.AscendingOrder
                             else self._sort_desc)
            else:
                sort_icon = self._sort_neutral
            sort_x = (rect.right() - self.FILTER_MARGIN
                      - self.FILTER_SIZE - self.SORT_GAP - self.SORT_W)
            if logical_index in self._skip_filter_columns:
                sort_x = rect.right() - self.FILTER_MARGIN - self.SORT_W
            sort_y = rect.y() + (rect.height() - self.SORT_H) // 2
            sort_icon.paint(painter,
                            QRect(sort_x, sort_y, self.SORT_W, self.SORT_H))

        # ---- filter funnel ----------------------------------------------
        if logical_index in self._skip_filter_columns:
            return
        active = logical_index in self._active_columns
        if not active and not hover:
            return
        icon = self._icon_active if active else self._icon_normal
        size = self.FILTER_SIZE
        margin = self.FILTER_MARGIN
        icon_rect = QRect(
            rect.right() - size - margin,
            rect.y() + (rect.height() - size) // 2,
            size,
            size,
        )
        icon.paint(painter, icon_rect)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        section = self.logicalIndexAt(event.position().toPoint())
        if section != self._hover_section:
            self._hover_section = section
            self.viewport().update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        if self._hover_section != -1:
            self._hover_section = -1
            self.viewport().update()
        super().leaveEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            section = self.logicalIndexAt(event.position().toPoint())
            if section >= 0:
                # 全选 header checkbox click (check column may be in skip list)
                if section == self._check_column and self._check_column >= 0:
                    self.checkAllClicked.emit(section)
                    event.accept()
                    return
                if section in self._skip_filter_columns:
                    super().mousePressEvent(event)
                    return
                icon_rect = self._icon_rect(section)
                if icon_rect.contains(event.position().toPoint()):
                    global_pos = self.mapToGlobal(QPoint(icon_rect.left(), self.height()))
                    self.filterClicked.emit(section, global_pos)
                    return
        super().mousePressEvent(event)


class MyTable(QTableView):
    """A modern table view with per-column filter, drag-to-reorder, and sorting.

    Optional features that can be enabled at runtime:
        * row checkboxes via :meth:`set_checkable_rows`
        * per-column editability via :meth:`set_editable_columns`
        * row deletion via :meth:`delete_rows`, :meth:`delete_selected_rows`
          and :meth:`delete_checked_rows`
    """

    rowsDeleted = Signal(list)               # source row indices (descending)
    rowChecked = Signal(int, bool)           # source row, checked
    cellEdited = Signal(int, int, object)    # source row, column, new value

    def __init__(self, parent: QWidget | None = None,
                 *, skip_filter_columns: Iterable[int] = ()) -> None:
        super().__init__(parent)
        self._proxy = _MultiColumnFilterProxy(self)
        super().setModel(self._proxy)

        self._header = _FilterHeaderView(Qt.Horizontal, self)
        self.setHorizontalHeader(self._header)
        self._header.filterClicked.connect(self._show_filter_menu)
        self._header.checkAllClicked.connect(self._on_header_check_all)

        self.setSortingEnabled(True)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setShowGrid(False)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(30)
        self.setMouseTracking(True)

        # ``QTableView.setHorizontalHeader`` (and ``setSortingEnabled``) reset
        # the header's sort-indicator-shown flag back to True, so the call
        # we make in ``_FilterHeaderView.__init__`` is not enough. Re-disable
        # after the table is fully wired up — we draw our own arrow icon.
        self._header.setSortIndicatorShown(False)

        # Remove the dotted focus rectangle from all items.
        self.setItemDelegate(NoFocusDelegate(self))
        # Auto-check rows when selected via drag / shift-click / single click.
        self.selectionModel().selectionChanged.connect(self._on_sel_changed)

        self._checkable_rows = False
        self._check_column = 0
        self._editable_columns: set[int] | None = None  # None = none, set = whitelist
        self._all_editable = False
        self._numeric_columns: set[int] = set()
        # Static "no filter icon" columns (e.g. action column with inline buttons).
        self._skip_filter_columns: set[int] = {int(c) for c in skip_filter_columns}

        self._apply_style()

    # ------------------------------------------------------------------
    # styling
    # ------------------------------------------------------------------
    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
            QTableView {
                background: #ffffff;
                alternate-background-color: #f8f9fa;
                gridline-color: #e8eaed;
                border: 1px solid #dadce0;
                border-radius: 8px;
                selection-background-color: #e8f0fe;
                selection-color: #202124;
                font-size: 13px;
            }
            QTableView::item { padding: 6px 8px; border: none; }
            QTableView::item:hover { background: #f1f3f4; }
            QTableView::item:selected { background: #e8f0fe; color: #1a73e8; }

            QHeaderView::section {
                background: #f8f9fa;
                color: #3c4043;
                padding: 6px 42px 6px 10px;
                border: none;
                border-right: 1px solid #e8eaed;
                border-bottom: 1px solid #dadce0;
                font-weight: 600;
                font-size: 13px;
            }
            QHeaderView::section:hover { background: #f1f3f4; }
            QHeaderView::section:pressed { background: #e8eaed; }

            QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
            QScrollBar::handle:vertical {
                background: #c4c7c5; border-radius: 5px; min-height: 24px;
            }
            QScrollBar::handle:vertical:hover { background: #9aa0a6; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
            QScrollBar:horizontal { background: transparent; height: 10px; margin: 2px; }
            QScrollBar::handle:horizontal {
                background: #c4c7c5; border-radius: 5px; min-width: 24px;
            }
            QScrollBar::handle:horizontal:hover { background: #9aa0a6; }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
            """
        )

    # ------------------------------------------------------------------
    # model wiring
    # ------------------------------------------------------------------
    def setModel(self, model) -> None:
        old = self._proxy.sourceModel()
        if old is not None:
            try:
                old.itemChanged.disconnect(self._on_source_item_changed)
            except (RuntimeError, TypeError):
                pass
        self._proxy.setSourceModel(model)
        super().setModel(self._proxy)
        self.selectionModel().selectionChanged.connect(self._on_sel_changed)
        if isinstance(model, QStandardItemModel):
            model.itemChanged.connect(self._on_source_item_changed)
        self._apply_flags_to_all()

    def sourceModel(self) -> QStandardItemModel | None:
        return self._proxy.sourceModel()

    def proxyModel(self) -> _MultiColumnFilterProxy:
        return self._proxy

    def set_data(self, headers: list[str], rows: list[list[Any]]) -> None:
        """Convenience helper to populate the table from python data."""
        model = QStandardItemModel(len(rows), len(headers), self)
        model.setHorizontalHeaderLabels(headers)
        for r, row in enumerate(rows):
            for c, value in enumerate(row):
                item = QStandardItem()
                item.setData(value, Qt.DisplayRole)
                item.setData(value, Qt.EditRole)
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                model.setItem(r, c, item)
        self.setModel(model)
        self.resizeColumnsToContents()
        for col in range(model.columnCount()):
            self._header.resizeSection(col, max(self._header.sectionSize(col) + 30, 120))

    # ------------------------------------------------------------------
    # filter management
    # ------------------------------------------------------------------
    def clear_filters(self) -> None:
        self._proxy.clear_filters()
        col_count = (self._proxy.columnCount()
                     if self._proxy.sourceModel() is not None else 0)
        for col in range(col_count):
            self._header.set_active(col, False)

    def set_filter_skipped_columns(self, columns: Iterable[int]) -> None:
        """Disable the filter icon (and clicks) for the given columns.

        Useful for action columns (e.g. the last column with inline delete
        buttons) which should never have a filter popup.
        """
        for c in columns:
            self._header.set_filter_skipped(int(c), True)
            self._skip_filter_columns.add(int(c))
            self._header.set_active(int(c), False)

    def set_column_numeric(self, column: int, enabled: bool = True) -> None:
        """Mark a column as numeric so its filter popup shows a numeric
        comparison UI (>, <, =, >=, <=, !=) alongside the default checkbox
        list. Has no effect on the data model — only on the filter UI.
        """
        if enabled:
            self._numeric_columns.add(int(column))
        else:
            self._numeric_columns.discard(int(column))
            self._proxy.clear_column_numeric_filter(int(column))
            self._header.set_active(int(column), False)

    def column_numeric_filter(self, column: int) -> list[tuple[str, float]] | None:
        """Return the AND-combined numeric conditions for *column*, or
        ``None`` if the column has no numeric filter. Example:
        ``[(">", 200), ("<", 300)]`` keeps rows in the open interval.
        """
        return self._proxy.column_numeric_filter(column)

    def _show_filter_menu(self, column: int, global_pos: QPoint) -> None:
        source = self._proxy.sourceModel()
        if source is None:
            return
        values: list[str] = []
        seen: set[str] = set()
        for r in range(source.rowCount()):
            idx = source.index(r, column)
            text = "" if not idx.isValid() else str(idx.data(Qt.DisplayRole) or "")
            if text not in seen:
                seen.add(text)
                values.append(text)
        popup = _FilterPopup(
            column, values,
            self._proxy.column_filter(column),
            numeric=column in self._numeric_columns,
            numeric_filter=self._proxy.column_numeric_filter(column),
            parent=self,
        )
        popup.filterChanged.connect(self._on_filter_changed)
        popup.numericFilterChanged.connect(self._on_numeric_filter_changed)
        popup.filterOnlyThis.connect(self._on_filter_only_this)
        # The popup's 升序/降序 buttons sort the popup's *own* list, not the
        # main table — the main table's column sort is driven by the header
        # arrows (see ``_FilterHeaderView`` and ``_on_header_sort_indicator``).
        popup.show_at(global_pos)

    def _on_filter_only_this(self, column: int, value: object) -> None:
        # Hover-overlay shortcut: replace the column's filter with a
        # single-value set. The popup self-closes after emitting this
        # signal (see ``_FilterPopup._on_hover_only_clicked``).
        self._proxy.set_column_filter(column, {value})
        self._header.set_active(column, True)

    def _on_filter_changed(self, column: int, allowed: set[str] | None) -> None:
        self._proxy.set_column_filter(column, allowed)
        # active = has any filter (text or numeric)
        has_text = allowed is not None
        has_num = self._proxy.column_numeric_filter(column) is not None
        self._header.set_active(column, has_text or has_num)

    def _on_numeric_filter_changed(self, column: int,
                                    conditions: list[tuple[str, float]] | None) -> None:
        # ``conditions`` is None to clear, otherwise a list of (op, value) AND'd.
        self._proxy.set_column_numeric_filter(column, conditions)
        has_text = self._proxy.column_filter(column) is not None
        has_num = bool(conditions)
        self._header.set_active(column, has_text or has_num)

    # ------------------------------------------------------------------
    # checkable rows
    # ------------------------------------------------------------------
    def _on_sel_changed(self, selected: QItemSelection, deselected: QItemSelection) -> None:
        if not self._checkable_rows:
            return
        source = self._proxy.sourceModel()
        if source is None:
            return
        seen: set[int] = set()
        for idx in selected.indexes():
            src_idx = self._proxy.mapToSource(idx)
            if src_idx.isValid():
                row = src_idx.row()
                if row not in seen:
                    seen.add(row)
                    item = source.item(row, self._check_column)
                    if item is not None and (item.flags() & Qt.ItemIsUserCheckable):
                        item.setCheckState(Qt.Checked)

    def _on_header_check_all(self, column: int) -> None:
        """Toggle all row checkboxes (全选 / 取消全选)."""
        if not self._checkable_rows or column != self._check_column:
            return
        source = self._proxy.sourceModel()
        if source is None:
            return
        n = source.rowCount()
        if n == 0:
            return
        all_checked = all(
            source.item(r, self._check_column).checkState() == Qt.Checked
            for r in range(n)
            if source.item(r, self._check_column) is not None
        )
        new_state = Qt.Unchecked if all_checked else Qt.Checked
        for r in range(n):
            item = source.item(r, self._check_column)
            if item is not None and (item.flags() & Qt.ItemIsUserCheckable):
                item.setCheckState(new_state)
        self._sync_header_check_state()

    def set_checkable_rows(self, enabled: bool, column: int = 0) -> None:
        """Show a checkbox in ``column`` of every row.

        The check column is excluded from the filter UI and from editability.
        """
        self._checkable_rows = enabled
        self._check_column = column
        self._header.set_check_column(column if enabled else -1)
        self._header.set_all_checked(False)
        if enabled:
            self._header.set_filter_skipped(column, True)
            self.setColumnWidth(column, 56)
        else:
            self._header.set_filter_skipped(column, False)
        self._apply_flags_to_all()
        if enabled:
            self._sync_header_check_state()

    def checked_rows(self) -> list[int]:
        """Return *source* row indices whose checkbox is currently checked."""
        if not self._checkable_rows:
            return []
        source = self._proxy.sourceModel()
        if source is None:
            return []
        out: list[int] = []
        for r in range(source.rowCount()):
            item = source.item(r, self._check_column)
            if item is not None and item.checkState() == Qt.Checked:
                out.append(r)
        return out

    def set_row_checked(self, source_row: int, checked: bool) -> None:
        source = self._proxy.sourceModel()
        if source is None or not self._checkable_rows:
            return
        item = source.item(source_row, self._check_column)
        if item is not None:
            item.setCheckState(Qt.Checked if checked else Qt.Unchecked)

    def set_all_checked(self, checked: bool) -> None:
        source = self._proxy.sourceModel()
        if source is None or not self._checkable_rows:
            return
        state = Qt.Checked if checked else Qt.Unchecked
        for r in range(source.rowCount()):
            item = source.item(r, self._check_column)
            if item is not None:
                item.setCheckState(state)

    # ------------------------------------------------------------------
    # editability
    # ------------------------------------------------------------------
    def set_editable_columns(self, columns: Sequence[int] | bool) -> None:
        """Allow cell editing.

        Pass ``True`` to make every column editable, an iterable of column
        indices to only allow those columns, or ``False`` to disable editing.
        """
        if columns is True:
            self._all_editable = True
            self._editable_columns = None
            self.setEditTriggers(
                QAbstractItemView.DoubleClicked
                | QAbstractItemView.EditKeyPressed
                | QAbstractItemView.SelectedClicked
            )
        elif columns is False or columns is None:
            self._all_editable = False
            self._editable_columns = None
            self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        else:
            self._all_editable = False
            self._editable_columns = set(int(c) for c in columns)
            self.setEditTriggers(
                QAbstractItemView.DoubleClicked
                | QAbstractItemView.EditKeyPressed
                | QAbstractItemView.SelectedClicked
            )
        self._apply_flags_to_all()

    def _column_is_editable(self, column: int) -> bool:
        if self._checkable_rows and column == self._check_column:
            return False
        if self._all_editable:
            return True
        if self._editable_columns is None:
            return False
        return column in self._editable_columns

    def _apply_flags_to_all(self) -> None:
        source = self._proxy.sourceModel()
        if source is None:
            return
        for r in range(source.rowCount()):
            self._apply_flags_to_row(r)

    def _apply_flags_to_row(self, row: int) -> None:
        source = self._proxy.sourceModel()
        if source is None:
            return
        for c in range(source.columnCount()):
            item = source.item(row, c)
            if item is None:
                item = QStandardItem()
                source.setItem(row, c, item)
            flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled
            if self._checkable_rows and c == self._check_column:
                flags |= Qt.ItemIsUserCheckable
                item.setCheckState(item.checkState())  # 同步 CheckStateRole data
                item.setData("", Qt.DisplayRole)
            elif self._column_is_editable(c):
                flags |= Qt.ItemIsEditable
            item.setFlags(flags)

    def _on_source_item_changed(self, item: QStandardItem) -> None:
        if (self._checkable_rows and item.column() == self._check_column):
            checked = item.checkState() == Qt.Checked
            self.rowChecked.emit(item.row(), checked)
            self._sync_header_check_state()
            return
        if self._column_is_editable(item.column()):
            self.cellEdited.emit(item.row(), item.column(), item.data(Qt.EditRole))

    def _sync_header_check_state(self) -> None:
        """Synchronise the 全选 header checkbox with the current row state."""
        source = self._proxy.sourceModel()
        if source is None or not self._checkable_rows:
            return
        n = source.rowCount()
        if n == 0:
            self._header.set_all_checked(False)
            return
        all_checked = all(
            source.item(r, self._check_column).checkState() == Qt.Checked
            for r in range(n)
            if source.item(r, self._check_column) is not None
        )
        self._header.set_all_checked(all_checked)

    # ------------------------------------------------------------------
    # row deletion
    # ------------------------------------------------------------------
    def delete_rows(self, source_rows: Iterable[int]) -> list[int]:
        """Remove the given *source* rows (any order). Returns rows actually removed."""
        source = self._proxy.sourceModel()
        if source is None:
            return []
        unique = sorted({int(r) for r in source_rows}, reverse=True)
        removed: list[int] = []
        for r in unique:
            if 0 <= r < source.rowCount():
                source.removeRow(r)
                removed.append(r)
        if removed:
            self.rowsDeleted.emit(removed)
        return removed

    def delete_selected_rows(self) -> list[int]:
        """Delete rows that the user has selected via row-selection in the view."""
        rows: set[int] = set()
        for idx in self.selectionModel().selectedRows():
            src = self._proxy.mapToSource(idx)
            if src.isValid():
                rows.add(src.row())
        return self.delete_rows(rows)

    def delete_checked_rows(self) -> list[int]:
        """Delete rows whose checkbox column is checked."""
        return self.delete_rows(self.checked_rows())

    def append_row(self, values: list[Any]) -> int:
        """Append a row of values to the source model. Returns the new row index."""
        source = self._proxy.sourceModel()
        if source is None:
            raise RuntimeError("No model set")
        row = source.rowCount()
        items: list[QStandardItem] = []
        for c, v in enumerate(values):
            item = QStandardItem()
            if self._checkable_rows and c == self._check_column:
                item.setCheckable(True)
                item.setCheckState(Qt.Checked if v else Qt.Unchecked)
            else:
                item.setData(v, Qt.DisplayRole)
                item.setData(v, Qt.EditRole)
            items.append(item)
        source.appendRow(items)
        self._apply_flags_to_row(row)
        return row


# ---------------------------------------------------------------------------
# Optional helper: a delegate that renders an inline "delete" button.
# ---------------------------------------------------------------------------
class NoFocusDelegate(QStyledItemDelegate):
    """Delegate that suppresses the dotted focus rectangle on items."""
    def paint(self, painter, option, index):
        opt = QStyleOptionViewItem(option)
        opt.state &= ~QStyle.State_HasFocus
        super().paint(painter, opt, index)


class ActionDelegate(QStyledItemDelegate):
    """Render a clickable button inside a cell. Used to show inline actions
    (e.g. a "delete" button) at the end of every row.

    Use as::

        delegate = ActionDelegate("删除", parent=table)
        delegate.clicked.connect(lambda src_row: table.delete_rows([src_row]))
        table.setItemDelegateForColumn(action_col, delegate)
    """

    clicked = Signal(int)  # source row index

    def __init__(self, text: str = "删除", parent: QTableView | None = None) -> None:
        super().__init__(parent)
        self._text = text
        self._hover_row = -1
        if parent is not None:
            parent.setMouseTracking(True)
            parent.viewport().installEventFilter(self)

    def paint(self, painter: QPainter, option, index: QModelIndex) -> None:
        painter.save()
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, QColor("#e8f0fe"))
        elif self._hover_row == index.row():
            painter.fillRect(option.rect, QColor("#f1f3f4"))
        rect = option.rect.adjusted(6, 4, -6, -4)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(QPen(QColor("#ea4335"), 1))
        painter.setBrush(QColor("#fdecea") if self._hover_row == index.row()
                         else QColor("#ffffff"))
        painter.drawRoundedRect(rect, 6, 6)
        painter.setPen(QColor("#c5221f"))
        painter.drawText(rect, Qt.AlignCenter, self._text)
        painter.restore()

    def sizeHint(self, option, index: QModelIndex) -> QSize:
        return QSize(80, 30)

    def editorEvent(self, event, model, option, index) -> bool:
        if event.type() == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
            if option.rect.contains(event.position().toPoint()):
                view = self.parent()
                src_row = index.row()
                if isinstance(view, QTableView):
                    proxy = view.model()
                    if isinstance(proxy, QSortFilterProxyModel):
                        mapped = proxy.mapToSource(index)
                        if mapped.isValid():
                            src_row = mapped.row()
                self.clicked.emit(src_row)
                return True
        return super().editorEvent(event, model, option, index)

    def eventFilter(self, obj, event) -> bool:
        if event.type() == QEvent.MouseMove and isinstance(self.parent(), QTableView):
            idx = self.parent().indexAt(event.position().toPoint())
            row = idx.row() if idx.isValid() else -1
            if row != self._hover_row:
                self._hover_row = row
                self.parent().viewport().update()
        elif event.type() == QEvent.Leave:
            self._hover_row = -1
            if isinstance(self.parent(), QTableView):
                self.parent().viewport().update()
        return super().eventFilter(obj, event)
