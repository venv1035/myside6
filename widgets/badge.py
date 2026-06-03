from __future__ import annotations

from PySide6.QtCore import QAbstractItemModel, QEvent, QPoint, Qt
from PySide6.QtGui import QColor, QFontMetrics, QPainter
from PySide6.QtWidgets import QWidget


class Badge(QWidget):
    """A small coloured badge attached to the top-right corner of a target
    widget (typically a ``QPushButton`` or ``QToolButton``).

    The badge auto-sizes: wider when the number has more digits.

    The badge is **not** parented to the target — it is parented to the nearest
    top-level window so it is never clipped by the target's bounds.

    Usage::

        badge = Badge(target=button, color="#ea4335")
        badge.set_count(5)

        # Bind to a model — auto-tracks rowCount changes
        badge.bind(table.sourceModel())

        # Bind to any sized object (static)
        badge.bind(my_list)
        badge.bind("chars")

        # Chained in constructor
        Badge(target=btn).bind(model)
    """

    def __init__(self, target: QWidget | None = None,
                 *, color: str = "#ea4335",
                 text_color: str = "#ffffff",
                 max_count: int = 999,
                 min_size: int = 20) -> None:
        # Parent to the top-level window so we aren't clipped.
        win = self._find_window(target)
        super().__init__(win)
        self._target = target
        self._count = 0
        self._max_count = max_count
        self._min_size = min_size
        self._current_diameter = min_size
        self._color = QColor(color)
        self._text_color = QColor(text_color)
        self._source = None

        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setVisible(False)

        if target is not None:
            target.installEventFilter(self)

    # ---- public API -------------------------------------------------------

    def set_count(self, count: int) -> None:
        """Set the badge number. Hidden when ``count <= 0``."""
        self._count = count
        self.setVisible(count > 0)
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

        ====================  ============================================
        ``source`` type       Behaviour
        ====================  ============================================
        ``QAbstractItemModel`` Auto-track ``rowCount()`` via ``rowsInserted`` /
                               ``rowsRemoved`` / ``modelReset`` signals.
        ``list``, ``str`` …   Static ``len(source)`` (no auto-update).
        ``callable``          ``source()`` is called each sync.
        ====================  ============================================
        """
        self._unbind()
        self._source = source
        if isinstance(source, QAbstractItemModel):
            source.rowsInserted.connect(self._sync)
            source.rowsRemoved.connect(self._sync)
            source.modelReset.connect(self._sync)
        self._sync()
        return self

    # ---- internal ---------------------------------------------------------

    def _unbind(self) -> None:
        src = self._source
        if isinstance(src, QAbstractItemModel):
            try:
                src.rowsInserted.disconnect(self._sync)
            except RuntimeError:
                pass
            try:
                src.rowsRemoved.disconnect(self._sync)
            except RuntimeError:
                pass
            try:
                src.modelReset.disconnect(self._sync)
            except RuntimeError:
                pass
        self._source = None

    def _sync(self) -> None:
        src = self._source
        if src is None:
            return
        if isinstance(src, QAbstractItemModel):
            self.set_count(src.rowCount())
        elif callable(src):
            self.set_count(src())
        elif hasattr(src, "__len__"):
            self.set_count(len(src))
        else:
            self.set_count(0)

    @staticmethod
    def _find_window(w: QWidget | None) -> QWidget | None:
        if w is None:
            return None
        while w.parentWidget() is not None:
            w = w.parentWidget()
        return w

    def _display_text(self) -> str:
        if self._count <= 0:
            return ""
        if self._count <= self._max_count:
            return str(self._count)
        return f"{self._max_count}+"

    def _calc_diameter(self) -> int:
        text = self._display_text()
        if not text:
            return 0
        fm = QFontMetrics(self.font())
        tw = fm.horizontalAdvance(text)
        return max(self._min_size, tw + 8)

    def _update_size(self) -> None:
        self._current_diameter = max(self._calc_diameter(), self._min_size)

    def _reposition(self) -> None:
        t = self._target
        p = self.parentWidget()
        if t is None or p is None:
            return
        tr = t.mapTo(p, QPoint(t.width(), 0))
        s = self._current_diameter
        self.setGeometry(tr.x() - s // 2, tr.y() - s // 2, s, s)
        self.raise_()

    def eventFilter(self, obj: QWidget, event: QEvent) -> bool:
        if obj is self._target and event.type() in (QEvent.Resize, QEvent.Move):
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
