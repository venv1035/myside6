from __future__ import annotations

import weakref

from PySide6.QtCore import QAbstractItemModel, QEvent, QObject, QPoint, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFontMetrics, QPainter
from PySide6.QtWidgets import QWidget


class Badge(QWidget):
    """A small coloured badge attached to the top-right corner of a target
    widget (typically a ``QPushButton`` or ``QToolButton``).

    The badge auto-sizes: wider when the number has more digits.

    The badge is **not** parented to the target — it is parented to the nearest
    top-level window so it is never clipped by the target's bounds.

    .. note::

       All badge instances are auto-polled by a 300 ms timer tied to the
       Qt event loop, so binding to a plain ``list`` / ``dict`` / ``str`` /
       ``callable`` will **just work** — no manual ``refresh()`` calls needed.

    Usage::

        badge = Badge(target=button, color="#ea4335")
        badge.set_count(5)

        # Auto-track a QAbstractItemModel (via Qt signals)
        badge.bind(table.sourceModel())

        # Bind to a plain list — auto-polled by the internal timer
        items = ["a", "b", "c"]
        Badge(target=btn).bind(items)      # → 3
        items.append("d")                  # → 4  (within ~300 ms)

        # Bind to a dict / string / callable — same automatic polling
        Badge(target=btn).bind({"a": 1})   # → 1
        Badge(target=btn).bind("hello")    # → 5
        Badge(target=btn).bind(counter_fn) # calls counter_fn()

        # Chained
        Badge(target=btn).bind(my_list)
    """

    # Weak references: a badge lives exactly as long as the widget tree it is
    # parented to.  A strong ``set`` would keep every closed window alive.
    _instances: "weakref.WeakSet[Badge]" = weakref.WeakSet()
    _timer: QTimer | None = None
    _poll_ms: int = 300

    def __init__(self, target: QWidget | None = None,
                 *, color: str = "#ea4335",
                 text_color: str = "#ffffff",
                 max_count: int = 999,
                 min_size: int = 20,
                 padding: int = 8,
                 font_size: int | None = None,
                 overflow_suffix: str = "+",
                 offset: tuple[int, int] = (0, 0),
                 poll_ms: int | None = None) -> None:
        # Parent to the top-level window so we aren't clipped.
        # ``target.window()`` returns *target itself* while it is not yet
        # inside a window (e.g. the page widget has been built but not added
        # to the tab widget).  Parenting the badge to the target in that
        # situation clips it to a small corner sliver, so stay unparented and
        # wait for the target's Show event instead.
        win = target.window() if target is not None else None
        if win is target:
            win = None
        super().__init__(win)
        self._target = target
        self._count = 0
        self._max_count = max_count
        self._min_size = min_size
        self._padding = max(0, int(padding))
        self._overflow_suffix = overflow_suffix
        self._offset = QPoint(int(offset[0]), int(offset[1]))
        self._current_diameter = min_size
        self._color = QColor(color)
        self._text_color = QColor(text_color)
        self._source = None

        if font_size is not None:
            font = self.font()
            font.setPixelSize(int(font_size))
            self.setFont(font)

        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setVisible(False)

        # Register so the polling timer picks us up.
        Badge._instances.add(self)
        if poll_ms is not None:
            Badge.set_poll_interval(poll_ms)
        else:
            Badge._ensure_timer()

        if target is not None:
            target.installEventFilter(self)
            # Keep a strong reference on the *target* so a chained
            # ``Badge(target=btn).bind(items)`` is not garbage collected;
            # the badge then lives exactly as long as the widget tree.
            holders = getattr(target, "_badges", None)
            if holders is None:
                holders = []
                target._badges = holders
            holders.append(self)

    # ---- public API -------------------------------------------------------

    def set_count(self, count: int) -> None:
        """Set the badge number. Hidden when ``count <= 0``."""
        self._count = count
        self._update_size()
        self._reposition()
        self.update()

    count = property(lambda self: self._count, set_count)

    def set_color(self, color: str) -> None:
        self._color = QColor(color)
        self.update()

    def set_text_color(self, color: str) -> None:
        self._text_color = QColor(color)
        self.update()

    def set_max_count(self, max_count: int) -> None:
        self._max_count = max_count
        self._update_size()
        self._reposition()
        self.update()

    def bind(self, source) -> Badge:
        """Bind the badge count to *source*. Returns ``self`` for chaining.

        ======================  =============================================
        ``source`` type         Behaviour
        ======================  =============================================
        ``QAbstractItemModel``  Auto-track ``rowCount()`` via Qt signals.
        Any object with a       Auto-track via ``changed`` signal.
        ``changed`` signal
        ``list``, ``dict``,     No signals — the internal polling timer
        ``str``, ``callable``…  re-reads every ~300 ms automatically.
        ======================  =============================================
        """
        self._unbind()
        self._source = source
        if isinstance(source, QAbstractItemModel):
            source.rowsInserted.connect(self._sync)
            source.rowsRemoved.connect(self._sync)
            source.modelReset.connect(self._sync)
        elif hasattr(source, "changed"):
            try:
                source.changed.connect(self._sync)
            except (TypeError, RuntimeError):
                pass
        self._sync()
        return self

    def refresh(self) -> None:
        """Immediately re-read the bound source and update the badge count."""
        self._sync()

    # ---- class-level polling ----------------------------------------------

    @classmethod
    def set_poll_interval(cls, ms: int) -> None:
        """Change the shared polling interval (applies to every badge)."""
        cls._poll_ms = max(16, int(ms))
        cls._ensure_timer()
        if cls._timer is not None:
            cls._timer.start(cls._poll_ms)

    @classmethod
    def _ensure_timer(cls) -> None:
        if cls._timer is None:
            cls._timer = QTimer()
            cls._timer.timeout.connect(cls._poll_all)
            cls._timer.start(cls._poll_ms)

    @classmethod
    def _poll_all(cls) -> None:
        for badge in list(cls._instances):
            badge._sync()

    # ---- internal ---------------------------------------------------------

    def _unbind(self) -> None:
        src = self._source
        if src is None:
            return
        if isinstance(src, QAbstractItemModel):
            for sig in ("rowsInserted", "rowsRemoved", "modelReset"):
                try:
                    getattr(src, sig).disconnect(self._sync)
                except RuntimeError:
                    pass
        elif hasattr(src, "changed"):
            try:
                src.changed.disconnect(self._sync)
            except (RuntimeError, TypeError):
                pass
        self._source = None

    def _sync(self) -> None:
        src = self._source
        if src is None:
            return
        new = self._read_count(src)
        if new != self._count:
            self.set_count(new)

    @staticmethod
    def _read_count(src) -> int:
        if isinstance(src, QAbstractItemModel):
            return src.rowCount()
        if callable(src):
            return src()
        if isinstance(src, int):
            return max(0, src)
        if hasattr(src, "__len__"):
            return len(src)
        return 0

    def _display_text(self) -> str:
        if self._count <= 0:
            return ""
        if self._count <= self._max_count:
            return str(self._count)
        return f"{self._max_count}{self._overflow_suffix}"

    def _calc_diameter(self) -> int:
        text = self._display_text()
        if not text:
            return 0
        fm = QFontMetrics(self.font())
        tw = fm.horizontalAdvance(text)
        return max(self._min_size, tw + self._padding)

    def _update_size(self) -> None:
        self._current_diameter = max(self._calc_diameter(), self._min_size)

    def _reposition(self) -> None:
        t = self._target
        if t is None:
            return
        win = t.window()
        if win is None or win is t:
            # Target is not inside a window yet (page built but not added to
            # a tab / central widget).  Stay hidden instead of flashing as a
            # floating window; the target's Show event brings us back.
            self.setVisible(False)
            return
        if self.parentWidget() is not win:
            # Corrects the case where the badge was created before the target
            # had a window: it would otherwise stay clipped inside the target.
            self.setParent(win)
        # The badge lives on the top-level window, so it does not hide itself
        # when the target's page (another tab) is switched away -- follow the
        # target's effective visibility explicitly.
        self.setVisible(self._count > 0 and t.isVisible())
        tr = t.mapTo(win, QPoint(t.width(), 0))
        s = self._current_diameter
        self.setGeometry(tr.x() - s // 2 + self._offset.x(),
                         tr.y() - s // 2 + self._offset.y(), s, s)
        self.raise_()

    def eventFilter(self, obj: QWidget, event: QEvent) -> bool:
        if obj is self._target and event.type() in (
                QEvent.Resize, QEvent.Move, QEvent.Show, QEvent.Hide,
                QEvent.ParentChange):
            self._reposition()
        return super().eventFilter(obj, event)

    def paintEvent(self, event) -> None:
        if self._count <= 0:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        r = self.rect()
        body = r.adjusted(1, 1, -1, -1)

        # pill shape when wider than tall, circle otherwise
        painter.setPen(Qt.NoPen)
        painter.setBrush(self._color)
        if body.width() > body.height():
            painter.drawRoundedRect(body, body.height() // 2, body.height() // 2)
        else:
            painter.drawEllipse(body)

        text = self._display_text()
        painter.setPen(self._text_color)
        painter.drawText(r, Qt.AlignCenter, text)


class BadgeList(QObject):
    """A ``list`` wrapper that emits ``changed`` on every mutation.

    Useful when you want **instant** (rather than timer-polled) badge updates.
    If timer-polling at ~300 ms is acceptable, a plain ``list`` works too.

    Usage with :meth:`Badge.bind`::

        items = BadgeList(["a", "b", "c"])
        Badge(target=btn).bind(items)    # → 3
        items.append("d")                # badge instant → 4
    """

    changed = Signal()

    def __init__(self, items=None, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._data = list(items) if items is not None else []

    def __len__(self) -> int:
        return len(self._data)

    def __iter__(self):
        return iter(self._data)

    def __getitem__(self, index):
        return self._data[index]

    def __contains__(self, item) -> bool:
        return item in self._data

    def __repr__(self) -> str:
        return repr(self._data)

    def __bool__(self) -> bool:
        return bool(self._data)

    def __iadd__(self, items):
        self._data += list(items)
        self.changed.emit()
        return self

    def __setitem__(self, index, value) -> None:
        self._data[index] = value
        self.changed.emit()

    def __delitem__(self, index) -> None:
        del self._data[index]
        self.changed.emit()

    def count(self, item) -> int:
        return self._data.count(item)

    def index(self, item, *args) -> int:
        return self._data.index(item, *args)

    def append(self, item) -> None:
        self._data.append(item)
        self.changed.emit()

    def extend(self, items) -> None:
        self._data.extend(items)
        self.changed.emit()

    def insert(self, index, item) -> None:
        self._data.insert(index, item)
        self.changed.emit()

    def remove(self, item) -> None:
        self._data.remove(item)
        self.changed.emit()

    def pop(self, index=-1):
        val = self._data.pop(index)
        self.changed.emit()
        return val

    def clear(self) -> None:
        self._data.clear()
        self.changed.emit()

    def sort(self, *, key=None, reverse=False) -> None:
        self._data.sort(key=key, reverse=reverse)
        self.changed.emit()

    def reverse(self) -> None:
        self._data.reverse()
        self.changed.emit()


class BadgeDict(QObject):
    """A ``dict`` wrapper that emits ``changed`` on every mutation.

    Useful when you want **instant** (rather than timer-polled) badge updates.
    If timer-polling at ~300 ms is acceptable, a plain ``dict`` works too.

    Usage with :meth:`Badge.bind`::

        d = BadgeDict({"alice": 90, "bob": 85})
        Badge(target=btn).bind(d)          # → 2
        d["charlie"] = 95                  # badge instant → 3
    """

    changed = Signal()

    def __init__(self, items=None, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._data = dict(items) if items is not None else {}

    def __len__(self) -> int:
        return len(self._data)

    def __iter__(self):
        return iter(self._data)

    def __getitem__(self, key):
        return self._data[key]

    def __contains__(self, key) -> bool:
        return key in self._data

    def __repr__(self) -> str:
        return repr(self._data)

    def __setitem__(self, key, value) -> None:
        self._data[key] = value
        self.changed.emit()

    def __delitem__(self, key) -> None:
        del self._data[key]
        self.changed.emit()

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def items(self):
        return self._data.items()

    def get(self, key, default=None):
        return self._data.get(key, default)

    def clear(self) -> None:
        self._data.clear()
        self.changed.emit()

    def update(self, *args, **kwargs) -> None:
        self._data.update(*args, **kwargs)
        self.changed.emit()

    def setdefault(self, key, default=None):
        val = self._data.setdefault(key, default)
        self.changed.emit()
        return val

    def pop(self, key, *args):
        val = self._data.pop(key, *args)
        self.changed.emit()
        return val

    def popitem(self):
        val = self._data.popitem()
        self.changed.emit()
        return val
