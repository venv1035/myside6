"""DragBar MVP — 苹果风格 + DragBarItem + 横纵双向 + 运行时换肤"""
import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QHBoxLayout, QPushButton, QVBoxLayout, QWidget,
)
from widgets import DragBar, DragBarItem

app = QApplication(sys.argv)
app.setStyle("Fusion")

w = QWidget()
w.setWindowTitle("DragBar MVP")
w.resize(520, 380)

root = QVBoxLayout(w)

hbox = QHBoxLayout()
hbox.setSpacing(12)

# Horizontal bar
bar_h = DragBar(spacing=8, style={
    "background": "rgba(250, 250, 250, 0.88)",
    "border": "1px solid rgba(200, 200, 205, 0.5)",
    "border_radius": 10,
}, closable=True)
for item in [
    DragBarItem("folder", "文件夹", "folder"),
    DragBarItem("calc", "计算器", "accessories-calculator"),
    DragBarItem("note", "记事本", "accessories-text-editor"),
]:
    bar_h.add_item(item)
bar_h.snapshot()
hbox.addWidget(bar_h)

# Vertical bar
bar_v = DragBar(spacing=8, style={
    "background": "rgba(250, 250, 250, 0.88)",
    "border": "1px solid rgba(200, 200, 205, 0.5)",
    "border_radius": 10,
}, closable=True, vertical=True)
for item in [
    DragBarItem("trash", "垃圾桶", "user-trash"),
    DragBarItem("gear", "设置", "preferences-system"),
    DragBarItem("info", "关于", "dialog-information"),
]:
    bar_v.add_item(item)
bar_v.snapshot()
hbox.addWidget(bar_v)

root.addLayout(hbox)

# Style switcher
btn = QPushButton("切换淡红边框 + 淡蓝透明背景")
def switch_style():
    s = {
        "background": "rgba(100, 150, 255, 0.25)",
        "border": "1px solid rgba(255, 100, 100, 0.5)",
        "border_radius": 10,
    }
    bar_h.set_style(s)
    bar_v.set_style(s)
btn.clicked.connect(switch_style)
root.addWidget(btn)

w.show()
sys.exit(app.exec())
