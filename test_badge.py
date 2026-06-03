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
w.resize(500, 100)
v = QHBoxLayout(w)

# 1 digit
btn1 = QPushButton("消息")
btn1.resize(100, 36)
v.addWidget(btn1)
Badge(target=btn1, color="#1a73e8").set_count(3)

# 2 digits
btn2 = QPushButton("未读")
v.addWidget(btn2)
Badge(target=btn2, color="#ea4335").set_count(42)

# 3 digits
btn3 = QPushButton("结果")
v.addWidget(btn3)
Badge(target=btn3, color="#43a047").set_count(200)

# 4 digits (beyond max_count, shows 999+)
btn4 = QPushButton("访问")
v.addWidget(btn4)
Badge(target=btn4, color="#fb8c00").set_count(5000)

# live counter
btn5 = QPushButton("实时")
v.addWidget(btn5)
live = Badge(target=btn5, color="#8e24aa", max_count=999)

counter = 0

def update():
    global counter
    counter += 1
    live.set_count(counter)

timer = QTimer()
timer.timeout.connect(update)
timer.start(30)

w.show()
sys.exit(app.exec())
