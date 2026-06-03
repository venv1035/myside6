"""DragBar MVP — 苹果风格 + DragBarItem + 横纵双向 + 运行时换肤 + 点击事件"""
import sys
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QApplication, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
)
from widgets import DragBar, DragBarItem

app = QApplication(sys.argv)
app.setStyle("Fusion")

w = QWidget()
w.setWindowTitle("DragBar MVP")
w.resize(520, 420)

root = QVBoxLayout(w)

hbox = QHBoxLayout()
hbox.setSpacing(12)

style = {
    "background": "rgba(250, 250, 250, 0.88)",
    "border": "1px solid rgba(200, 200, 205, 0.5)",
    "border_radius": 10,
}

log = QLabel("点击 item 查看…")
root.addWidget(log)

# Horizontal bar
bar_h = DragBar(spacing=8, style=style, closable=True)
for data in [
    ("folder", "文件夹", "folder"),
    ("calc", "计算器", "accessories-calculator"),
    ("note", "记事本", "accessories-text-editor"),
]:
    item = DragBarItem(*data)
    item.clicked.connect(lambda c, s, n=data[0]: log.setText(f"点击: {n}  ctrl={c} shift={s}"))
    bar_h.add_item(item)
bar_h.snapshot()
hbox.addWidget(bar_h)

# Vertical bar
bar_v = DragBar(spacing=8, style=style, closable=True, vertical=True)
for data in [
    ("trash", "垃圾桶", "user-trash"),
    ("gear", "设置", "preferences-system"),
    ("info", "关于", "dialog-information"),
]:
    item = DragBarItem(*data)
    item.clicked.connect(lambda c, s, n=data[0]: log.setText(f"点击: {n}  ctrl={c} shift={s}"))
    bar_v.add_item(item)
bar_v.snapshot()
hbox.addWidget(bar_v)

root.addLayout(hbox)

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
