"""
MyTable MVP
===========
最小可运行示例。运行 ``uv run python test_my_table.py`` 弹出窗口。
"""
import sys
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout
from widgets import MyTable

app = QApplication(sys.argv)
app.setStyle("Fusion")

w = QWidget()
w.resize(700, 400)
v = QVBoxLayout(w)

t = MyTable()
t.set_data(
    headers=["", "姓名", "部门", "城市", "年龄"],
    rows=[
        ["张三", "技术", "北京", 30],
        ["李四", "市场", "上海", 25],
        ["王五", "技术", "广州", 35],
        ["赵六", "财务", "北京", 28],
        ["陈七", "市场", "上海", 32],
    ],
)
t.set_checkable_rows(True, 0)
v.addWidget(t)

w.show()
sys.exit(app.exec())
