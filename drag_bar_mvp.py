"""DragBar MVP — 苹果风格 + DragBarItem + 横纵双向"""
import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QHBoxLayout, QWidget
from widgets import DragBar, DragBarItem

app = QApplication(sys.argv)
app.setStyle("Fusion")

w = QWidget()
w.setWindowTitle("DragBar MVP")
w.resize(520, 320)

style = {
    "background": "rgba(250, 250, 250, 0.88)",
    "border": "1px solid rgba(200, 200, 205, 0.5)",
    "border_radius": 10,
}

hbox = QHBoxLayout(w)
hbox.setSpacing(12)

# Horizontal bar (default)
bar_h = DragBar(spacing=8, style=style, closable=True)
for item in [
    DragBarItem("folder", "文件夹", "folder"),
    DragBarItem("calc", "计算器", "accessories-calculator"),
    DragBarItem("note", "记事本", "accessories-text-editor"),
]:
    bar_h.add_item(item)
bar_h.snapshot()
hbox.addWidget(bar_h)

# Vertical bar
bar_v = DragBar(spacing=8, style=style, closable=True, vertical=True)
for item in [
    DragBarItem("trash", "垃圾桶", "user-trash"),
    DragBarItem("gear", "设置", "preferences-system"),
    DragBarItem("info", "关于", "dialog-information"),
]:
    bar_v.add_item(item)
bar_v.snapshot()
hbox.addWidget(bar_v)

w.show()
sys.exit(app.exec())
