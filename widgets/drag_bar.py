from __future__ import annotations

import json
from PySide6.QtCore import QMimeData, QPoint, QRect, QSize, Qt, Signal
from PySide6.QtGui import (
    QColor, QDrag, QFont, QIcon, QMouseEvent, QPainter, QPen, QPixmap,
)
from PySide6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLabel, QLayout, QScrollArea,
    QVBoxLayout, QWidget, QWidgetItem,
)

_MIME = "application/x-dragbar-items"


def _manhattan_dist(a: QPoint, b: QPoint) -> int:
    """Manhattan length between two QPoints (avoids PySide6 QPoint.__sub__ bug)."""
    return abs(a.x() - b.x()) + abs(a.y() - b.y())


# ── helpers ─────────────────────────────────────────────────────────────

def _mime_data(names, items_meta, source_id: int) -> QMimeData:
    """Build MIME data for a drag operation."""
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
        parsed = _parse_mime(event)
        if parsed:
            names = [it["name"] for it in parsed["items"]]
            self.accepted.emit(names)
        event.acceptProposedAction()


# ── Drop container (hosts flow layout, forwards drag events) ────────────

class _DropContainer(QWidget):
    """Widget that accepts drops and delegates to the owning DragBar."""

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


# ── DragBar item ────────────────────────────────────────────────────────

class _DragItem(QWidget):
    clicked = Signal(str, bool, bool)  # name, ctrl, shift
    dragRequested = Signal(str)

    def __init__(self, name: str, text: str, icon=None, parent=None):
        super().__init__(parent)
        self._name = name
        self._text = text
        self._icon_src = ""
        self._icon = QIcon()
        if icon is not None:
            if isinstance(icon, str):
                self._icon_src = icon
                self._icon = QIcon.fromTheme(icon)
                if self._icon.isNull():
                    self._icon = QIcon(icon)
            else:
                self._icon = icon
        self.selected = False
        self._hovered = False
        self.setFixedSize(64, 64)
        self.setCursor(Qt.OpenHandCursor)
        self.setMouseTracking(True)
        self.setToolTip(text)
        self._drag_start: QPoint | None = None

    def sizeHint(self):
        return QSize(64, 64)

    @property
    def name(self):
        return self._name

    @property
    def icon_src(self) -> str:
        return self._icon_src

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

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._drag_start = event.position().toPoint()
            mod = QApplication.keyboardModifiers()
            self.clicked.emit(
                self._name,
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
                self.dragRequested.emit(self._name)
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

    支持同一 Bar 内拖拽排序、跨 Bar 拖拽、多选、回收站删除。

    Signals
    -------
    item_moved(name, new_index)
    item_removed(name)
    selection_changed([names...])
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
        self._rubber_origin: QPoint | None = None
        self._rubber_rect: QRect | None = None
        self._drag_data: dict | None = None

        # container with flow layout + drop forwarding
        self._flow_widget = _DropContainer(self)
        self._flow = _FlowLayout(self._flow_widget)
        self._flow.setSpacing(spacing)
        self._flow.setContentsMargins(4, 4, 4, 4)

        # trash
        self._trash = _TrashZone()
        self._trash.accepted.connect(self._on_trash_drop)
        self._flow.addWidget(self._trash)

        # scroll area
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
        w.dragRequested.connect(self._on_item_drag_requested)
        w.clicked.connect(self._on_item_clicked)
        self._names.append(name)
        self._widgets[name] = w
        self._flow.insertWidget(self._flow.count() - 1, w)

    def insert_item(self, index: int, name: str, text: str, icon=None) -> None:
        if name in self._widgets:
            return
        w = _DragItem(name, text, icon, parent=self._flow_widget)
        w.dragRequested.connect(self._on_item_drag_requested)
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

    def set_spacing(self, spacing: int) -> None:
        self._spacing = spacing
        self._flow.setSpacing(spacing)

    # ── selection ───────────────────────────────────────────────────────

    def _update_selection(self) -> None:
        for n, w in self._widgets.items():
            w.selected = n in self._selected
            w.update()

    def _on_item_clicked(self, name: str, ctrl: bool, shift: bool) -> None:
        if ctrl:
            if name in self._selected:
                self._selected.discard(name)
            else:
                self._selected.add(name)
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

    # ── drag initiation (from item) ─────────────────────────────────────

    def _on_item_drag_requested(self, clicked_name: str) -> None:
        names = list(self._selected) if self._selected else [clicked_name]
        if not names:
            return

        # clear any leftover rubber band state
        self._rubber_rect = None
        self._rubber_origin = None
        self._flow_widget.update()

        drag = QDrag(self)
        meta = {n: {"text": self._widgets[n]._text,
                     "icon": self._widgets[n]._icon_src}
                for n in names if n in self._widgets}
        mime = _mime_data(names, meta, id(self))
        drag.setMimeData(mime)

        # composite pixmap
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

        action = drag.exec(Qt.MoveAction | Qt.CopyAction)
        if action == Qt.MoveAction and self._drag_data is None:
            # Successful move to a different bar → source items already
            # handled via dropEvent on the target; but if the drag was
            # accepted but we never got a drop on a DIFFERENT bar,
            # we do nothing. The source items stay.
            pass

    # ── drop target (via _DropContainer) ────────────────────────────────

    def _on_drag_enter(self, event):
        data = _parse_mime(event)
        if data is None:
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

        # drop position (already in _flow_widget coords)
        local = event.position().toPoint()
        idx = self._drop_index(local)

        same_bar = (source_id == id(self))

        if same_bar:
            # Reorder within same bar
            names = [it["name"] for it in items_data]
            names = [n for n in names if n in self._widgets]
            if not names:
                event.ignore()
                return
            idx = min(idx, len(self._names))
            for n in names:
                if n in self._names:
                    self._names.remove(n)
            if idx > len(self._names):
                idx = len(self._names)
            self._names[idx:idx] = names
            self._rebuild()
            self._selected = set(names)
            self._update_selection()
            for n in names:
                self.item_moved.emit(n, self._names.index(n))
            self.selection_changed.emit(list(self._selected))
        else:
            # Cross-bar: copy items into this bar
            for it_data in items_data:
                n = it_data["name"]
                # avoid name clash
                if n in self._widgets:
                    n = self._unique_name(n)
                self.add_item(n, it_data["text"], it_data.get("icon") or None)
                idx = min(idx, len(self._names))
                # move to drop position
                self._names.remove(n)
                if idx > len(self._names):
                    idx = len(self._names)
                self._names.insert(idx, n)
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
        for i, n in enumerate(self._names):
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
        tidx = self._flow.indexOf(self._trash)
        if tidx >= 0:
            self._flow.takeAt(tidx)
        self._flow.addWidget(self._trash)
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

    # ── helpers ─────────────────────────────────────────────────────────

    def _unique_name(self, base: str) -> str:
        i = 1
        while f"{base}_{i}" in self._widgets:
            i += 1
        return f"{base}_{i}"

    # ── empty-area mouse: rubber band or deselect ───────────────────────

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._rubber_origin = event.position().toPoint()  # DragBar coords
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
