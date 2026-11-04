from __future__ import annotations

from typing import Any, Iterable, Sequence
import re

from PySide6.QtCore import (
    QDate,
    QEvent,
    QModelIndex,
    QObject,
    QPoint,
    QRect,
    QSize,
    QSortFilterProxyModel,
    Qt,
    QTimer,
    Signal,
)
from PySide6.QtGui import (
    QColor,
    QIcon,
    QIntValidator,
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
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QSizePolicy,
    QStyle,
    QStyleOptionButton,
    QStyleOptionViewItem,
    QStyledItemDelegate,
    QTableView,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QWidgetAction,
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


# --------------------------------------------------------------------------
# Every user-visible string lives here so callers can reword / localise the
# table without touching the source:  ``MyTable(texts={"ok": "Apply"})``.
# --------------------------------------------------------------------------
DEFAULT_TEXTS: dict[str, object] = {
    # ---- filter popup: shared ------------------------------------------
    "sort_asc":             "\u2191 升序",
    "sort_desc":            "\u2193 降序",
    "select_all":           "全选",
    "search_placeholder":   "搜索...",
    "invert":               "反选",
    "reset":                "重置",
    "cancel":               "取消",
    "ok":                   "确定",
    "hover_only":           "仅筛此项",
    "hover_only_tip":       "把筛选替换为只看这一项",
    "blank":                "(空白)",
    "reset_tip_text":       "取消勾选所有可见项",
    # ---- filter popup: numeric -----------------------------------------
    "numeric_toggle":       "按数字比较",
    "op_eq":                "等于 =",
    "op_ne":                "不等于 ≠",
    "op_gt":                "大于 >",
    "op_ge":                "大于等于 ≥",
    "op_lt":                "小于 <",
    "op_le":                "小于等于 ≤",
    "add_condition":        "+ 添加条件",
    "add_condition_tip":    "再增加一个比较条件(AND 关系)",
    "remove_condition_tip": "删除该条件",
    "reset_tip_numeric":    "只保留一条“等于 0”的条件",
    # ---- filter popup: date --------------------------------------------
    "date_toggle":          "按日期范围",
    "date_hint":            "点一天设为起始日，再点一天设为结束日；顶部「年」「月」可直接下拉跳转；“全部”= 不限",
    "ignore_sep":           "忽视分隔符匹配",
    "ignore_sep_tip":       "勾选后 2025/11/11、2025-11-11、2025.11.11 视为同一天",
    "reset_tip_date":       "清空日期范围，回到“不限”",
    # ---- date picker ----------------------------------------------------
    "preset_7d":            "近 7 天",
    "preset_30d":           "近 30 天",
    "preset_month":         "本月",
    "preset_year":          "今年",
    "preset_all":           "全部",
    "prev_month_tip":       "上个月",
    "next_month_tip":       "下个月",
    "pick_year_tip":        "选择年份",
    "pick_month_tip":       "选择月份",
    "today":                "今天",
    "today_tip":            "跳到今天",
    "year_placeholder":     "输入年份",
    "month_placeholder":    "输入月份",
    "jump":                 "跳转",
    "year_hint":            "输入年份后回车跳转（{min}–{max}）",
    "month_hint":           "输入月份后回车跳转（1–12）",
    "year_data_hint":       "；数据年份 {lo}–{hi}",
    "unbounded":            "不限",
    "no_range":             "未选择（不限）",
    "year_suffix":          " 年",
    "month_suffix":         " 月",
    "date_format":          "yyyy-MM-dd",
    "weekdays":             ("一", "二", "三", "四", "五", "六", "日"),
    # ---- table shell ----------------------------------------------------
    "delete_selected":      "删除选中行 ({n})",
    "delete_checked":       "删除已勾选行 ({n})",
    "check_all":            "全选",
    "uncheck_all":          "取消全选",
    "clear_filters":        "清空筛选",
}

# Order of the one-click date presets; each key maps to a label in
# :data:`DEFAULT_TEXTS` and to a computation in ``_apply_preset``.
PRESET_KEYS: tuple[str, ...] = (
    "preset_7d", "preset_30d", "preset_month", "preset_year", "preset_all",
)

# Default geometry of every sub-widget.  Overridable through
# ``MyTable(metrics={...})``.
DEFAULT_METRICS: dict[str, int] = {
    "row_height":         30,
    "table_font_size":    13,
    "header_font_size":   13,
    "header_pad_left":    10,
    "header_pad_right":   42,
    "min_section":        80,
    "default_section":    140,
    "filter_icon_size":   16,
    "filter_margin":      6,
    "sort_w":             8,
    "sort_h":             14,
    "sort_gap":           6,
    "sort_text_gap":      6,
    "check_box_size":     14,
    "check_box_margin":   8,
    "check_column_width": 56,
    "col_extra":          30,
    "col_min":            120,
    "cal_cell_w":         34,
    "cal_cell_h":         28,
    "cal_header_h":       24,
    "year_span":          10,
    "year_min":           1900,
    "year_max":           2999,
    "year_edit_width":    84,
    "year_edit_height":   24,
    "choice_min_width":   58,
    "list_min_height":    180,
    "list_max_height":    280,
    "list_min_width":     220,
    "action_radius":      6,
    "action_margin_x":    6,
    "action_margin_y":    4,
    "action_min_width":   80,
    "action_min_height":  30,
}


# Default palette of the table shell.  Same convention as the other widgets:
# a flat dict merged through ``style=`` / :meth:`MyTable.set_style`.
DEFAULT_STYLE: dict[str, object] = {
    "background":            "#ffffff",
    "alternate_background":  "#f8f9fa",
    "text_color":            "#202124",
    "gridline_color":        "#e8eaed",
    "border_color":          "#dadce0",
    "border_radius":         8,
    "selection_bg":          "#e8f0fe",
    "selection_text_color":  "#1a73e8",
    "item_hover_bg":         "#f1f3f4",
    "header_background":     "#f8f9fa",
    "header_text_color":     "#3c4043",
    "header_hover_bg":       "#f1f3f4",
    "header_pressed_bg":     "#e8eaed",
    "header_separator_color": "#e8eaed",
    "header_border_color":   "#dadce0",
    "scrollbar_handle":      "#c4c7c5",
    "scrollbar_handle_hover": "#9aa0a6",
}


# Explicit date formats accepted by :func:`_parse_date`, tried in order
# after the ISO parser. ``Qt.ISODate`` ("yyyy-MM-dd" plus ISO datetimes)
# is always attempted first.
_DATE_PARSE_FORMATS = (
    "yyyy/M/d", "yyyy-M-d", "yyyy.M.d",
    "d/M/yyyy", "d-M-yyyy", "d.M.yyyy",
    "yyyyMMdd",
)


def _parse_date(text: str, ignore_separators: bool = False) -> QDate | None:
    """Best-effort parse of a cell's display text into a :class:`QDate`.

    Understands ISO dates ("2024-03-01"), ISO datetimes ("2024-03-01T10:30"
    / "2024-03-01 10:30") and a handful of common explicit formats. Returns
    ``None`` when the text is not a recognisable date.

    When *ignore_separators* is true, ``/`` ``-`` ``.`` and spaces are treated
    as equivalent, so ``2025/11/11`` and ``2025-11-11`` parse to the same day.
    """
    raw = (text or "").strip()
    if not raw:
        return None
    candidates = [raw]
    if ignore_separators:
        head = raw.replace("T", " ").split(" ", 1)[0]
        collapsed = re.sub(r"[./\-\s]+", "-", head).strip("-")
        if collapsed and collapsed not in candidates:
            candidates.append(collapsed)
        digits = re.sub(r"\D", "", head)
        if len(digits) >= 8:
            ymd = digits[:8]
            if ymd not in candidates:
                candidates.append(ymd)
    parsed = QDate()
    for cand in candidates:
        parsed = QDate.fromString(cand, Qt.ISODate)
        if not parsed.isValid():
            head = cand.replace("T", " ").split(" ", 1)[0]
            if head != cand:
                parsed = QDate.fromString(head, Qt.ISODate)
        for fmt in _DATE_PARSE_FORMATS:
            if parsed.isValid():
                break
            parsed = QDate.fromString(cand, fmt)
        if parsed.isValid():
            return parsed
    return None


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
        # column -> (start, end) inclusive; either bound may be None (open)
        self._dates: dict[int, tuple[QDate | None, QDate | None]] = {}
        # column -> ignore date separators when matching cells (default on)
        self._date_ignore_sep: dict[int, bool] = {}

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

    # ---- date-range filters ----------------------------------------------
    def set_column_date_filter(
            self, column: int,
            date_range: tuple[QDate | None, QDate | None] | None) -> None:
        """Replace the date-range filter for *column*.

        ``date_range`` is an inclusive ``(start, end)``; either bound may
        be ``None`` (open-ended). Passing ``None`` — or a range with both
        bounds open — clears the filter. Rows whose cell cannot be parsed
        as a date are excluded, mirroring the numeric-filter behaviour.
        """
        empty = (date_range is None
                 or (date_range[0] is None and date_range[1] is None))
        if empty:
            changed = self._dates.pop(column, None) is not None
            self._date_ignore_sep.pop(column, None)
            if changed:
                self.invalidateFilter()
        else:
            self._dates[column] = (date_range[0], date_range[1])
            self.invalidateFilter()

    def column_date_filter(
            self, column: int) -> tuple[QDate | None, QDate | None] | None:
        """Return a copy of the date range for *column*, or ``None``."""
        rng = self._dates.get(column)
        return (rng[0], rng[1]) if rng is not None else None

    def set_column_date_ignore_separators(self, column: int, enabled: bool) -> None:
        prev = self._date_ignore_sep.get(column, True)
        self._date_ignore_sep[column] = bool(enabled)
        if prev != bool(enabled) and column in self._dates:
            self.invalidateFilter()

    def column_date_ignore_separators(self, column: int) -> bool:
        return self._date_ignore_sep.get(column, True)

    def clear_column_date_filter(self, column: int) -> None:
        self._date_ignore_sep.pop(column, None)
        if self._dates.pop(column, None) is not None:
            self.invalidateFilter()

    # ---- shared ----------------------------------------------------------
    def active_filter_columns(self) -> set[int]:
        return set(self._allowed.keys()) | set(self._numeric.keys()) \
            | set(self._dates.keys())

    def clear_filters(self) -> None:
        self._allowed.clear()
        self._numeric.clear()
        self._dates.clear()
        self._date_ignore_sep.clear()
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
        for column, (start, end) in self._dates.items():
            idx = model.index(source_row, column, source_parent)
            raw = "" if not idx.isValid() else idx.data(Qt.DisplayRole)
            ignore = self._date_ignore_sep.get(column, True)
            d = _parse_date(str(raw) if raw is not None else "", ignore)
            if d is None:
                return False       # unparseable cell → exclude
            jd = d.toJulianDay()
            if start is not None and jd < start.toJulianDay():
                return False
            if end is not None and jd > end.toJulianDay():
                return False
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

    OP_KEYS: tuple[tuple[str, str], ...] = (
        ("op_eq", "="), ("op_ne", "!="), ("op_gt", ">"),
        ("op_ge", ">="), ("op_lt", "<"), ("op_le", "<="),
    )

    def __init__(self, op: str = "=", value: float = 0.0,
                 parent: QWidget | None = None, *,
                 texts: dict | None = None) -> None:
        super().__init__(parent)
        t = {**DEFAULT_TEXTS, **(texts or {})}
        self._op = QComboBox(self)
        for key, data in self.OP_KEYS:
            self._op.addItem(str(t[key]), data)
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
        self._remove.setToolTip(str(t["remove_condition_tip"]))
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

    def set_condition(self, op: str, value: float) -> None:
        """Overwrite operator + value (used by the popup's 重置 button)."""
        idx = self._op.findData(op)
        self._op.setCurrentIndex(idx if idx >= 0 else 0)
        self._value.setValue(float(value))


class _MonthGrid(QWidget):
    """Self-drawn month grid: weekday header + 6 week rows of day cells.

    ``QCalendarWidget`` keeps both painting *and* hit-testing inside its
    private ``QCalendarView``. Drawing the range band required overriding
    ``paintCell()`` while skipping ``super()``; day clicks were then reported
    to stop reaching the widget inside the filter popup (only keyboard
    navigation still moved the current cell). Drawing the grid here puts
    rendering and hit-testing into the very same coordinates, so a click
    always selects the day the user sees.

    Keyboard: ←/→ ±1 天, ↑/↓ ±1 周, PageUp/PageDown ±1 月, Enter/Space 选中。

    Signals:
        dayClicked(QDate): a day cell was clicked or confirmed with Enter.
    """

    dayClicked = Signal(QDate)

    COLS = 7
    ROWS = 6
    CELL_W = 34
    CELL_H = 28
    HEADER_H = 24
    WEEKDAYS = ("一", "二", "三", "四", "五", "六", "日")

    RANGE_BG = QColor("#e8f0fe")
    RANGE_FG = QColor("#174ea6")
    EDGE_BG = QColor("#1a73e8")
    EDGE_FG = QColor("#ffffff")
    MUTED_FG = QColor("#bdc1c6")
    TODAY_FG = QColor("#1a73e8")
    TEXT_FG = QColor("#202124")
    HEADER_FG = QColor("#5f6368")
    HOVER_BG = QColor("#f1f3f4")

    def __init__(self, parent: QWidget | None = None, *,
                 cell_w: int | None = None,
                 cell_h: int | None = None,
                 header_h: int | None = None,
                 cols: int | None = None,
                 rows: int | None = None,
                 weekdays: Sequence[str] | None = None,
                 colors: dict | None = None) -> None:
        """Every size / label / colour below can be overridden per instance.

        Unspecified values fall back to the class-level defaults, so existing
        call sites keep their exact look.
        """
        super().__init__(parent)
        # Instance attributes shadow the class constants used by the
        # painting / hit-testing code.
        if cell_w:
            self.CELL_W = int(cell_w)
        if cell_h:
            self.CELL_H = int(cell_h)
        if header_h:
            self.HEADER_H = int(header_h)
        if cols:
            self.COLS = int(cols)
        if rows:
            self.ROWS = int(rows)
        if weekdays:
            self.WEEKDAYS = tuple(weekdays)
        for key, value in (colors or {}).items():
            if hasattr(self, key):
                setattr(self, key, QColor(value))
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self._page = QDate.currentDate()
        self._cursor = QDate.currentDate()
        self._lo: QDate | None = None
        self._hi: QDate | None = None
        self._hover: QDate | None = None

    # ---- page / geometry -------------------------------------------------
    def sizeHint(self) -> QSize:
        return QSize(self.COLS * self.CELL_W,
                     self.HEADER_H + self.ROWS * self.CELL_H)

    def minimumSizeHint(self) -> QSize:
        return self.sizeHint()

    def page(self) -> tuple[int, int]:
        return (self._page.year(), self._page.month())

    def set_page(self, year: int, month: int) -> None:
        self._page = QDate(int(year), int(month), 1)
        self.update()

    def cursor_date(self) -> QDate:
        return QDate(self._cursor)

    def set_cursor_date(self, day: QDate) -> None:
        self._cursor = QDate(day)

    def set_highlight(self, start: QDate | None,
                      end: QDate | None) -> None:
        self._lo = QDate(start) if start is not None else None
        self._hi = QDate(end) if end is not None else None
        self.update()

    def _x_offset(self) -> int:
        return max(0, (self.width() - self.COLS * self.CELL_W) // 2)

    def _grid_start(self) -> QDate:
        first = QDate(self._page.year(), self._page.month(), 1)
        return first.addDays(-(first.dayOfWeek() - 1))   # 周一为一周之始

    def date_at(self, pos: QPoint) -> QDate | None:
        """Return the date under *pos* (widget-local), or ``None``."""
        if pos.y() < self.HEADER_H:
            return None
        col = (pos.x() - self._x_offset()) // self.CELL_W
        row = (pos.y() - self.HEADER_H) // self.CELL_H
        if not (0 <= col < self.COLS and 0 <= row < self.ROWS):
            return None
        return self._grid_start().addDays(row * self.COLS + col)

    # ---- interaction -----------------------------------------------------
    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            day = self.date_at(event.position().toPoint())
            if day is not None:
                self._cursor = day
                self.setFocus(Qt.MouseFocusReason)
                self.dayClicked.emit(day)
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        day = self.date_at(event.position().toPoint())
        if day != self._hover:
            self._hover = day
            self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event) -> None:
        if self._hover is not None:
            self._hover = None
            self.update()
        super().leaveEvent(event)

    def keyPressEvent(self, event) -> None:
        key = event.key()
        step = {Qt.Key_Left: -1, Qt.Key_Right: 1,
                Qt.Key_Up: -7, Qt.Key_Down: 7}.get(key)
        if step is not None:
            self._move_cursor(self._cursor.addDays(step))
            return
        if key in (Qt.Key_PageUp, Qt.Key_PageDown):
            self._move_cursor(
                self._cursor.addMonths(-1 if key == Qt.Key_PageUp else 1))
            return
        if key in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            self.dayClicked.emit(QDate(self._cursor))
            return
        super().keyPressEvent(event)

    def _move_cursor(self, day: QDate) -> None:
        self._cursor = QDate(day)
        if (day.year(), day.month()) != self.page():
            self.set_page(day.year(), day.month())
        self.update()

    # ---- painting --------------------------------------------------------
    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.fillRect(self.rect(), QColor("#ffffff"))

        base = self.font()
        base.setBold(False)
        painter.setFont(base)
        painter.setPen(self.HEADER_FG)
        x_off = self._x_offset()
        for col, name in enumerate(self.WEEKDAYS):
            painter.drawText(
                QRect(x_off + col * self.CELL_W, 0,
                      self.CELL_W, self.HEADER_H),
                Qt.AlignCenter, name)

        start = self._grid_start()
        today = QDate.currentDate()
        lo, hi = self._lo, self._hi
        top = hi if hi is not None else lo
        for index in range(self.ROWS * self.COLS):
            day = start.addDays(index)
            row, col = divmod(index, self.COLS)
            rect = QRect(x_off + col * self.CELL_W,
                         self.HEADER_H + row * self.CELL_H,
                         self.CELL_W, self.CELL_H)
            in_range = lo is not None and lo <= day <= top
            is_edge = lo is not None and (day == lo or day == hi)
            if is_edge:
                painter.setPen(Qt.NoPen)
                painter.setBrush(self.EDGE_BG)
                painter.drawRoundedRect(rect.adjusted(2, 1, -2, -1), 8, 8)
                painter.setBrush(Qt.NoBrush)
            elif in_range:
                painter.fillRect(rect, self.RANGE_BG)
            elif day == self._hover:
                painter.fillRect(rect, self.HOVER_BG)

            if is_edge:
                color = self.EDGE_FG
            elif in_range:
                color = self.RANGE_FG
            elif day.month() != self._page.month():
                color = self.MUTED_FG
            elif day == today:
                color = self.TODAY_FG
            else:
                color = self.TEXT_FG
            font = self.font()
            font.setBold(is_edge or day == today)
            painter.setFont(font)
            painter.setPen(color)
            painter.drawText(rect, Qt.AlignCenter, str(day.day()))
        painter.end()


class _ChoiceGrid(QWidget):
    """A compact grid of numeric choices embedded in a ``QMenu``.

    Modern date pickers do not scroll a 20-item year list: they show a small
    grid so every option is a single click away. ``picked`` reports the chosen
    value and the owning menu closes itself. ``scrolled`` reports mouse-wheel
    steps (positive = wheel down, i.e. towards larger values) so the year
    panel can lazily extend its range instead of stopping at a fixed window.
    """

    picked = Signal(int)
    scrolled = Signal(int)

    def __init__(self, columns: int, values: Sequence[int], current: int,
                 suffix: str = "", parent: QWidget | None = None, *,
                 min_width: int = 58) -> None:
        super().__init__(parent)
        self._suffix = suffix
        self._min_width = int(min_width)
        self._cells: list[QPushButton] = []
        grid = QGridLayout(self)
        grid.setContentsMargins(4, 2, 4, 4)
        grid.setSpacing(3)
        for index, value in enumerate(values):
            cell = QPushButton(self)
            cell.setObjectName("ChoiceCell")
            cell.setCheckable(True)
            cell.setCursor(Qt.PointingHandCursor)
            cell.setMinimumWidth(self._min_width)
            cell.clicked.connect(
                lambda _=False, c=cell: self._pick(int(c.property("choiceValue")))
            )
            grid.addWidget(cell, index // columns, index % columns)
            self._cells.append(cell)
        self.set_values(values, current)

    def set_values(self, values: Sequence[int], current: int) -> None:
        """Update the visible choices in place (grid size stays the same)."""
        values = list(values)
        for index, cell in enumerate(self._cells):
            if index >= len(values):
                cell.hide()
                continue
            value = int(values[index])
            cell.setProperty("choiceValue", value)
            cell.setText(f"{value}{self._suffix}")
            cell.setChecked(value == current)
            cell.show()

    def wheelEvent(self, event) -> None:
        delta = event.angleDelta().y()
        if delta:
            steps = int(-delta / 120) or (-1 if delta > 0 else 1)
            self.scrolled.emit(steps)
            event.accept()
            return
        super().wheelEvent(event)

    def _pick(self, value: int) -> None:
        self.picked.emit(int(value))
        menu = self.window()
        if isinstance(menu, QMenu):
            menu.close()


class _YearEdit(QLineEdit):
    """Numeric box inside the year / month panel: focus selects all so typing
    replaces the pre-filled value instead of appending to it."""

    def focusInEvent(self, event) -> None:
        super().focusInEvent(event)
        # 预填的是当前年份，不自动全选的话新数字会被 validator 挡掉。
        self.selectAll()


class _DateRangePicker(QWidget):
    """Inline calendar range picker for the date filter.

    Modern range UX instead of two cramped checkbox+``QDateEdit`` rows:

    * a live summary pill (``2024-03-01 → 2024-03-31``, or ``不限`` on an
      open side),
    * one-click presets (近 7 天 / 近 30 天 / 本月 / 今年 / 全部),
    * a month calendar where the first click sets the start day and the
      second click sets the end day (clicking the same day twice selects
      exactly that day). The selected span is highlighted in place,
    * year / month dropdowns that open a compact grid (year = current page
      year ± 10, month = 4×3) instead of a long scrolling list; the year
      panel also accepts a typed year, so any date is reachable.

    Either bound may be missing, which means "no bound on that side" —
    the same open-range semantics the proxy implements.
    """

    def __init__(self, suggested_start: QDate, suggested_end: QDate,
                 parent: QWidget | None = None, *,
                 texts: dict | None = None,
                 metrics: dict | None = None) -> None:
        super().__init__(parent)
        self._texts: dict = {**DEFAULT_TEXTS, **(texts or {})}
        self._metrics: dict = {**DEFAULT_METRICS, **(metrics or {})}
        t, m = self._texts, self._metrics
        self._start: QDate | None = None
        self._end: QDate | None = None
        self._anchor: QDate | None = None

        # 年份面板固定为「当前显示年 ± year_span」的网格，随翻页自动跟随；
        # 顶部还有输入框可键入任意年份，所以不设硬边界。
        today = QDate.currentDate()
        self._year_span = int(m["year_span"])
        self._data_span = (
            suggested_start if suggested_start.isValid() else None,
            suggested_end if suggested_end.isValid() else None,
        )

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)

        # -- live summary --------------------------------------------------
        self._summary = QLabel(self)
        self._summary.setObjectName("DateSummary")
        lay.addWidget(self._summary)

        # -- presets -------------------------------------------------------
        chips = QHBoxLayout()
        chips.setSpacing(4)
        for key in PRESET_KEYS:
            name = str(t[key])
            chip = QPushButton(name, self)
            chip.setObjectName("DateChip")
            chip.setCursor(Qt.PointingHandCursor)
            chip.clicked.connect(lambda _=False, k=key: self._apply_preset(k))
            chips.addWidget(chip)
        chips.addStretch(1)
        lay.addLayout(chips)

        # -- month header --------------------------------------------------
        # “年”“月”都是可直接选的下拉菜单，不用一个月一个月地翻。
        header = QHBoxLayout()
        header.setSpacing(2)
        self._prev = QToolButton(self)
        self._prev.setObjectName("CalNav")
        self._prev.setText("\u2039")
        self._prev.setToolTip(str(t["prev_month_tip"]))
        self._next = QToolButton(self)
        self._next.setObjectName("CalNav")
        self._next.setText("\u203a")
        self._next.setToolTip(str(t["next_month_tip"]))

        self._year_btn = QToolButton(self)
        self._year_btn.setObjectName("CalMonth")
        self._year_btn.setCursor(Qt.PointingHandCursor)
        self._year_btn.setToolTip(str(t["pick_year_tip"]))
        self._year_btn.setPopupMode(QToolButton.InstantPopup)
        self._year_menu = QMenu(self._year_btn)
        self._year_btn.setMenu(self._year_menu)
        self._year_menu.aboutToShow.connect(self._fill_year_menu)
        # 菜单不管以哪种方式关闭（选中 / 空白处 / Esc），按钮不能停在“按下”外观。
        self._year_menu.aboutToHide.connect(
            lambda: self._year_btn.setDown(False))

        self._month_btn = QToolButton(self)
        self._month_btn.setObjectName("CalMonth")
        self._month_btn.setCursor(Qt.PointingHandCursor)
        self._month_btn.setToolTip(str(t["pick_month_tip"]))
        self._month_btn.setPopupMode(QToolButton.InstantPopup)
        self._month_menu = QMenu(self._month_btn)
        self._month_btn.setMenu(self._month_menu)
        self._month_menu.aboutToShow.connect(self._fill_month_menu)
        self._month_menu.aboutToHide.connect(
            lambda: self._month_btn.setDown(False))

        self._today = QToolButton(self)
        self._today.setObjectName("CalToday")
        self._today.setText(str(t["today"]))
        self._today.setToolTip(str(t["today_tip"]))
        header.addWidget(self._prev)
        header.addStretch(1)
        header.addWidget(self._year_btn)
        header.addWidget(self._month_btn)
        header.addStretch(1)
        header.addWidget(self._next)
        header.addSpacing(6)
        header.addWidget(self._today)
        lay.addLayout(header)

        # -- day grid ------------------------------------------------------
        # 自绘网格：渲染与命中测试同一套坐标，点哪天就是哪天。
        self._grid = _MonthGrid(
            self,
            cell_w=m["cal_cell_w"],
            cell_h=m["cal_cell_h"],
            header_h=m["cal_header_h"],
            weekdays=t["weekdays"],
        )
        self._grid.set_page(today.year(), today.month())
        lay.addWidget(self._grid, 0, Qt.AlignHCenter)

        self._prev.clicked.connect(lambda: self._step_month(-1))
        self._next.clicked.connect(lambda: self._step_month(1))
        self._today.clicked.connect(self._go_today)
        self._grid.dayClicked.connect(self._on_day_clicked)

        self._sync_month_label()
        self._sync_summary()

    # ---- public API (used by _FilterPopup) -------------------------------
    def set_range(self, start: QDate | None, end: QDate | None) -> None:
        """Seed the picker from a prior ``(start, end)`` filter."""
        self._anchor = None
        self._start = QDate(start) if start is not None else None
        self._end = QDate(end) if end is not None else None
        if self._start is not None:
            self._goto(self._start.year(), self._start.month())
            self._grid.set_cursor_date(self._start)
        self._paint_range()
        self._sync_summary()

    def range(self) -> tuple[QDate | None, QDate | None]:
        """Return ``(start, end)``; ``None`` on a side = open bound."""
        return (self._start, self._end)

    def focus_start(self) -> None:
        self._grid.setFocus(Qt.OtherFocusReason)

    # ---- year / month menu -----------------------------------------------
    def _fill_year_menu(self) -> None:
        """年份面板：可编辑输入框 + 「当前年 ± 10」的 3×7 网格。"""
        t, m = self._texts, self._metrics
        menu = self._year_menu
        menu.clear()
        year, _month = self._grid.page()

        panel = QWidget(menu)
        box = QVBoxLayout(panel)
        box.setContentsMargins(4, 4, 4, 0)
        box.setSpacing(2)

        row = QHBoxLayout()
        row.setSpacing(4)
        edit = _YearEdit(panel)
        edit.setObjectName("YearEdit")
        edit.setPlaceholderText(str(t["year_placeholder"]))
        edit.setFixedWidth(int(m["year_edit_width"]))
        edit.setFixedHeight(int(m["year_edit_height"]))
        edit.setValidator(QIntValidator(int(m["year_min"]),
                                        int(m["year_max"]), edit))
        edit.setText(str(year))
        hint = str(t["year_hint"]).format(min=m["year_min"], max=m["year_max"])
        lo_d, hi_d = self._data_span
        if lo_d is not None and hi_d is not None:
            hint += str(t["year_data_hint"]).format(lo=lo_d.year(), hi=hi_d.year())
        edit.setToolTip(hint)
        jump = QPushButton(str(t["jump"]), panel)
        jump.setObjectName("YearJump")
        jump.setCursor(Qt.PointingHandCursor)
        jump.setFixedHeight(int(m["year_edit_height"]))
        row.addWidget(edit)
        row.addWidget(jump)
        row.addStretch(1)
        box.addLayout(row)

        span = self._year_span
        start = year - span

        grid = _ChoiceGrid(
            3, range(start, start + 2 * span + 1),
            year, str(t["year_suffix"]), panel,
            min_width=m["choice_min_width"])
        box.addWidget(grid)

        # 滚轮向上/向下滚动时整格年份窗口逐年平移（2016→2015→2014…／
        # 2036→2037→2038…），而不是被固定的 ±span 窗口卡住。
        def shift(steps: int) -> None:
            nonlocal start
            lo = max(int(m["year_min"]), start + steps)
            hi = lo + 2 * span
            if lo == start or hi > int(m["year_max"]):
                return
            start = lo
            grid.set_values(range(start, start + 2 * span + 1), year)

        grid.scrolled.connect(shift)

        action = QWidgetAction(menu)
        action.setDefaultWidget(panel)
        menu.addAction(action)

        def submit() -> None:
            text = edit.text().strip()
            if not text.isdigit():
                return
            value = int(text)
            if int(m["year_min"]) <= value <= int(m["year_max"]):
                self._goto(value, self._grid.page()[1])
                menu.close()

        edit.returnPressed.connect(submit)
        jump.clicked.connect(submit)
        grid.picked.connect(
            lambda y: self._goto(y, self._grid.page()[1]))
        # 菜单弹出后直接可键入年份，不用再点一次输入框。
        QTimer.singleShot(0, edit.setFocus)

    def _fill_month_menu(self) -> None:
        """月份面板：可编辑输入框 + 4×3 网格，点选和键入都能跳转。"""
        t, m = self._texts, self._metrics
        menu = self._month_menu
        menu.clear()
        year, month = self._grid.page()

        panel = QWidget(menu)
        box = QVBoxLayout(panel)
        box.setContentsMargins(4, 4, 4, 4)
        box.setSpacing(2)

        row = QHBoxLayout()
        row.setSpacing(4)
        edit = _YearEdit(panel)
        edit.setObjectName("YearEdit")
        edit.setPlaceholderText(str(t["month_placeholder"]))
        edit.setFixedWidth(int(m["year_edit_width"]))
        edit.setFixedHeight(int(m["year_edit_height"]))
        edit.setValidator(QIntValidator(1, 12, edit))
        edit.setText(str(month))
        edit.setToolTip(str(t["month_hint"]))
        jump = QPushButton(str(t["jump"]), panel)
        jump.setObjectName("YearJump")
        jump.setCursor(Qt.PointingHandCursor)
        jump.setFixedHeight(int(m["year_edit_height"]))
        row.addWidget(edit)
        row.addWidget(jump)
        row.addStretch(1)
        box.addLayout(row)

        grid = _ChoiceGrid(4, range(1, 13), month, str(t["month_suffix"]), panel,
                           min_width=m["choice_min_width"])
        box.addWidget(grid)

        action = QWidgetAction(menu)
        action.setDefaultWidget(panel)
        menu.addAction(action)

        def submit() -> None:
            text = edit.text().strip()
            if text.isdigit() and 1 <= int(text) <= 12:
                self._goto(year, int(text))
                menu.close()

        edit.returnPressed.connect(submit)
        jump.clicked.connect(submit)
        grid.picked.connect(lambda picked: self._goto(year, picked))
        # 菜单弹出后直接可键入月份，不用再点一次输入框。
        QTimer.singleShot(0, edit.setFocus)

    def _goto(self, year: int, month: int) -> None:
        # 不再限制在固定年份窗口内：输入框可以跳到任意年份。
        year = max(1, min(9999, int(year)))
        month = max(1, min(12, int(month)))
        self._grid.set_page(year, int(month))
        # 翻页后把键盘光标带进新月份，否则按 ←/→/Enter 会突然跳回旧月份。
        cursor = self._grid.cursor_date()
        if (cursor.year(), cursor.month()) != (year, int(month)):
            day = min(cursor.day(), QDate(year, int(month), 1).daysInMonth())
            self._grid.set_cursor_date(QDate(year, int(month), day))
        self._sync_month_label()

    def _step_month(self, delta: int) -> None:
        year, month = self._grid.page()
        nxt = QDate(year, month, 1).addMonths(delta)
        self._goto(nxt.year(), nxt.month())

    # ---- presets ---------------------------------------------------------
    def _apply_preset(self, key: str) -> None:
        today = QDate.currentDate()
        if key == "preset_7d":
            start, end = today.addDays(-6), today
        elif key == "preset_30d":
            start, end = today.addDays(-29), today
        elif key == "preset_month":
            start = QDate(today.year(), today.month(), 1)
            end = start.addMonths(1).addDays(-1)
        elif key == "preset_year":
            start = QDate(today.year(), 1, 1)
            end = QDate(today.year(), 12, 31)
        else:  # preset_all
            start = end = None
        self._anchor = None
        self._start, self._end = start, end
        if start is not None:
            self._goto(start.year(), start.month())
            self._grid.set_cursor_date(start)
        self._paint_range()
        self._sync_summary()

    def _go_today(self) -> None:
        today = QDate.currentDate()
        self._goto(today.year(), today.month())
        self._grid.set_cursor_date(today)
        self._grid.setFocus(Qt.MouseFocusReason)

    # ---- calendar interaction --------------------------------------------
    def _on_day_clicked(self, date: QDate) -> None:
        day = QDate(date)
        # 点到上/下月的灰字日期时，顺便把日历翻到那个月。
        if (day.year(), day.month()) != self._grid.page():
            self._goto(day.year(), day.month())
        self._grid.set_cursor_date(day)
        if self._anchor is None:
            # First click = start of a new selection (open end for now).
            self._anchor = day
            self._start, self._end = day, None
        else:
            anchor = self._anchor
            self._anchor = None
            if day < anchor:
                self._start, self._end = day, anchor
            else:
                self._start, self._end = anchor, day
        self._paint_range()
        self._sync_summary()

    def _sync_month_label(self) -> None:
        year, month = self._grid.page()
        self._year_btn.setText(f"{year}{self._texts['year_suffix']}")
        self._month_btn.setText(f"{month}{self._texts['month_suffix']}")

    def _paint_range(self) -> None:
        # _MonthGrid 自己画区间色带，不会和 Qt 内置的选中态打架。
        self._grid.set_highlight(self._start, self._end)
        if self._start is not None:
            year, month = self._grid.page()
            if (year, month) != (self._start.year(), self._start.month()):
                self._goto(self._start.year(), self._start.month())

    def _sync_summary(self) -> None:
        start, end = self._start, self._end
        unbounded = str(self._texts["unbounded"])
        fmt = str(self._texts["date_format"])
        if start is None and end is None:
            self._summary.setText(str(self._texts["no_range"]))
            return
        left = start.toString(fmt) if start is not None else unbounded
        right = end.toString(fmt) if end is not None else unbounded
        self._summary.setText(f"{left}  \u2192  {right}")


class _PopupOutsideFilter(QObject):
    """Close a child-widget popup when the user presses outside it.

    :class:`_FilterPopup` lives inside the table window (so it travels with
    the window and can never fall behind it), which means Qt can no longer
    auto-close it the way a ``Qt.Popup`` window would.  This application
    filter restores that behaviour and also re-clamps the popup after the
    host window shrinks.
    """

    def __init__(self, popup: QWidget) -> None:
        super().__init__(popup)
        self._popup = popup

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if not isinstance(obj, QWidget):
            return False
        t = event.type()
        if t == QEvent.MouseButtonPress:
            w = obj
            while w is not None:
                if w is self._popup:
                    return False
                w = w.parentWidget()
            if self._popup.isVisible():
                self._popup.close()
        elif t == QEvent.Resize and obj is self._popup.parentWidget():
            QTimer.singleShot(0, self._popup._relayout)
        elif t in (QEvent.Hide, QEvent.WindowDeactivate) \
                and obj is self._popup.window():
            if self._popup.isVisible():
                self._popup.close()
        return False


class _FilterPopup(QFrame):
    """Excel-style column filter popup with search + checkable values
    or numeric comparison (one or more AND-combined conditions).

    Numeric mode lets the user add multiple ``(op, value)`` conditions —
    e.g. ``(> 200)`` AND ``(< 300)`` — and remove them individually.

    Date mode ("按日期范围") lets the user pick an inclusive start / end
    date; either bound can be left open. The three modes (text / numeric /
    date) are mutually exclusive per column.

    Implemented as a :class:`QFrame` child of the table's top-level window
    rather than as a :class:`QMenu`, because ``QMenu`` interferes with IME
    composition (typing Chinese / Japanese / Korean inside the search box did
    not work).  Being a child widget (instead of a separate ``Qt.Popup``
    window) keeps it glued to the window -- including while the native title
    bar is dragged -- and stops it from being hidden behind the window.
    :class:`_PopupOutsideFilter` restores the click-outside-to-close
    behaviour that the popup window flag used to provide.

    Default semantics: when no prior filter exists, the popup opens with all
    list items visually checked but is treated as "no filter active" until
    the user un-checks at least one item. This makes the empty filter the
    most natural default (selecting the funnel icon should not hide rows).
    """

    filterChanged = Signal(int, object)            # column, set or None
    numericFilterChanged = Signal(int, object)     # column, list[(op, value)] or None
    filterOnlyThis = Signal(int, object)           # column, value: "filter to only this item"
    dateFilterChanged = Signal(int, object)        # column, (start, end) QDate tuple or None
    dateIgnoreSepChanged = Signal(int, bool)       # column, ignore separators

    def __init__(self, column: int, values: Iterable[str],
                 selected: set[str] | None,
                 *,
                 numeric: bool = False,
                 numeric_filter: Sequence[tuple[str, float]] | None = None,
                 date_filter: tuple[QDate | None, QDate | None] | None = None,
                 date_ignore_separators: bool = True,
                 texts: dict | None = None,
                 metrics: dict | None = None,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._texts: dict = {**DEFAULT_TEXTS, **(texts or {})}
        self._metrics: dict = {**DEFAULT_METRICS, **(metrics or {})}
        t, m = self._texts, self._metrics
        self.setObjectName("FilterPopup")
        self.setFrameShape(QFrame.NoFrame)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self._column = column
        # Anchor (window-local) the popup was opened at; every later
        # re-layout is derived from it so repeated resize/move is idempotent.
        self._anchor_pos: QPoint | None = None
        # Zero-delay timer used to defer re-layouts to the next event-loop
        # tick (see ``_relayout``). Owned by the popup so it dies with it.
        self._relayout_timer = QTimer(self)
        self._relayout_timer.setSingleShot(True)
        self._relayout_timer.setInterval(0)
        self._relayout_timer.timeout.connect(self._relayout)
        # Click-outside / window-resize watcher, installed only while shown.
        self._outside_filter = _PopupOutsideFilter(self)
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
        self._condition_rows: list[_NumericConditionRow] = []

        self.setStyleSheet(
            """
            QFrame#FilterPopup {
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
            QLabel#DateHint { color: #80868b; font-size: 11px; }
            QLabel#DateSummary {
                background: #f1f3f4;
                border: 1px solid #e8eaed;
                border-radius: 6px;
                padding: 7px 10px;
                color: #202124;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton#DateChip {
                border: 1px solid #dadce0;
                border-radius: 11px;
                padding: 2px 8px;
                background: #ffffff;
                color: #3c4043;
                font-size: 11px;
            }
            QPushButton#DateChip:hover {
                background: #e8f0fe;
                border-color: #1a73e8;
                color: #1a73e8;
            }
            QToolButton#CalMonth {
                border: none;
                background: transparent;
                color: #202124;
                font-size: 12px;
                font-weight: 600;
                padding: 2px 4px;
                border-radius: 4px;
            }
            QToolButton#CalMonth:hover { background: #f1f3f4; color: #1a73e8; }
            QToolButton#CalMonth::menu-indicator { image: none; width: 0; }
            QPushButton#ChoiceCell {
                border: 1px solid transparent;
                border-radius: 5px;
                padding: 3px 2px;
                background: transparent;
                color: #3c4043;
                font-size: 12px;
            }
            QPushButton#ChoiceCell:hover {
                background: #f1f3f4;
                color: #1a73e8;
            }
            QPushButton#ChoiceCell:checked {
                background: #1a73e8;
                color: #ffffff;
                font-weight: 600;
            }
            QLineEdit#YearEdit {
                border: 1px solid #dadce0;
                border-radius: 4px;
                padding: 2px 6px;
                background: #ffffff;
                color: #202124;
                font-size: 12px;
            }
            QLineEdit#YearEdit:focus { border-color: #1a73e8; }
            QPushButton#YearJump {
                border: 1px solid #dadce0;
                border-radius: 4px;
                padding: 2px 10px;
                background: #ffffff;
                color: #3c4043;
                font-size: 12px;
            }
            QPushButton#YearJump:hover {
                background: #e8f0fe;
                border-color: #1a73e8;
                color: #1a73e8;
            }
            QToolButton#CalNav, QToolButton#CalToday {
                border: none;
                background: transparent;
                color: #5f6368;
                padding: 2px 8px;
                border-radius: 4px;
            }
            QToolButton#CalNav { font-size: 16px; }
            QToolButton#CalToday { font-size: 11px; }
            QToolButton#CalNav:hover, QToolButton#CalToday:hover {
                background: #f1f3f4;
                color: #1a73e8;
            }
            QMenu {
                background: #ffffff;
                border: 1px solid #dadce0;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                padding: 4px 18px;
                border-radius: 4px;
                color: #3c4043;
            }
            QMenu::item:selected { background: #e8f0fe; color: #1a73e8; }
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
        # 关掉布局的尺寸约束（默认 SetDefaultConstraint）。
        # 切换「文本 / 数字 / 日期」模式时会 show()/hide() 一批子控件，布局
        # 随之 invalidate；默认约束下 Qt 会自己给这个弹窗做
        # setGeometry/adjustSize，而此刻布局只更新了一半（宽度还是旧模式、
        # 高度已是新模式的），窗口系统会按真实最小尺寸回夹并打印：
        #   QWindowsWindow::setGeometry: Unable to set geometry ...
        # 弹窗尺寸完全由 _relayout() 负责设置，所以这里不需要 Qt 再插手。
        v.setSizeConstraint(QLayout.SetNoConstraint)

        sort_row = QHBoxLayout()
        sort_row.setSpacing(4)
        self._sort_asc = QPushButton(str(t["sort_asc"]))
        self._sort_desc = QPushButton(str(t["sort_desc"]))
        sort_row.addWidget(self._sort_asc)
        sort_row.addWidget(self._sort_desc)
        v.addLayout(sort_row)

        # Numeric-mode toggle (only when column is registered as numeric).
        self._numeric_toggle: QCheckBox | None = None
        self._numeric_container: QWidget | None = None
        self._numeric_layout: QVBoxLayout | None = None
        if numeric:
            self._numeric_toggle = QCheckBox(str(t["numeric_toggle"]), self)
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

            self._add_btn = QPushButton(str(t["add_condition"]), self._numeric_container)
            self._add_btn.setToolTip(str(t["add_condition_tip"]))
            self._numeric_layout.addWidget(self._add_btn)
            self._add_btn.clicked.connect(lambda: (self._add_condition_row("=", 0.0),
                                                   self._sync_remove_buttons()))

        # Date-range mode (available on every column — cells are parsed
        # with a set of common date formats; unparseable rows are filtered
        # out). Sits directly below the 按数字比较 toggle.
        self._date_toggle = QCheckBox(str(t["date_toggle"]), self)
        v.addWidget(self._date_toggle)

        self._date_container = QWidget(self)
        date_v = QVBoxLayout(self._date_container)
        date_v.setContentsMargins(0, 0, 0, 0)
        date_v.setSpacing(4)
        v.addWidget(self._date_container)

        # Suggest the earliest / latest date found in the column as the
        # initial calendar focus; the filter itself still starts open.
        parsed_dates = [d for d in map(_parse_date, self._all_values)
                        if d is not None]
        self._date_picker = _DateRangePicker(
            min(parsed_dates) if parsed_dates else QDate(),
            max(parsed_dates) if parsed_dates else QDate(),
            self._date_container,
            texts=self._texts,
            metrics=self._metrics,
        )
        date_v.addWidget(self._date_picker)
        self._date_hint = QLabel(str(t["date_hint"]), self._date_container)
        self._date_hint.setObjectName("DateHint")
        self._date_hint.setWordWrap(True)
        date_v.addWidget(self._date_hint)
        self._date_ignore_sep = QCheckBox(str(t["ignore_sep"]), self._date_container)
        self._date_ignore_sep.setChecked(bool(date_ignore_separators))
        self._date_ignore_sep.setToolTip(str(t["ignore_sep_tip"]))
        date_v.addWidget(self._date_ignore_sep)

        if date_filter is not None:
            self._date_picker.set_range(date_filter[0], date_filter[1])
            self._date_toggle.setChecked(True)

        # Text-mode widgets: 全选 checkbox → search box → list.
        self._select_all = QCheckBox(str(t["select_all"]), self)
        self._select_all.setTristate(True)
        v.addWidget(self._select_all)

        self._search = QLineEdit(self)
        self._search.setPlaceholderText(str(t["search_placeholder"]))
        self._search.setClearButtonEnabled(True)
        v.addWidget(self._search)

        self._list = _CheckListWidget(self)
        self._list.setSelectionMode(QAbstractItemView.NoSelection)
        self._list.setMinimumHeight(int(m["list_min_height"]))
        self._list.setMaximumHeight(int(m["list_max_height"]))
        self._list.setMinimumWidth(int(m["list_min_width"]))
        v.addWidget(self._list)

        btn_row = QHBoxLayout()
        self._invert_btn = QPushButton(str(t["invert"]))
        self._reset_btn = QPushButton(str(t["reset"]))
        btn_row.addWidget(self._invert_btn)
        btn_row.addWidget(self._reset_btn)
        btn_row.addStretch(1)
        self._cancel_btn = QPushButton(str(t["cancel"]))
        self._ok_btn = QPushButton(str(t["ok"]))
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
        self._hover_only_btn.setText(str(t["hover_only"]))
        self._hover_only_btn.setObjectName("HoverOnly")
        self._hover_only_btn.setCursor(Qt.PointingHandCursor)
        self._hover_only_btn.setToolTip(str(t["hover_only_tip"]))
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
            self._sync_remove_buttons()
        self._date_toggle.toggled.connect(self._on_date_toggled)
        self._apply_mode_visibility()

    # ---- numeric rows ----------------------------------------------------
    def _add_condition_row(self, op: str, value: float) -> _NumericConditionRow:
        assert self._numeric_layout is not None
        row = _NumericConditionRow(op, value, self._numeric_container,
                                   texts=self._texts)
        row.removeRequested.connect(self._on_remove_row)
        # insert *before* the "+ 添加条件" button (which is the last item)
        self._numeric_layout.insertWidget(self._numeric_layout.count() - 1, row)
        self._condition_rows.append(row)
        # 布局设成了 SetNoConstraint，Qt 不会再因为行数变化自动撑高弹窗，
        # 这里显式重排一次（show_at 阶段窗口还不可见，忽略即可）。
        if self.isVisible():
            self._relayout_timer.start()
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
        if self.isVisible():
            self._relayout_timer.start()

    def _sync_remove_buttons(self) -> None:
        # Disable the × button when there's only one row left so the user
        # always has at least one condition to fill in.
        for r in self._condition_rows:
            r._remove.setEnabled(len(self._condition_rows) > 1)

    def _collect_conditions(self) -> list[tuple[str, float]]:
        return [r.condition() for r in self._condition_rows]

    # ---- mode toggles (numeric / date are mutually exclusive) ------------
    def _on_numeric_toggled(self, checked: bool) -> None:
        if checked and self._date_toggle is not None \
                and self._date_toggle.isChecked():
            self._date_toggle.blockSignals(True)
            self._date_toggle.setChecked(False)
            self._date_toggle.blockSignals(False)
        self._apply_mode_visibility()

    def _on_date_toggled(self, checked: bool) -> None:
        if checked and self._numeric_toggle is not None \
                and self._numeric_toggle.isChecked():
            self._numeric_toggle.blockSignals(True)
            self._numeric_toggle.setChecked(False)
            self._numeric_toggle.blockSignals(False)
        self._apply_mode_visibility()

    def _apply_mode_visibility(self) -> None:
        numeric_on = (self._numeric_toggle is not None
                      and self._numeric_toggle.isChecked())
        date_on = (self._date_toggle is not None
                   and self._date_toggle.isChecked())
        special_on = numeric_on or date_on
        for w in (self._search, self._select_all, self._list):
            (w.show if not special_on else w.hide)()
        # 「反选」只对勾选列表有意义；数字/日期模式没有对应语义，所以直接
        # 隐藏它，而不是留一个点了没任何反应的按钮。
        (self._invert_btn.show if not special_on else self._invert_btn.hide)()
        # 「重置」在三种模式下都可用，但语义不同，用 tooltip 说明。
        if date_on:
            self._reset_btn.setToolTip(str(self._texts["reset_tip_date"]))
        elif numeric_on:
            self._reset_btn.setToolTip(str(self._texts["reset_tip_numeric"]))
        else:
            self._reset_btn.setToolTip(str(self._texts["reset_tip_text"]))
        if self._numeric_container is not None:
            (self._numeric_container.show if numeric_on
             else self._numeric_container.hide)()
        if self._date_container is not None:
            (self._date_container.show if date_on
             else self._date_container.hide)()
        # 触发 layout 重算：日期模式把列表换成日历，弹窗需要跟着长高/收窄
        self.layout().invalidate()
        if self.isVisible():
            # 刚 show()/hide() 的子控件此时还没完成 polish，立刻按 sizeHint
            # resize 会把“过期”的尺寸交给 Windows，触发
            # "QWindowsWindow::setGeometry: Unable to set geometry ..."。
            # 推迟一帧，等布局/样式稳定后再量尺寸。
            self._relayout_timer.start()
        else:
            self._relayout()

    def _host_rect(self) -> QRect:
        """Available area (window-local) the popup may occupy."""
        win = self.window()
        if win is None:
            return QRect()
        return win.rect().adjusted(4, 4, -4, -4)

    def _relayout(self) -> None:
        """Resize the popup to the current mode and keep it inside the window.

        The target size is ``sizeHint()`` *expanded* to ``minimumSizeHint()``
        so the layout never gets less room than it needs.  The popup is a
        child of the window, so all coordinates are window-local: moving the
        window needs no work (it travels with it), only its own size / anchor
        changes do.
        """
        self.ensurePolished()
        lay = self.layout()
        if lay is not None:
            lay.activate()
        want = self.sizeHint().expandedTo(self.minimumSizeHint())
        if not self.isVisible():
            self.resize(want)
            return
        rect = self._host_rect()
        if rect.isNull():
            return
        anchor = self._anchor_pos if self._anchor_pos is not None else self.pos()
        w = min(want.width(), rect.width())
        h = min(want.height(), rect.height())
        x, y = self._clamp_pos(anchor, QSize(w, h), rect)
        if (x, y, w, h) != (self.x(), self.y(), self.width(), self.height()):
            self.setGeometry(x, y, w, h)

    @staticmethod
    def _clamp_pos(anchor: QPoint, size: QSize, rect: QRect) -> tuple[int, int]:
        """Position a ``size``-sized popup at ``anchor`` (flipping up if needed)."""
        x = min(anchor.x(), rect.left() + rect.width() - size.width())
        x = max(x, rect.left())
        y = anchor.y()
        if y + size.height() > rect.top() + rect.height():
            y = anchor.y() - size.height()
        y = max(y, rect.top())
        y = min(y, max(rect.top(), rect.top() + rect.height() - size.height()))
        return x, y

    # ---- list population -------------------------------------------------
    def _populate_list(self, query: str) -> None:
        self._list.blockSignals(True)
        self._list.clear()
        q = query.strip().lower()
        for value in self._all_values:
            display = value if value != "" else str(self._texts["blank"])
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
        blank = str(self._texts["blank"])
        empties = [x for x in items if x["display"] == blank]
        non_empty = [x for x in items if x["display"] != blank]
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
        # Only meaningful for the checkbox list; the button is hidden in
        # numeric / date mode (guarded here as well for keyboard/programmatic
        # invocation).
        if (self._numeric_toggle is not None
                and self._numeric_toggle.isChecked()) \
                or self._date_toggle.isChecked():
            return
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
        # 重置: 回到“还没筛选”的状态。三种模式语义不同，都在本地完成 ——
        # 不关闭弹窗、不发任何 filter 信号；要真正生效仍需点“确定”。
        numeric_on = (self._numeric_toggle is not None
                      and self._numeric_toggle.isChecked())
        date_on = self._date_toggle.isChecked()
        if date_on:
            # 日期模式：清空起止 → 摘要显示“未选择（不限）”
            self._date_picker.set_range(None, None)
            return
        if numeric_on:
            # 数字模式：删掉多余条件，保留一条“等于 0”
            if self._numeric_layout is not None:
                while len(self._condition_rows) > 1:
                    row = self._condition_rows.pop()
                    self._numeric_layout.removeWidget(row)
                    row.setParent(None)
                    row.deleteLater()
            if self._condition_rows:
                self._condition_rows[0].set_condition("=", 0.0)
            self._sync_remove_buttons()
            # 删除的行要到下一次事件循环才真正从布局里消失，同步重排会量到
            # “还没减小”的旧高度，所以同样交给 0ms 定时器。
            self._relayout_timer.start()
            return
        # 文本模式: uncheck every visible item in the popup. Local action —
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
        numeric_on = (self._numeric_toggle is not None
                      and self._numeric_toggle.isChecked())
        date_on = (self._date_toggle is not None
                   and self._date_toggle.isChecked())
        if numeric_on:
            conditions = self._collect_conditions()
            self.numericFilterChanged.emit(self._column, conditions)
            # 同时清理文本 / 日期 filter
            self.filterChanged.emit(self._column, None)
            self.dateFilterChanged.emit(self._column, None)
        elif date_on:
            start, end = self._date_picker.range()
            if start is None and end is None:
                # 两个边界都为空 = 不限 = 清除该列日期筛选
                self.dateFilterChanged.emit(self._column, None)
            else:
                self.dateFilterChanged.emit(self._column, (start, end))
            self.dateIgnoreSepChanged.emit(
                self._column, self._date_ignore_sep.isChecked())
            # 同时清理文本 / 数字 filter
            self.filterChanged.emit(self._column, None)
            self.numericFilterChanged.emit(self._column, None)
        else:
            # Excel-like semantics: empty selection = no filter (show all).
            # The user sees an unchecked list and "确定" without picking
            # anything → fall back to the un-filtered default. Non-empty
            # selection → keep only the checked values.
            if not self._selected:
                self.filterChanged.emit(self._column, None)
            else:
                self.filterChanged.emit(self._column, set(self._selected))
            # 清理 numeric / date filter (回到纯文本模式)
            self.numericFilterChanged.emit(self._column, None)
            self.dateFilterChanged.emit(self._column, None)
        self.close()

    def show_at(self, global_pos: QPoint) -> None:
        owner = self.parentWidget()
        win = owner.window() if owner is not None else None
        if win is None:
            self.close()
            return
        # Re-parent to the top-level window: the popup then shares the
        # window's native surface, so it follows every window move (even
        # during a native title-bar drag) and can never be covered by it.
        if self.parentWidget() is not win:
            self.setParent(win)
        self._anchor_pos = win.mapFromGlobal(global_pos)
        self.ensurePolished()
        lay = self.layout()
        if lay is not None:
            lay.activate()
        size = self.sizeHint().expandedTo(self.minimumSizeHint())
        rect = self._host_rect()
        w = min(size.width(), rect.width())
        h = min(size.height(), rect.height())
        x, y = self._clamp_pos(self._anchor_pos, QSize(w, h), rect)
        self.setGeometry(x, y, w, h)
        self.show()
        self.raise_()
        self._relayout_timer.start()
        if self._numeric_toggle is not None and self._numeric_toggle.isChecked() \
                and self._condition_rows:
            self._condition_rows[0]._value.setFocus()
            self._condition_rows[0]._value.selectAll()
        elif self._date_toggle is not None and self._date_toggle.isChecked():
            self._date_picker.focus_start()
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

    def showEvent(self, event) -> None:
        app = QApplication.instance()
        if app is not None:
            app.installEventFilter(self._outside_filter)
        super().showEvent(event)

    def hideEvent(self, event) -> None:
        app = QApplication.instance()
        if app is not None:
            app.removeEventFilter(self._outside_filter)
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

    # Default geometry of the right-side icon area.  Every value is copied
    # onto the instance so ``metrics`` can override it per table.
    FILTER_SIZE = 16
    FILTER_MARGIN = 6
    SORT_W = 8
    SORT_H = 14
    SORT_GAP = 6           # gap between sort arrows and filter funnel
    SORT_TEXT_GAP = 6      # min gap between text and sort arrows

    def __init__(self, orientation: Qt.Orientation, parent: QWidget | None = None,
                 *, texts: dict | None = None,
                 metrics: dict | None = None) -> None:
        super().__init__(orientation, parent)
        self._texts: dict = {**DEFAULT_TEXTS, **(texts or {})}
        m = {**DEFAULT_METRICS, **(metrics or {})}
        self.FILTER_SIZE = int(m["filter_icon_size"])
        self.FILTER_MARGIN = int(m["filter_margin"])
        self.SORT_W = int(m["sort_w"])
        self.SORT_H = int(m["sort_h"])
        self.SORT_GAP = int(m["sort_gap"])
        self.SORT_TEXT_GAP = int(m["sort_text_gap"])
        self._check_box_size = int(m["check_box_size"])
        self._check_box_margin = int(m["check_box_margin"])
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
        self.setMinimumSectionSize(int(m["min_section"]))
        self.setDefaultSectionSize(int(m["default_section"]))

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
            cb_sz = self._check_box_size
            margin_left = self._check_box_margin
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
            painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft,
                             str(self._texts["check_all"]))
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
                 *, skip_filter_columns: Iterable[int] = (),
                 texts: dict | None = None,
                 metrics: dict | None = None,
                 style: dict | None = None) -> None:
        """
        Parameters
        ----------
        skip_filter_columns : Iterable[int]
            Columns that get no filter funnel (e.g. an action column).
        texts : dict, optional
            Any subset of :data:`DEFAULT_TEXTS` -- every visible string.
        metrics : dict, optional
            Any subset of :data:`DEFAULT_METRICS` -- row height, header,
            calendar cell size, popup list size, ...
        style : dict, optional
            Any subset of :data:`DEFAULT_STYLE` -- table / header palette,
            border radius and scrollbar colours.
        """
        super().__init__(parent)
        self._texts: dict = {**DEFAULT_TEXTS, **(texts or {})}
        self._metrics: dict = {**DEFAULT_METRICS, **(metrics or {})}
        self._style: dict = {**DEFAULT_STYLE, **(style or {})}
        self._proxy = _MultiColumnFilterProxy(self)
        super().setModel(self._proxy)

        self._header = _FilterHeaderView(Qt.Horizontal, self,
                                         texts=self._texts,
                                         metrics=self._metrics)
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
        self.verticalHeader().setDefaultSectionSize(int(self._metrics["row_height"]))
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
        # Right-click context menu for batch operations.
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

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
        m = self._metrics
        s = self._style
        self.setStyleSheet(
            f"""
            QTableView {{
                background: {s['background']};
                alternate-background-color: {s['alternate_background']};
                gridline-color: {s['gridline_color']};
                border: 1px solid {s['border_color']};
                border-radius: {s['border_radius']}px;
                selection-background-color: {s['selection_bg']};
                selection-color: {s['text_color']};
                font-size: {m['table_font_size']}px;
            }}
            QTableView::item {{ padding: 6px 8px; border: none; }}
            QTableView::item:hover {{ background: {s['item_hover_bg']}; }}
            QTableView::item:selected {{
                background: {s['selection_bg']};
                color: {s['selection_text_color']};
            }}

            QHeaderView::section {{
                background: {s['header_background']};
                color: {s['header_text_color']};
                padding: 6px {m['header_pad_right']}px 6px {m['header_pad_left']}px;
                border: none;
                border-right: 1px solid {s['header_separator_color']};
                border-bottom: 1px solid {s['header_border_color']};
                font-weight: 600;
                font-size: {m['header_font_size']}px;
            }}
            QHeaderView::section:hover {{ background: {s['header_hover_bg']}; }}
            QHeaderView::section:pressed {{ background: {s['header_pressed_bg']}; }}

            QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
            QScrollBar::handle:vertical {{
                background: {s['scrollbar_handle']};
                border-radius: 5px; min-height: 24px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {s['scrollbar_handle_hover']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
            QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px; }}
            QScrollBar::handle:horizontal {{
                background: {s['scrollbar_handle']};
                border-radius: 5px; min-width: 24px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: {s['scrollbar_handle_hover']};
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
            """
        )

    def style(self) -> dict:
        """Return a copy of the current style dictionary."""
        return dict(self._style)

    def set_style(self, style: dict) -> None:
        """Merge ``style`` into the current style dict and re-apply it."""
        self._style.update(style)
        self._apply_style()
        self.viewport().update()

    def texts(self) -> dict:
        """Return a copy of the current text dictionary."""
        return dict(self._texts)

    def set_texts(self, texts: dict) -> None:
        """Merge ``texts`` into the current text dict and refresh the UI."""
        self._texts.update(texts)
        self._header._texts = self._texts
        self._header.viewport().update()

    def metrics(self) -> dict:
        """Return a copy of the current metrics dictionary."""
        return dict(self._metrics)

    def set_metrics(self, metrics: dict) -> None:
        """Merge ``metrics`` into the current metrics dict and re-apply."""
        self._metrics.update({k: int(v) for k, v in metrics.items()})
        self.verticalHeader().setDefaultSectionSize(self._metrics["row_height"])
        self._apply_style()
        self._header.updateGeometry()
        self.viewport().update()

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
        extra = int(self._metrics["col_extra"])
        floor = int(self._metrics["col_min"])
        for col in range(model.columnCount()):
            self._header.resizeSection(col, max(self._header.sectionSize(col) + extra, floor))

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

    def column_date_filter(self, column: int) -> tuple[QDate, QDate] | None:
        """Return the inclusive date-range filter for *column* as
        ``(start, end)`` — either bound may be ``None`` (open-ended), or
        ``None`` if the column has no date filter.
        """
        return self._proxy.column_date_filter(column)

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
            date_filter=self._proxy.column_date_filter(column),
            date_ignore_separators=self._proxy.column_date_ignore_separators(column),
            texts=self._texts,
            metrics=self._metrics,
            parent=self,
        )
        popup.filterChanged.connect(self._on_filter_changed)
        popup.numericFilterChanged.connect(self._on_numeric_filter_changed)
        popup.dateFilterChanged.connect(self._on_date_filter_changed)
        popup.dateIgnoreSepChanged.connect(self._on_date_ignore_sep_changed)
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
        self._proxy.set_column_numeric_filter(column, None)
        self._proxy.set_column_date_filter(column, None)
        self._header.set_active(column, True)

    def _on_filter_changed(self, column: int, allowed: set[str] | None) -> None:
        self._proxy.set_column_filter(column, allowed)
        self._refresh_filter_icon(column)

    def _on_numeric_filter_changed(self, column: int,
                                    conditions: list[tuple[str, float]] | None) -> None:
        # ``conditions`` is None to clear, otherwise a list of (op, value) AND'd.
        self._proxy.set_column_numeric_filter(column, conditions)
        self._refresh_filter_icon(column)

    def _on_date_filter_changed(self, column: int,
                                date_range: tuple[QDate | None, QDate | None] | None) -> None:
        # ``date_range`` is None to clear, otherwise an inclusive
        # ``(start, end)`` with either bound possibly None (open).
        self._proxy.set_column_date_filter(column, date_range)
        self._refresh_filter_icon(column)

    def _on_date_ignore_sep_changed(self, column: int, enabled: bool) -> None:
        self._proxy.set_column_date_ignore_separators(column, enabled)

    def _refresh_filter_icon(self, column: int) -> None:
        # active = has any filter (text or numeric or date)
        self._header.set_active(
            column,
            self._proxy.column_filter(column) is not None
            or self._proxy.column_numeric_filter(column) is not None
            or self._proxy.column_date_filter(column) is not None,
        )

    # ------------------------------------------------------------------
    # checkable rows
    # ------------------------------------------------------------------
    def _show_context_menu(self, pos: QPoint) -> None:
        menu = QMenu(self)
        sel_count = len(self.selectionModel().selectedRows())
        if sel_count > 0:
            a = menu.addAction(str(self._texts["delete_selected"]).format(n=sel_count))
            a.triggered.connect(lambda: self.delete_selected_rows())
        chk_count = len(self.checked_rows())
        if chk_count > 0:
            a = menu.addAction(str(self._texts["delete_checked"]).format(n=chk_count))
            a.triggered.connect(lambda: self.delete_checked_rows())
        if sel_count > 0 or chk_count > 0:
            menu.addSeparator()
        if self._checkable_rows:
            src = self._proxy.sourceModel()
            all_checked = (
                src is not None
                and all(
                    src.item(r, self._check_column).checkState() == Qt.Checked
                    for r in range(src.rowCount())
                    if src.item(r, self._check_column) is not None
                )
            )
            menu.addAction(str(self._texts["uncheck_all"] if all_checked
                                else self._texts["check_all"])).triggered.connect(
                lambda: self.set_all_checked(not all_checked)
            )
        menu.addAction(str(self._texts["clear_filters"])).triggered.connect(self.clear_filters)
        menu.exec(self.mapToGlobal(pos))

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
            self.setColumnWidth(column, int(self._metrics["check_column_width"]))
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


ACTION_STYLES = {
    "delete":   dict(bg_normal="#ffffff", bg_hover="#fdecea", border="#ea4335", color="#c5221f"),
    "confirm":  dict(bg_normal="#ffffff", bg_hover="#e8f5e9", border="#43a047", color="#2e7d32"),
    "info":     dict(bg_normal="#ffffff", bg_hover="#e3f2fd", border="#1e88e5", color="#1565c0"),
    "warning":  dict(bg_normal="#ffffff", bg_hover="#fff3e0", border="#fb8c00", color="#e65100"),
    # Solid filled variants (no outline, background is the accent colour).
    "delete_solid":  dict(bg_normal="#ea4335", bg_hover="#d93025", border="#ea4335", color="#ffffff", filled=True),
    "confirm_solid": dict(bg_normal="#43a047", bg_hover="#2e7d32", border="#43a047", color="#ffffff", filled=True),
    "info_solid":    dict(bg_normal="#1e88e5", bg_hover="#1565c0", border="#1e88e5", color="#ffffff", filled=True),
    "warning_solid": dict(bg_normal="#fb8c00", bg_hover="#e65100", border="#fb8c00", color="#ffffff", filled=True),
}


class ActionDelegate(QStyledItemDelegate):
    """Render a clickable button inside a cell. Used to show inline actions
    (e.g. a "delete" button) at the end of every row.

    Use as::

        delegate = ActionDelegate("删除", parent=table)
        delegate.clicked.connect(lambda src_row: table.delete_rows([src_row]))
        table.setItemDelegateForColumn(action_col, delegate)

    To customise the button colours, pass a ``style`` dict (or one of the
    presets from :data:`ACTION_STYLES`)::

        delegate = ActionDelegate("确认", parent=table,
                                  style=ACTION_STYLES["confirm"])

    For a solid filled button (no outline, coloured background)::

        delegate = ActionDelegate("删除", parent=table,
                                  style=ACTION_STYLES["delete_solid"])
    """

    clicked = Signal(int)  # source row index

    def __init__(self, text: str = "删除", parent: QTableView | None = None,
                 *, style: dict | None = None,
                 radius: int = 6,
                 margin_x: int = 6,
                 margin_y: int = 4,
                 min_width: int = 80,
                 min_height: int = 30) -> None:
        super().__init__(parent)
        self._text = text
        self._hover_row = -1
        self._radius = int(radius)
        self._margin_x = int(margin_x)
        self._margin_y = int(margin_y)
        self._min_size = QSize(int(min_width), int(min_height))
        s = ACTION_STYLES["delete"] if style is None else style
        self._bg_normal = s["bg_normal"]
        self._bg_hover = s["bg_hover"]
        self._border = s["border"]
        self._color = s["color"]
        self._filled = s.get("filled", False)
        if parent is not None:
            parent.setMouseTracking(True)
            parent.viewport().installEventFilter(self)

    def paint(self, painter: QPainter, option, index: QModelIndex) -> None:
        painter.save()
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, QColor("#e8f0fe"))
        elif self._hover_row == index.row():
            painter.fillRect(option.rect, QColor("#f1f3f4"))
        rect = option.rect.adjusted(self._margin_x, self._margin_y,
                                    -self._margin_x, -self._margin_y)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(Qt.NoPen if self._filled
                       else QPen(QColor(self._border), 1))
        painter.setBrush(QColor(self._bg_hover) if self._hover_row == index.row()
                         else QColor(self._bg_normal))
        painter.drawRoundedRect(rect, self._radius, self._radius)
        painter.setPen(QColor(self._color))
        painter.drawText(rect, Qt.AlignCenter, self._text)
        painter.restore()

    def sizeHint(self, option, index: QModelIndex) -> QSize:
        return QSize(self._min_size)

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
