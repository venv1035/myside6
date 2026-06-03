from __future__ import annotations

from PySide6.QtCore import QEvent, QPoint, QRect, Qt, Signal
from PySide6.QtGui import QColor, QFontMetrics, QPainter, QPen
from PySide6.QtWidgets import QWidget


class Badge(QWidget):
    """A small coloured circle with a number, attached to the top-right corner
    of a target widget (typically a ``QPushButton`` or ``QToolButton``).

    The badge is **not** parented to the target — it is parented to the nearest
    top-level window so it is never clipped by the target's bounds.

    Usage::

        badge = Badge(target=button, color="#ea4335")
        badge.set_count(5)

        # Bind to a signal for live updates
        some_signal.connect(badge.set_count)
    """

    def __init__(self, target: QWidget | None = None,
                 *, color: str = "#ea4335",
                 text_color: str = "#ffffff",
                 max_count: int = 99,
                 size: int = 20) -> None:
        # Parent to the top-level window so we aren't clipped.
        win = self._find_window(target)
        super().__init__(win)
        self._target = target
        self._count = 0
        self._max_count = max_count
        self._size = size
        self._color = QColor(color)
        self._text_color = QColor(text_color)

        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setVisible(False)

        if target is not None:
            target.installEventFilter(self)

    # ---- public API -------------------------------------------------------

    def set_count(self, count: int) -> None:
        """Set the badge number. Hidden when ``count <= 0``."""
        self._count = count
        self.setVisible(count > 0)
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
        self.update()

    # ---- internal ---------------------------------------------------------

    @staticmethod
    def _find_window(w: QWidget | None) -> QWidget | None:
        if w is None:
            return None
        while w.parentWidget() is not None:
            w = w.parentWidget()
        return w

    def _reposition(self) -> None:
        t = self._target
        p = self.parentWidget()
        if t is None or p is None:
            return
        # top-right corner of target in this badge's parent coordinates
        tr = t.mapTo(p, QPoint(t.width(), 0))
        s = self._size
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

        # filled circle
        painter.setPen(Qt.NoPen)
        painter.setBrush(self._color)
        painter.drawEllipse(r.adjusted(1, 1, -1, -1))

        # text
        text = (str(self._count)
                if self._count <= self._max_count
                else f"{self._max_count}+")
        painter.setPen(self._text_color)
        painter.drawText(r, Qt.AlignCenter, text)
