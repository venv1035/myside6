"""
MyCombo MVP
===========
最小可运行示例。运行 ``uv run python test_my_combo.py`` 弹出窗口。
"""
import sys
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout
from widgets import MyCombo,ACTION_STYLES

app = QApplication(sys.argv)
app.setStyle("Fusion")

w = QWidget()
w.resize(300, 120)
v = QVBoxLayout(w)

cb = MyCombo(placeholder="请选择城市...",string_only=ACTION_STYLES["confirm"])
cb.set_items(["北京", "上海", "广州", "深圳"])
v.addWidget(cb)

w.show()
sys.exit(app.exec())
