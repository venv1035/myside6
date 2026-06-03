"""Badge MVP — 最小可运行示例"""
import sys
from PySide6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget
from widgets import Badge

app = QApplication(sys.argv)
w = QWidget()
w.setWindowTitle("Badge MVP")

items = ["a", "b", "c"]

btn = QPushButton("点击添加")
btn_clr = QPushButton("清空")

v = QVBoxLayout(w)
v.addWidget(btn)
v.addWidget(btn_clr)
v.addStretch()

Badge(target=btn).bind(lambda: len(items))

btn.clicked.connect(lambda: items.append(f"x{len(items)}"))
btn_clr.clicked.connect(items.clear)

w.show()
sys.exit(app.exec())
