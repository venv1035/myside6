from __future__ import annotations

import json
from PySide6.QtCore import QMimeData, QObject, QPoint, QRect, QSize, Qt, QUrl, Signal
from PySide6.QtGui import (
    QColor, QDrag, QFont, QIcon, QMouseEvent, QPainter, QPen, QPixmap,
)
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PySide6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLayout, QPushButton,
    QScrollArea, QVBoxLayout, QWidget, QWidgetItem,
)

_MIME = "application/x-dragbar-items"


def _manhattan_dist(a: QPoint, b: QPoint) -> int:
    return abs(a.x() - b.x()) + abs(a.y() - b.y())


# ── helpers ─────────────────────────────────────────────────────────────

def _mime_data(names, items_meta, source_id: int) -> QMimeData:
    payload = json.dumps({
        "source_id": source_id,
        "items": [
            {"name": n, "text": items_meta[n]["text"],
             "icon": items_meta[n].get("icon", "")}
            for n in names if n in items_meta
        ],
    })
    mime = QMimeData()
    mime.setData(_MIME, payload.encode("utf-8"))
    return mime


def _parse_mime(event) -> dict | None:
    try:
        raw = event.mimeData().data(_MIME).data().decode("utf-8")
        return json.loads(raw)
    except Exception:
        return None


# ── DragBarItem (data object) ────────────────────────────────────────────

class DragBarItem(QObject):
    """Data object for a single DragBar item.

    Auto‑supports move / delete / reset when added to a DragBar.
    Icon 支持主题名 (``"folder"``)、本地路径 (``"C:/img.png"``)、
    或 URL (``"https://example.com/icon.png"``)。
    """

    clicked = Signal(bool, bool)  # ctrl, shift
    icon_changed = Signal()
    _net: QNetworkAccessManager | None = None

    def __init__(self, name: str, text: str, icon=None):
        super().__init__()
        self.name = name
        self.text = text
        self._icon_src = ""
        self._icon = QIcon()
        if icon is not None:
            if isinstance(icon, str):
                self._icon_src = icon
                if icon.startswith("http://") or icon.startswith("https://"):
                    self._download_icon(icon)
                else:
                    self._icon = QIcon.fromTheme(icon)
                    if self._icon.isNull():
                        self._icon = QIcon(icon)
            else:
                self._icon = icon

    @classmethod
    def _get_net(cls) -> QNetworkAccessManager:
        if cls._net is None:
            cls._net = QNetworkAccessManager()
        return cls._net

    def _download_icon(self, url: str):
        mgr = self._get_net()
        reply = mgr.get(QNetworkRequest(QUrl(url)))
        reply.finished.connect(lambda r=reply: self._on_icon_downloaded(r))

    def _on_icon_downloaded(self, reply):
        data = reply.readAll()
        px = QPixmap()
        if px.loadFromData(data) and not px.isNull():
            self._icon = QIcon(px)
            self.icon_changed.emit()
        reply.deleteLater()

    @property
    def icon_src(self) -> str:
        return self._icon_src


# ── FlowLayout ──────────────────────────────────────────────────────────

class _FlowLayout(QLayout):
    def __init__(self, parent=None, vertical: bool = False):
        super().__init__(parent)
        self._items: list[QLayoutItem] = []
        self._vertical = vertical

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        return self._items[index] if 0 <= index < len(self._items) else None

    def takeAt(self, index):
        return self._items.pop(index) if 0 <= index < len(self._items) else None

    def indexOf(self, w: QWidget) -> int:
        for i, it in enumerate(self._items):
            if it.widget() is w:
                return i
        return -1

    def insertWidget(self, index: int, w: QWidget) -> None:
        self.addChildWidget(w)
        wi = QWidgetItem(w)
        self._items.insert(index, wi)

    def expandingDirections(self):
        return Qt.Orientations()

    def hasHeightForWidth(self):
        return not self._vertical

    def heightForWidth(self, w):
        return self._layout(QRect(0, 0, w, 0), False)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._layout(rect, True)

    def sizeHint(self):
        m = self.contentsMargins()
        if self._vertical:
            h = m.top() + m.bottom()
            gap = self.spacing()
            for it in self._items:
                sh = it.sizeHint()
                if sh.isValid() and sh.height() > 0:
                    h += sh.height() + gap
            return QSize(200, h)
        s = QSize()
        for it in self._items:
            s = s.expandedTo(it.minimumSize())
        return QSize(200, s.height() + m.top() + m.bottom())

    def minimumSize(self):
        s = QSize()
        for it in self._items:
            s = s.expandedTo(it.minimumSize())
        m = self.contentsMargins()
        return QSize(s.width() + m.left() + m.right(),
                     s.height() + m.top() + m.bottom())

    def _layout(self, rect, set_geo):
        if self._vertical:
            return self._layout_vertical(rect, set_geo)
        return self._layout_horizontal(rect, set_geo)

    def _layout_horizontal(self, rect, set_geo):
        m = self.contentsMargins()
        x = rect.x() + m.left()
        y = rect.y() + m.top()
        row_h = 0
        gap = self.spacing()
        right = rect.right() - m.right()

        for it in self._items:
            w = it.widget()
            if w is None:
                continue
            hint = it.sizeHint()
            if not hint.isValid() or hint.width() <= 0:
                continue
            if x + hint.width() > right and x > rect.x() + m.left():
                x = rect.x() + m.left()
                y += row_h + gap
                row_h = 0
            if set_geo:
                w.setGeometry(QRect(QPoint(x, y), hint))
            x += hint.width() + gap
            row_h = max(row_h, hint.height())

        return y + row_h - rect.y() + m.bottom()

    def _layout_vertical(self, rect, set_geo):
        m = self.contentsMargins()
        x = rect.x() + m.left()
        y = rect.y() + m.top()
        col_w = 0
        gap = self.spacing()
        bottom = rect.bottom() - m.bottom()

        for it in self._items:
            w = it.widget()
            if w is None:
                continue
            hint = it.sizeHint()
            if not hint.isValid() or hint.height() <= 0:
                continue
            if y + hint.height() > bottom and y > rect.y() + m.top():
                y = rect.y() + m.top()
                x += col_w + gap
                col_w = 0
            if set_geo:
                w.setGeometry(QRect(QPoint(x, y), hint))
            y += hint.height() + gap
            col_w = max(col_w, hint.width())

        return y + gap - rect.y() + m.bottom()


# ── Trash zone ──────────────────────────────────────────────────────────

class _TrashZone(QWidget):
    """Drop target that deletes the dropped items."""

    accepted = Signal(list)

    def __init__(self, opts: dict, parent=None):
        super().__init__(parent)
        self._opts = opts
        self._over = False
        self.setAcceptDrops(True)
        self.setFixedSize(*opts["trash_size"])

    def paintEvent(self, event):
        o = self._opts
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        danger = QColor(o["danger"])
        if self._over:
            fill = QColor(danger)
            fill.setAlpha(30)
            p.setBrush(fill)
            p.setPen(QPen(danger, 2))
            p.drawRoundedRect(self.rect().adjusted(2, 2, -2, -2),
                              o["zone_radius"], o["zone_radius"])
        p.setPen(danger if self._over else QColor(o["muted"]))
        p.setFont(QFont(o["icon_font_family"], o["trash_font_size"]))
        p.drawText(self.rect(), Qt.AlignCenter, o["trash_icon"])

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(_MIME):
            self._over = True
            self.update()
            event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self._over = False
        self.update()

    def dropEvent(self, event):
        self._over = False
        self.update()
        parsed = _parse_mime(event)
        if parsed:
            names = [it["name"] for it in parsed["items"]]
            self.accepted.emit(names)
        event.acceptProposedAction()


# ── Reset zone ──────────────────────────────────────────────────────────

class _ResetZone(QWidget):
    """Click target that restores the item list to its last snapshot."""

    clicked = Signal()

    def __init__(self, opts: dict, parent=None):
        super().__init__(parent)
        self._opts = opts
        self.setFixedSize(*opts["reset_size"])
        self._hovered = False
        self.setCursor(Qt.PointingHandCursor)
        self.setMouseTracking(True)

    def paintEvent(self, event):
        o = self._opts
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = self.rect().adjusted(2, 2, -2, -2)
        if self._hovered:
            p.setBrush(QColor(o["reset_hover_fill"]))
            p.setPen(Qt.NoPen)
            p.drawRoundedRect(r, o["zone_radius"], o["zone_radius"])
        p.setPen(QColor(o["reset_hover_color"] if self._hovered else o["mid"]))
        p.setFont(QFont(o["icon_font_family"], o["reset_font_size"]))
        p.drawText(self.rect(), Qt.AlignCenter, o["reset_icon"])

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
            event.accept()
            return
        super().mousePressEvent(event)

    def enterEvent(self, event):
        self._hovered = True
        self.update()

    def leaveEvent(self, event):
        self._hovered = False
        self.update()


# ── Drop container (hosts flow layout, forwards drag events) ────────────

class _DropContainer(QWidget):

    def __init__(self, bar: "DragBar"):
        super().__init__()
        self._bar = bar
        self.setAcceptDrops(True)

    def paintEvent(self, event):
        super().paintEvent(event)
        rr = getattr(self._bar, '_rubber_rect', None)
        if rr is not None:
            p = QPainter(self)
            p.setRenderHint(QPainter.Antialiasing)
            p.setPen(QPen(QColor(26, 115, 232), 1.5))
            p.setBrush(QColor(26, 115, 232, 25))
            p.drawRect(rr)

    def dragEnterEvent(self, event):
        self._bar._on_drag_enter(event)

    def dragMoveEvent(self, event):
        self._bar._on_drag_move(event)

    def dragLeaveEvent(self, event):
        self._bar._on_drag_leave(event)

    def dropEvent(self, event):
        self._bar._on_drop(event)


# ── DragBar item widget ─────────────────────────────────────────────────

class _DragItem(QWidget):
    clicked = Signal(str, bool, bool)
    dragRequested = Signal(str)

    def __init__(self, item: DragBarItem, opts: dict, parent=None):
        super().__init__(parent)
        self._item = item
        self._opts = opts
        self.selected = False
        self._hovered = False
        self.setFixedSize(opts["item_size"], opts["item_size"])
        self.setCursor(Qt.OpenHandCursor)
        self.setMouseTracking(True)
        self.setToolTip(item.text)
        self._drag_start: QPoint | None = None

    def sizeHint(self):
        return QSize(self._opts["item_size"], self._opts["item_size"])

    def paintEvent(self, event):
        o = self._opts
        radius = o["item_radius"]
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = self.rect().adjusted(2, 2, -2, -2)

        if self.selected:
            p.setBrush(QColor(o["item_selected_fill"]))
            p.setPen(QPen(QColor(o["accent"]), 2))
            p.drawRoundedRect(r, radius, radius)
        elif self._hovered:
            p.setBrush(QColor(o["item_hover_fill"]))
            p.setPen(Qt.NoPen)
            p.drawRoundedRect(r, radius, radius)

        sz = o["icon_size"]
        if not self._item._icon.isNull():
            px = self._item._icon.pixmap(sz, sz)
            ix = (self.width() - sz) // 2
            p.drawPixmap(ix, o["icon_top"], px)
        else:
            p.setPen(QColor(o["item_icon_color"]))
            p.setFont(QFont(o["icon_font_family"], o["label_font_size"] * 2))
            p.drawText(QRect(0, 4, self.width(), sz + 4), Qt.AlignCenter,
                       o["placeholder_icon"])

        p.setPen(QColor(o["item_text_color"]))
        font = QFont(self.font())
        font.setPointSize(o["label_font_size"])
        p.setFont(font)
        p.drawText(QRect(0, o["label_top"], self.width(), o["label_height"]),
                   Qt.AlignCenter, self._item.text)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._drag_start = event.position().toPoint()
            mod = QApplication.keyboardModifiers()
            self.clicked.emit(
                self._item.name,
                bool(mod & Qt.ControlModifier),
                bool(mod & Qt.ShiftModifier),
            )
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton and self._drag_start is not None:
            d = _manhattan_dist(event.position().toPoint(), self._drag_start)
            if d > QApplication.startDragDistance():
                self.dragRequested.emit(self._item.name)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_start = None
        super().mouseReleaseEvent(event)

    def enterEvent(self, event):
        self._hovered = True
        self.update()

    def leaveEvent(self, event):
        self._hovered = False
        self.update()


# ── DragBar ─────────────────────────────────────────────────────────────

class DragBar(QWidget):
    """可拖拽图标工具栏。

    支持同一 Bar 内拖拽排序、跨 Bar 拖拽、多选、回收站删除、重置初始状态。
    支持横向（默认）和纵向两种方向。

    Parameters
    ----------
    fixed_length : int | None
        固定宽度（横向）或固定高度（纵向），超过则换行。
    spacing : int
        元素间距。
    style : dict | None
        样式字典，覆盖 :data:`DragBar.DEFAULT_STYLE` 中的任意键
        （背景 / 边框 / 颜色 / 尺寸 / 图标字符……）。
    closable : bool
        是否显示右上角 X 关闭按钮。
    vertical : bool
        True 为纵向排列，False 为横向。
    item_size : int
        单个图标的边长（含文字区域）。
    icon_size : int
        图标像素尺寸。
    label_font_size : int
        图标下方文字字号(pt)。
    trash_size, reset_size : tuple[int, int]
        垃圾桶 / 重置按钮的尺寸。
    trash_icon, reset_icon : str
        垃圾桶 / 重置按钮显示的字符。
    close_text : str
        右上角关闭按钮的文字。
    show_trash, show_reset : bool
        是否显示垃圾桶 / 重置按钮。

    Signals
    -------
    item_moved(name, new_index)
    item_removed(name)
    selection_changed([names...])
    closed
    """

    item_moved = Signal(str, int)
    item_removed = Signal(str)
    selection_changed = Signal(list)
    closed = Signal()

    DEFAULT_STYLE = {
        # -- container ----------------------------------------------------
        "background": "transparent",
        "border": "none",
        "border_radius": 0,
        "padding": 4,
        # -- items ---------------------------------------------------------
        "item_size": 64,
        "icon_size": 28,
        "icon_top": 6,
        "label_top": 40,
        "label_height": 22,
        "label_font_size": 8,
        "item_radius": 8,
        "item_text_color": "#323232",
        "item_icon_color": "#b4b4b4",
        "item_hover_fill": "#0a000000",      # 黑色 4% (AARRGGBB)
        "item_selected_fill": "#231a73e8",   # 主色 14%
        "accent": "#1a73e8",
        "placeholder_icon": "\U0001F4C4",
        "icon_font_family": "Segoe UI Symbol",
        "drag_gap": 4,
        # -- trash / reset zones -------------------------------------------
        "show_trash": True,
        "show_reset": True,
        "trash_size": (56, 60),
        "trash_icon": "\U0001F5D1",
        "trash_font_size": 22,
        "reset_size": (56, 60),
        "reset_icon": "\u21BA",
        "reset_font_size": 20,
        "reset_hover_fill": "#0c000000",     # 黑色 5% (AARRGGBB)
        "reset_hover_color": "#323232",
        "zone_radius": 8,
        # -- palette -------------------------------------------------------
        "danger": "#ea4335",
        "muted": "#b4b4b4",
        "mid": "#969696",
        # -- close button --------------------------------------------------
        "close_text": "\u00D7",
        "close_size": 18,
        "close_font_size": 15,
        "close_color": "#999999",
        "close_hover_color": "#333333",
        "close_tip": "关闭",
        "header_height": 20,
    }

    def __init__(self, fixed_length: int | None = None, spacing: int = 6,
                 style: dict | None = None, closable: bool = True,
                 vertical: bool = False,
                 parent: QWidget | None = None,
                 *, item_size: int | None = None,
                 icon_size: int | None = None,
                 label_font_size: int | None = None,
                 trash_size: tuple[int, int] | None = None,
                 reset_size: tuple[int, int] | None = None,
                 trash_icon: str | None = None,
                 reset_icon: str | None = None,
                 close_text: str | None = None,
                 show_trash: bool = True,
                 show_reset: bool = True):
        super().__init__(parent)
        self._vertical = vertical
        self._items: list[DragBarItem] = []
        self._widgets: dict[str, _DragItem] = {}
        self._selected: set[str] = set()
        self._last_clicked: str | None = None
        self._rubber_origin: QPoint | None = None
        self._rubber_rect: QRect | None = None
        self._drag_data: dict | None = None
        self._initial_data: list[dict] = []

        # One options dict drives every painter, so a single ``style=`` arg
        # (plus the convenience keywords below) re-skins the whole bar.
        self._style = dict(self.DEFAULT_STYLE)
        self._style["show_trash"] = bool(show_trash)
        self._style["show_reset"] = bool(show_reset)
        for key, value in (("item_size", item_size), ("icon_size", icon_size),
                           ("label_font_size", label_font_size),
                           ("trash_size", trash_size), ("reset_size", reset_size),
                           ("trash_icon", trash_icon), ("reset_icon", reset_icon),
                           ("close_text", close_text)):
            if value is not None:
                self._style[key] = value
        if style:
            self._style.update(style)

        # container with flow layout + drop forwarding
        self._flow_widget = _DropContainer(self)
        self._flow = _FlowLayout(self._flow_widget, vertical=vertical)
        self._flow.setSpacing(spacing)
        pad = int(self._style["padding"])
        self._flow.setContentsMargins(pad, pad, pad, pad)

        # trash / reset zones -- created from the same options dict
        self._trash = _TrashZone(self._style)
        self._trash.accepted.connect(self._on_trash_drop)
        if self._style["show_trash"]:
            self._flow.addWidget(self._trash)
        else:
            self._trash.hide()

        self._reset_zone = _ResetZone(self._style)
        self._reset_zone.clicked.connect(self._on_reset)
        if self._style["show_reset"]:
            self._flow.addWidget(self._reset_zone)
        else:
            self._reset_zone.hide()

        # scroll area
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        if vertical:
            self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        else:
            self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._scroll.setFrameShape(QFrame.NoFrame)
        self._scroll.setWidget(self._flow_widget)
        self._scroll.viewport().setAutoFillBackground(False)
        self._flow_widget.setAutoFillBackground(False)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # header row with close button
        if closable:
            self._header = QWidget()
            self._header.setFixedHeight(int(self._style["header_height"]))
            self._header.setAttribute(Qt.WA_TransparentForMouseEvents, True)
            hlay = QHBoxLayout(self._header)
            hlay.setContentsMargins(0, 0, 4, 0)
            hlay.addStretch()
            size = int(self._style["close_size"])
            self._close_btn = QPushButton(str(self._style["close_text"]),
                                          self._header)
            self._close_btn.setFixedSize(size, size)
            self._close_btn.setFlat(True)
            self._close_btn.setToolTip(str(self._style.get("close_tip", "关闭")))
            self._close_btn.setStyleSheet(f"""
                QPushButton {{
                    font-size: {self._style['close_font_size']}px;
                    font-weight: bold;
                    color: {self._style['close_color']};
                    background: transparent; border: none;
                }}
                QPushButton:hover {{ color: {self._style['close_hover_color']}; }}
            """)
            self._close_btn.setParent(self)
            self._close_btn.raise_()
            self._close_btn.clicked.connect(self._on_close)
            outer.addWidget(self._header)

        outer.addWidget(self._scroll)

        if fixed_length is not None:
            if vertical:
                self.setFixedHeight(fixed_length)
            else:
                self.setFixedWidth(fixed_length)

        self._apply_style()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_close_btn'):
            size = self._close_btn.width()
            self._close_btn.move(self.width() - size - 4, 2)

    # ── style ────────────────────────────────────────────────────────────

    def set_style(self, style: dict) -> None:
        """Merge *style* into the current options and re-skin the bar."""
        self._style.update(style)
        self._apply_style()
        for w in self._widgets.values():
            w.update()
        self._trash.update()
        self._reset_zone.update()

    def _apply_style(self):
        bg = self._style.get("background", "transparent")
        border = self._style.get("border", "none")
        radius = self._style.get("border_radius", 0)

        self.setStyleSheet(f"""
            background: {bg};
            border: {border};
            border-radius: {radius}px;
        """)

    # ── public API ──────────────────────────────────────────────────────

    def add_item(self, item: DragBarItem | str, text: str | None = None,
                 icon=None) -> DragBarItem | None:
        if isinstance(item, DragBarItem):
            pass  # use as-is
        else:
            item = DragBarItem(item, text or "", icon)
        if item.name in self._widgets:
            return None
        w = _DragItem(item, self._style, parent=self._flow_widget)
        w.dragRequested.connect(self._on_item_drag_requested)
        w.clicked.connect(self._on_item_clicked)
        item.icon_changed.connect(w.update)
        self._items.append(item)
        self._widgets[item.name] = w
        self._flow.insertWidget(self._flow.count() - 2, w)
        return item

    def insert_item(self, index: int, item: DragBarItem | str,
                    text: str | None = None, icon=None) -> DragBarItem | None:
        if isinstance(item, DragBarItem):
            pass
        else:
            item = DragBarItem(item, text or "", icon)
        if item.name in self._widgets:
            return None
        w = _DragItem(item, self._style, parent=self._flow_widget)
        w.dragRequested.connect(self._on_item_drag_requested)
        w.clicked.connect(self._on_item_clicked)
        item.icon_changed.connect(w.update)
        self._items.insert(index, item)
        self._widgets[item.name] = w
        self._flow.insertWidget(index, w)
        return item

    def remove_item(self, name: str) -> None:
        w = self._widgets.pop(name, None)
        if w is None:
            return
        self._items[:] = [it for it in self._items if it.name != name]
        self._selected.discard(name)
        idx = self._flow.indexOf(w)
        if idx >= 0:
            self._flow.takeAt(idx)
        w.setParent(None)
        w.deleteLater()

    @property
    def _names(self) -> list[str]:
        return [it.name for it in self._items]

    def clear(self) -> None:
        for name in list(self._widgets):
            self.remove_item(name)
        self._selected.clear()
        self._last_clicked = None

    def items(self) -> list[DragBarItem]:
        return list(self._items)

    def selected_items(self) -> list[str]:
        return [it.name for it in self._items if it.name in self._selected]

    def select_all(self) -> None:
        self._selected = set(self._names)
        self._update_selection()
        self.selection_changed.emit(list(self._selected))

    def deselect_all(self) -> None:
        self._selected.clear()
        self._update_selection()
        self.selection_changed.emit([])

    def set_spacing(self, spacing: int) -> None:
        self._flow.setSpacing(spacing)

    # ── snapshot / reset ────────────────────────────────────────────────

    def snapshot(self) -> None:
        """Save current items as the reset baseline."""
        self._initial_data = [
            {"name": it.name, "text": it.text,
             "icon_src": it._icon_src}
            for it in self._items
        ]

    def reset(self) -> None:
        """Restore the item list saved by the last :meth:`snapshot`."""
        self._on_reset()

    def _on_reset(self):
        if not self._initial_data:
            return
        self.clear()
        for d in self._initial_data:
            self.add_item(d["name"], d["text"], d["icon_src"] or None)

    # ── close ────────────────────────────────────────────────────────────

    def _on_close(self):
        self.closed.emit()
        self.hide()

    # ── selection ───────────────────────────────────────────────────────

    def _update_selection(self) -> None:
        for n, w in self._widgets.items():
            w.selected = n in self._selected
            w.update()

    def _on_item_clicked(self, name: str, ctrl: bool, shift: bool) -> None:
        names = self._names
        if ctrl:
            if name in self._selected:
                self._selected.discard(name)
            else:
                self._selected.add(name)
        elif shift and self._last_clicked and name != self._last_clicked:
            try:
                i0 = names.index(self._last_clicked)
                i1 = names.index(name)
            except ValueError:
                self._selected = {name}
            else:
                lo, hi = (i0, i1) if i0 < i1 else (i1, i0)
                self._selected = set(names[lo:hi + 1])
        else:
            self._selected = {name}

        self._last_clicked = name

        item = self._widgets.get(name)
        if item is not None:
            item._item.clicked.emit(ctrl, shift)
        self._update_selection()
        self.selection_changed.emit(list(self._selected))

    # ── drag initiation (from item) ─────────────────────────────────────

    def _on_item_drag_requested(self, clicked_name: str) -> None:
        names = list(self._selected) if self._selected else [clicked_name]
        if not names:
            return

        self._rubber_rect = None
        self._rubber_origin = None
        self._flow_widget.update()

        drag = QDrag(self)
        meta = {n: {"text": self._widgets[n]._item.text,
                     "icon": self._widgets[n]._item._icon_src}
                for n in names if n in self._widgets}
        mime = _mime_data(names, meta, id(self))
        drag.setMimeData(mime)

        widgets = [self._widgets[n] for n in names if n in self._widgets]
        if widgets:
            gap = int(self._style["drag_gap"])
            tw = sum(w.width() for w in widgets) + (len(widgets) - 1) * gap
            pm = QPixmap(tw, widgets[0].height())
            pm.fill(Qt.transparent)
            pp = QPainter(pm)
            x = 0
            for w in widgets:
                pp.drawPixmap(x, 0, w.grab())
                x += w.width() + gap
            pp.end()
            drag.setPixmap(pm)
            drag.setHotSpot(QPoint(0, 0))

        action = drag.exec(Qt.MoveAction | Qt.CopyAction)
        if action == Qt.MoveAction and self._drag_data is None:
            for n in list(names):
                if n in self._widgets:
                    self.remove_item(n)
                    self.item_removed.emit(n)
            self._selected &= set(self._widgets.keys())
            self._update_selection()
            self.selection_changed.emit(list(self._selected))

    # ── drop target (via _DropContainer) ────────────────────────────────

    def _has_name_conflict(self, data: dict) -> bool:
        if data.get("source_id") == id(self):
            return False
        for it in data.get("items", []):
            if it["name"] in self._widgets:
                return True
        return False

    def _on_drag_enter(self, event):
        data = _parse_mime(event)
        if data is None:
            event.ignore()
            return
        if self._has_name_conflict(data):
            event.ignore()
            return
        self._drag_data = data
        event.setDropAction(Qt.MoveAction)
        event.accept()

    def _on_drag_move(self, event):
        data = _parse_mime(event)
        if data is None:
            event.ignore()
            return
        if self._has_name_conflict(data):
            event.ignore()
            return
        event.setDropAction(Qt.MoveAction)
        event.accept()

    def _on_drag_leave(self, event):
        self._drag_data = None

    def _on_drop(self, event):
        data = _parse_mime(event)
        if data is None:
            event.ignore()
            return

        source_id = data.get("source_id")
        items_data = data.get("items", [])
        if not items_data:
            event.ignore()
            return

        local = event.position().toPoint()
        idx = self._drop_index(local)
        names = self._names
        same_bar = (source_id == id(self))

        if same_bar:
            moved_names = [it["name"] for it in items_data]
            moved_names = [n for n in moved_names if n in self._widgets]
            if not moved_names:
                event.ignore()
                return
            idx = min(idx, len(names))
            for n in moved_names:
                if n in names:
                    names.remove(n)
            if idx > len(names):
                idx = len(names)
            names[idx:idx] = moved_names
            # sync _items order
            self._items[:] = [self._widgets[n]._item for n in names]
            self._rebuild()
            self._selected = set(moved_names)
            self._update_selection()
            for n in moved_names:
                self.item_moved.emit(n, self._names.index(n))
            self.selection_changed.emit(list(self._selected))
        else:
            if self._has_name_conflict(data):
                self._drag_data = None
                event.ignore()
                return
            for it_data in items_data:
                n = it_data["name"]
                self.add_item(n, it_data["text"], it_data.get("icon") or None)
                names = self._names
                idx = min(idx, len(names))
                names.remove(n)
                if idx > len(names):
                    idx = len(names)
                names.insert(idx, n)
                self._items[:] = [self._widgets[n]._item for n in names]
            self._rebuild()
            self._selected = set()
            self._update_selection()
            self.selection_changed.emit(list(self._selected))

        event.setDropAction(Qt.MoveAction)
        event.accept()
        self._drag_data = None

    def _drop_index(self, local: QPoint) -> int:
        best = 0
        best_d = 1e9
        names = self._names
        for i, n in enumerate(names):
            cx = self._widgets[n].geometry().center()
            d = _manhattan_dist(local, cx)
            if d < best_d:
                best_d = d
                best = i
        return best

    # ── rebuild layout ──────────────────────────────────────────────────

    def _rebuild(self):
        for w in list(self._widgets.values()):
            idx = self._flow.indexOf(w)
            if idx >= 0:
                self._flow.takeAt(idx)
        for n in self._names:
            self._flow.addWidget(self._widgets[n])
        for fixed in (self._trash, self._reset_zone):
            idx = self._flow.indexOf(fixed)
            if idx >= 0:
                self._flow.takeAt(idx)
            self._flow.addWidget(fixed)
        self._flow_widget.update()
        self._flow.invalidate()
        self._flow.activate()

    # ── trash ───────────────────────────────────────────────────────────

    def _on_trash_drop(self, names: list[str]):
        for n in list(names):
            if n in self._widgets:
                self.remove_item(n)
                self.item_removed.emit(n)
        self._selected = {n for n in self._selected if n in self._widgets}
        self.selection_changed.emit(list(self._selected))

    # ── empty-area mouse: rubber band or deselect ───────────────────────

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._rubber_origin = event.position().toPoint()
            self._rubber_rect = None
            self.deselect_all()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton and self._rubber_origin is not None:
            d = _manhattan_dist(event.position().toPoint(), self._rubber_origin)
            if d > QApplication.startDragDistance():
                origin_flow = self._flow_widget.mapFrom(self, self._rubber_origin)
                pos_flow = self._flow_widget.mapFrom(self, event.position().toPoint())
                self._rubber_rect = QRect(origin_flow, pos_flow).normalized()
                self._flow_widget.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self._rubber_rect is not None:
                sel = set()
                for n, w in self._widgets.items():
                    if self._rubber_rect.intersects(w.geometry()):
                        sel.add(n)
                if sel:
                    self._selected = sel
                    self._update_selection()
                    self.selection_changed.emit(list(self._selected))
            self._rubber_rect = None
            self._rubber_origin = None
            self._flow_widget.update()
            event.accept()
            return
        super().mouseReleaseEvent(event)
