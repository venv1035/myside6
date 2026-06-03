"""DragBar MVP — 苹果风格 + DragBarItem"""
import sys
from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget
from widgets import DragBar, DragBarItem

app = QApplication(sys.argv)
app.setStyle("Fusion")

w = QWidget()
w.setWindowTitle("DragBar MVP")
w.resize(400, 140)

style = {
    "background": "rgba(250, 250, 250, 0.88)",
    "border": "1px solid rgba(200, 200, 205, 0.5)",
    "border_radius": 10,
}

bar = DragBar(spacing=8, style=style, closable=True)
for item in [
    DragBarItem("folder", "文件夹", "folder"),
    DragBarItem("calc", "计算器", "accessories-calculator"),
    DragBarItem("note", "记事本", "accessories-text-editor"),
]:
    bar.add_item(item)
bar.snapshot()

v = QVBoxLayout(w)
v.addWidget(bar)
w.show()
sys.exit(app.exec())
