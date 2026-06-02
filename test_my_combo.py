"""
MyCombo MVP
===========
最小可运行示例。运行 ``uv run python test_my_combo.py`` 弹出窗口。
"""
import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel,
)
from widgets import MyCombo


app = QApplication(sys.argv)
app.setStyle("Fusion")

w = QWidget()

w.resize(360, 180)
v = QVBoxLayout(w)

cb = MyCombo(placeholder="请选择...")
cb.set_dict_items({"BJ": "北京", "SH": "上海", "GZ": "广州", "SZ": "深圳"})
btn = QPushButton("切换搜索框位置")
v.addWidget(cb)
v.addWidget(btn)


status = QLabel("")
v.addWidget(status)
btn.clicked.connect(lambda:print(cb.selected_labels()))

row = QHBoxLayout()
for label, fn in [("全选", cb.select_all), ("清空", cb.clear_selection),
                  ("切 string_only", lambda: cb.set_string_only(not cb.is_string_only()))]:
    b = QPushButton(label)
    b.clicked.connect(fn)
    row.addWidget(b)
v.addLayout(row)

w.show()
sys.exit(app.exec())
