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
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QStyle,
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
    """Proxy model that filters multiple columns by a set of allowed values."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._allowed: dict[int, set[str]] = {}

    def set_column_filter(self, column: int, allowed_values: set[str] | None) -> None:
        if allowed_values is None:
            self._allowed.pop(column, None)
        else:
            self._allowed[column] = set(allowed_values)
        self.invalidateFilter()

    def column_filter(self, column: int) -> set[str] | None:
        return self._allowed.get(column)

    def active_filter_columns(self) -> set[int]:
        return set(self._allowed.keys())

    def clear_filters(self) -> None:
        self._allowed.clear()
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


class _FilterPopup(QFrame):
    """Excel-style column filter popup with search + checkable values.

    Implemented as a :class:`QFrame` with the ``Qt.Popup`` window flag rather
    than as a :class:`QMenu`, because ``QMenu`` interferes with IME composition
    (typing Chinese / Japanese / Korean inside the search box did not work).
    """

    filterChanged = Signal(int, object)            # column, set or None
    sortRequested = Signal(int, Qt.SortOrder)

    def __init__(self, column: int, values: Iterable[str],
                 selected: set[str] | None, parent: QWidget | None = None) -> None:
        super().__init__(parent, Qt.Popup)
        self.setFrameShape(QFrame.NoFrame)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self._column = column
        self._all_values = sorted({str(v) for v in values},
                                  key=lambda s: (s == "", s.lower()))
        self._selected = set(self._all_values) if selected is None else set(selected)

        self.setStyleSheet(
            """
            QFrame {
                background: #ffffff;
                border: 1px solid #dadce0;
                border-radius: 8px;
            }
            QLineEdit {
                border: 1px solid #dadce0;
                border-radius: 6px;
                padding: 5px 8px;
                background: #f8f9fa;
            }
            QLineEdit:focus { border-color: #1a73e8; background: #ffffff; }
            QListWidget {
                border: 1px solid #e8eaed;
                border-radius: 6px;
                background: #ffffff;
                outline: 0;
            }
            QListWidget::item { padding: 4px 6px; }
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

        self._search = QLineEdit(self)
        self._search.setPlaceholderText("搜索...")
        self._search.setClearButtonEnabled(True)
        v.addWidget(self._search)

        self._select_all = QCheckBox("(全选)", self)
        self._select_all.setTristate(True)
        v.addWidget(self._select_all)

        self._list = _CheckListWidget(self)
        self._list.setSelectionMode(QAbstractItemView.NoSelection)
        self._list.setMinimumHeight(180)
        self._list.setMaximumHeight(280)
        self._list.setMinimumWidth(220)
        v.addWidget(self._list)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        self._clear_btn = QPushButton("清除筛选")
        self._cancel_btn = QPushButton("取消")
        self._ok_btn = QPushButton("确定")
        self._ok_btn.setObjectName("primary")
        btn_row.addWidget(self._clear_btn)
        btn_row.addWidget(self._cancel_btn)
        btn_row.addWidget(self._ok_btn)
        v.addLayout(btn_row)

        self._populate_list("")

        self._search.textChanged.connect(self._populate_list)
        self._select_all.clicked.connect(self._on_select_all_clicked)
        self._list.itemChanged.connect(self._on_item_changed)
        self._sort_asc.clicked.connect(lambda: self._emit_sort(Qt.AscendingOrder))
        self._sort_desc.clicked.connect(lambda: self._emit_sort(Qt.DescendingOrder))
        self._clear_btn.clicked.connect(self._on_clear)
        self._ok_btn.clicked.connect(self._on_ok)
        self._cancel_btn.clicked.connect(self.close)

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
        state = (Qt.Checked
                 if self._select_all.checkState() != Qt.Unchecked
                 else Qt.Unchecked)
        self._select_all.setCheckState(state)
        self._list.blockSignals(True)
        for i in range(self._list.count()):
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

    def _emit_sort(self, order: Qt.SortOrder) -> None:
        self.sortRequested.emit(self._column, order)
        self.close()

    def _on_clear(self) -> None:
        self.filterChanged.emit(self._column, None)
        self.close()

    def _on_ok(self) -> None:
        if not self._selected:
            self.filterChanged.emit(self._column, set())
        elif self._selected == set(self._all_values):
            self.filterChanged.emit(self._column, None)
        else:
            self.filterChanged.emit(self._column, set(self._selected))
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
        self._search.setFocus()


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
            if section >= 0 and section not in self._skip_filter_columns:
                icon_rect = self._icon_rect(section)
                # Only react to the icon click if the icon is currently visible.
                visible = (section in self._active_columns
                           or section == self._hover_section)
                if visible and icon_rect.contains(event.position().toPoint()):
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

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._proxy = _MultiColumnFilterProxy(self)
        super().setModel(self._proxy)

        self._header = _FilterHeaderView(Qt.Horizontal, self)
        self.setHorizontalHeader(self._header)
        self._header.filterClicked.connect(self._show_filter_menu)

        self.setSortingEnabled(True)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setShowGrid(False)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(30)
        self.setMouseTracking(True)

        self._checkable_rows = False
        self._check_column = 0
        self._editable_columns: set[int] | None = None  # None = none, set = whitelist
        self._all_editable = False

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
        popup = _FilterPopup(column, values, self._proxy.column_filter(column), self)
        popup.filterChanged.connect(self._on_filter_changed)
        popup.sortRequested.connect(self._on_sort_requested)
        popup.show_at(global_pos)

    def _on_filter_changed(self, column: int, allowed: set[str] | None) -> None:
        self._proxy.set_column_filter(column, allowed)
        self._header.set_active(column, allowed is not None)

    def _on_sort_requested(self, column: int, order: Qt.SortOrder) -> None:
        self.sortByColumn(column, order)

    # ------------------------------------------------------------------
    # checkable rows
    # ------------------------------------------------------------------
    def set_checkable_rows(self, enabled: bool, column: int = 0) -> None:
        """Show a checkbox in ``column`` of every row.

        The check column is excluded from the filter UI and from editability.
        """
        self._checkable_rows = enabled
        self._check_column = column
        if enabled:
            self._header.set_filter_skipped(column, True)
            self.setColumnWidth(column, 36)
        else:
            self._header.set_filter_skipped(column, False)
        self._apply_flags_to_all()

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
                if item.checkState() not in (Qt.Checked, Qt.Unchecked):
                    item.setCheckState(Qt.Unchecked)
                item.setData("", Qt.DisplayRole)
            elif self._column_is_editable(c):
                flags |= Qt.ItemIsEditable
            item.setFlags(flags)

    def _on_source_item_changed(self, item: QStandardItem) -> None:
        if (self._checkable_rows and item.column() == self._check_column):
            checked = item.checkState() == Qt.Checked
            self.rowChecked.emit(item.row(), checked)
            return
        if self._column_is_editable(item.column()):
            self.cellEdited.emit(item.row(), item.column(), item.data(Qt.EditRole))

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
