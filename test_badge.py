"""
Badge MVP
=========
运行 ``uv run python test_badge.py`` 弹出窗口演示小圆圈角标。
"""
import sys
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QHBoxLayout, QPushButton, QWidget
from widgets import Badge

app = QApplication(sys.argv)
app.setStyle("Fusion")

w = QWidget()
w.setWindowTitle("Badge 演示")
w.resize(400, 100)
v = QHBoxLayout(w)

btn = QPushButton("消息")
btn.resize(100, 36)
v.addWidget(btn)

badge = Badge(parent=btn)
badge.set_count(3)
badge.set_color("#1a73e8")

btn2 = QPushButton("告警")
v.addWidget(btn2)
badge2 = Badge(parent=btn2, color="#ea4335")
badge2.set_count(12)

btn3 = QPushButton("已完成")
v.addWidget(btn3)
badge3 = Badge(parent=btn3, color="#43a047")
badge3.set_count(99)

counter = 0

def update():
    global counter
    counter += 1
    badge.set_count(counter)
    if counter >= 20:
        timer.stop()

timer = QTimer()
timer.timeout.connect(update)
timer.start(500)

w.show()
sys.exit(app.exec())
