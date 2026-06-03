from __future__ import annotations

from PySide6.QtCore import QMimeData, QPoint, QRect, QSize, Qt, Signal
from PySide6.QtGui import (
    QColor, QDrag, QFont, QIcon, QPainter, QPen, QPixmap,
)
from PySide6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLabel, QLayout, QScrollArea,
    QSizePolicy, QVBoxLayout, QWidget, QWidgetItem,
)


_MIME = "application/x-dragbar-items"


# ── FlowLayout ──────────────────────────────────────────────────────────

class _FlowLayout(QLayout):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._items: list[QLayoutItem] = []

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
        return True

    def heightForWidth(self, w):
        return self._layout(QRect(0, 0, w, 0), False)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._layout(rect, True)

    def sizeHint(self):
        s = QSize()
        for it in self._items:
            s = s.expandedTo(it.minimumSize())
        m = self.contentsMargins()
        return QSize(200, s.height() + m.top() + m.bottom())

    def minimumSize(self):
        s = QSize()
        for it in self._items:
            s = s.expandedTo(it.minimumSize())
        m = self.contentsMargins()
        return QSize(s.width() + m.left() + m.right(),
                     s.height() + m.top() + m.bottom())

    def _layout(self, rect, set_geo):
        m = self.contentsMargins()
        x = rect.x() + m.left()
        y = rect.y() + m.top()
        row_h = 0
        gap = self.spacing()
        right = rect.right() - m.right()

        for it in self._items:
            w = it.widget()
            if w and not w.isVisible():
                continue
            hint = it.sizeHint()
            if x + hint.width() > right and x > rect.x() + m.left():
                x = rect.x() + m.left()
                y += row_h + gap
                row_h = 0
            if set_geo:
                it.setGeometry(QRect(QPoint(x, y), hint))
            x += hint.width() + gap
            row_h = max(row_h, hint.height())

        return y + row_h - rect.y() + m.bottom()


# ── Trash zone ──────────────────────────────────────────────────────────

class _TrashZone(QWidget):
    accepted = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._over = False
        self.setAcceptDrops(True)
        self.setFixedSize(56, 60)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        if self._over:
            p.setBrush(QColor(234, 67, 53, 30))
            p.setPen(QPen(QColor(234, 67, 53), 2))
            p.drawRoundedRect(self.rect().adjusted(2, 2, -2, -2), 8, 8)
        p.setPen(QColor(180, 180, 180) if not self._over else QColor(234, 67, 53))
        font = QFont("Segoe UI Symbol", 22)
        p.setFont(font)
        p.drawText(self.rect(), Qt.AlignCenter, "\U0001F5D1")

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
        raw = event.mimeData().data(_MIME).data().decode("utf-8")
        names = raw.split(",") if raw else []
        if names:
            self.accepted.emit(names)
        event.acceptProposedAction()


# ── DragBar item ────────────────────────────────────────────────────────

class _DragItem(QWidget):
    clicked = Signal(str, bool, bool)  # name, ctrl, shift
    dragRequested = Signal(str)

    def __init__(self, name: str, text: str, icon=None, parent=None):
        super().__init__(parent)
        self._name = name
        self._text = text
        self._icon = QIcon()
        if icon is not None:
            self._icon = QIcon(icon) if isinstance(icon, str) else icon
        self.selected = False
        self._hovered = False
        self.setFixedSize(64, 64)
        self.setCursor(Qt.OpenHandCursor)
        self.setMouseTracking(True)
        self.setToolTip(text)

    @property
    def name(self):
        return self._name

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = self.rect().adjusted(2, 2, -2, -2)

        if self.selected:
            p.setBrush(QColor(26, 115, 232, 35))
            p.setPen(QPen(QColor(26, 115, 232), 2))
            p.drawRoundedRect(r, 8, 8)
        elif self._hovered:
            p.setBrush(QColor(0, 0, 0, 10))
            p.setPen(Qt.NoPen)
            p.drawRoundedRect(r, 8, 8)

        sz = 28
        if not self._icon.isNull():
            px = self._icon.pixmap(sz, sz)
            ix = (self.width() - sz) // 2
            p.drawPixmap(ix, 6, px)
        else:
            p.setPen(QColor(180, 180, 180))
            font = QFont("Segoe UI Symbol", 18)
            p.setFont(font)
            p.drawText(QRect(0, 4, self.width(), sz + 4), Qt.AlignCenter, "\U0001F4C4")

        p.setPen(QColor(50, 50, 50))
        font = QFont(self.font())
        font.setPointSize(8)
        p.setFont(font)
        p.drawText(QRect(0, 40, self.width(), 22), Qt.AlignCenter, self._text)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_start = event.position().toPoint()
            mod = QApplication.keyboardModifiers()
            self.clicked.emit(
                self._name,
                bool(mod & Qt.ControlModifier),
                bool(mod & Qt.ShiftModifier),
            )
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            d = (event.position().toPoint() - self._drag_start).manhattanLength()
            if d > QApplication.startDragDistance():
                self.dragRequested.emit(self._name)
        super().mouseMoveEvent(event)

    def enterEvent(self, event):
        self._hovered = True; self.update()

    def leaveEvent(self, event):
        self._hovered = False; self.update()


# ── DragBar ─────────────────────────────────────────────────────────────

class DragBar(QWidget):
    """可拖拽图标工具栏。

    Features
    --------
    • 每个元素有 ``name``（标识）、``text``（显示文字）、``icon``（图标）
    • 拖拽排序（支持单选／多选拖动）
    • 多选：**Ctrl**+单击 切换选中，**Shift**+单击 范围选中
    • 末尾回收站 — 将元素拖入即可删除
    • 可配置元素间距（``spacing``）
    • ``fixed_length=None`` 自动撑开；= 像素值时固定宽度，元素
      换行排列（FlowLayout）

    Usage ::

        bar = DragBar(spacing=8)
        bar.add_item("calc", "计算器", "calc.png")
        bar.add_item("note", "记事本", "note.png")
        bar.item_removed.connect(lambda n: print(f"已删除: {n}"))
        bar.item_moved.connect(lambda n, i: print(f"{n} 移到 {i}"))

    Signals
    -------
    item_moved(name, new_index)
    item_removed(name)
    selection_changed([names…])
    """

    item_moved = Signal(str, int)
    item_removed = Signal(str)
    selection_changed = Signal(list)

    def __init__(self, fixed_length: int | None = None, spacing: int = 6,
                 parent: QWidget | None = None):
        super().__init__(parent)
        self._spacing = spacing
        self._names: list[str] = []
        self._widgets: dict[str, _DragItem] = {}
        self._selected: set[str] = set()
        self._last_clicked: str | None = None

        # flow container
        self._flow_widget = QWidget()
        self._flow = _FlowLayout(self._flow_widget)
        self._flow.setSpacing(spacing)
        self._flow.setContentsMargins(4, 4, 4, 4)

        # trash (last item in flow)
        self._trash = _TrashZone()
        self._trash.accepted.connect(self._on_trash_drop)
        self._flow.addWidget(self._trash)

        # scroll area for overflow
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._scroll.setFrameShape(QFrame.NoFrame)
        self._scroll.setWidget(self._flow_widget)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self._scroll)

        if fixed_length is not None:
            self.setFixedWidth(fixed_length)

    # ── public API ──────────────────────────────────────────────────────

    def add_item(self, name: str, text: str, icon=None) -> None:
        if name in self._widgets:
            return
        w = _DragItem(name, text, icon, parent=self._flow_widget)
        w.dragRequested.connect(self._start_drag)
        w.clicked.connect(self._on_item_clicked)
        self._names.append(name)
        self._widgets[name] = w
        self._flow.insertWidget(self._flow.count() - 1, w)

    def insert_item(self, index: int, name: str, text: str, icon=None) -> None:
        if name in self._widgets:
            return
        w = _DragItem(name, text, icon, parent=self._flow_widget)
        w.dragRequested.connect(self._start_drag)
        w.clicked.connect(self._on_item_clicked)
        self._names.insert(index, name)
        self._widgets[name] = w
        self._flow.insertWidget(index, w)

    def remove_item(self, name: str) -> None:
        w = self._widgets.pop(name, None)
        if w is None:
            return
        self._names.remove(name)
        self._selected.discard(name)
        idx = self._flow.indexOf(w)
        if idx >= 0:
            self._flow.takeAt(idx)
        w.setParent(None)
        w.deleteLater()

    def clear(self) -> None:
        for name in list(self._names):
            self.remove_item(name)
        self._selected.clear()
        self._last_clicked = None

    def items(self) -> list[dict]:
        return [{"name": n, "text": self._widgets[n]._text,
                 "icon": self._widgets[n]._icon} for n in self._names]

    def selected_items(self) -> list[str]:
        return list(self._selected)

    def select_all(self) -> None:
        self._selected = set(self._names)
        self._update_selection()
        self.selection_changed.emit(list(self._selected))

    def deselect_all(self) -> None:
        self._selected.clear()
        self._update_selection()
        self.selection_changed.emit([])

    # ── selection ───────────────────────────────────────────────────────

    def _update_selection(self) -> None:
        for n, w in self._widgets.items():
            w.selected = n in self._selected
            w.update()

    def _on_item_clicked(self, name: str, ctrl: bool, shift: bool) -> None:
        if ctrl:
            self._selected.symmetric_difference_update([name])
        elif shift and self._last_clicked and name != self._last_clicked:
            try:
                i0 = self._names.index(self._last_clicked)
                i1 = self._names.index(name)
            except ValueError:
                self._selected = {name}
            else:
                lo, hi = (i0, i1) if i0 < i1 else (i1, i0)
                self._selected = set(self._names[lo:hi + 1])
        else:
            self._selected = {name}

        self._last_clicked = name
        self._update_selection()
        self.selection_changed.emit(list(self._selected))

    # ── drag ────────────────────────────────────────────────────────────

    def _start_drag(self, clicked_name: str) -> None:
        names = list(self._selected) if self._selected else [clicked_name]
        if not names:
            return

        drag = QDrag(self)
        mime = QMimeData()
        mime.setData(_MIME, ",".join(names).encode("utf-8"))
        drag.setMimeData(mime)

        # composite pixmap of selected items
        widgets = [self._widgets[n] for n in names if n in self._widgets]
        if widgets:
            tw = sum(w.width() for w in widgets) + (len(widgets) - 1) * 4
            pm = QPixmap(tw, widgets[0].height())
            pm.fill(Qt.transparent)
            pp = QPainter(pm)
            x = 0
            for w in widgets:
                pp.drawPixmap(x, 0, w.grab())
                x += w.width() + 4
            pp.end()
            drag.setPixmap(pm)
            drag.setHotSpot(QPoint(0, 0))

        drag.exec(Qt.MoveAction)

    # mouse events on empty area → deselect all
    def mousePressEvent(self, event):
        self._drag_start = event.position().toPoint()
        self.deselect_all()
        super().mousePressEvent(event)

    # ── drop ────────────────────────────────────────────────────────────

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(_MIME):
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat(_MIME):
            event.acceptProposedAction()

    def dropEvent(self, event):
        raw = event.mimeData().data(_MIME).data().decode("utf-8")
        names = raw.split(",") if raw else []
        names = [n for n in names if n in self._widgets]
        if not names:
            return

        # drop index
        local = self._flow_widget.mapFrom(self, event.position().toPoint())
        idx = self._drop_index(local)
        idx = min(idx, len(self._names))

        # remove from current positions, insert at idx
        for n in names:
            if n in self._names:
                self._names.remove(n)
        self._names[idx:idx] = names

        self._rebuild()
        self._selected = set(names)
        self._update_selection()

        for n in names:
            self.item_moved.emit(n, self._names.index(n))
        self.selection_changed.emit(list(self._selected))
        event.acceptProposedAction()

    def _drop_index(self, local: QPoint) -> int:
        best = 0
        best_d = 1e9
        for i, n in enumerate(self._names):
            cx = self._widgets[n].geometry().center()
            d = (local - cx).manhattanLength()
            if d < best_d:
                best_d = d
                best = i
        return best

    def _rebuild(self):
        # remove all widgets from flow layout
        for w in list(self._widgets.values()):
            idx = self._flow.indexOf(w)
            if idx >= 0:
                self._flow.takeAt(idx)
                w.setParent(self._flow_widget)  # keep alive
        # re-add in new order
        for n in self._names:
            self._flow.addWidget(self._widgets[n])
        # ensure trash is last
        tidx = self._flow.indexOf(self._trash)
        if tidx >= 0:
            self._flow.takeAt(tidx)
        self._flow.addWidget(self._trash)

    # ── trash ───────────────────────────────────────────────────────────

    def _on_trash_drop(self, names: list[str]):
        for n in list(names):
            if n in self._widgets:
                self.remove_item(n)
                self.item_removed.emit(n)
        self._selected = {n for n in self._selected if n in self._widgets}
        self.selection_changed.emit(list(self._selected))
