"""
MyTable MVP
===========
最小可运行示例。运行 ``uv run python test_my_table.py`` 弹出窗口。

演示功能: 勾选列 / 编辑 / 筛选 / 删除 / 数值筛选
"""
import sys
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout
from widgets import MyTable, ActionDelegate

EDITABLE_COLS = [1, 2, 3, 4]
ACTION_COL = 5
CHECK_COL = 0

app = QApplication(sys.argv)
app.setStyle("Fusion")

w = QWidget()
w.resize(900, 400)
v = QVBoxLayout(w)

t = MyTable(skip_filter_columns=[ACTION_COL])
t.set_data(
    headers=["", "姓名", "部门", "城市", "年龄", "操作"],
    rows=[
        [False, "张三", "技术", "北京", 30, ""],
        [False, "李四", "市场", "上海", 25, ""],
        [False, "王五", "技术", "广州", 35, ""],
        [False, "赵六", "财务", "北京", 28, ""],
        [False, "陈七", "市场", "上海", 32, ""],
    ],
)
t.set_checkable_rows(True, CHECK_COL)
t.set_editable_columns(EDITABLE_COLS)
t.set_column_numeric(4, True)

d = ActionDelegate("大宝贝", parent=t)
d.clicked.connect(lambda src_row: t.delete_rows([src_row]))
t.setItemDelegateForColumn(ACTION_COL, d)
t.setColumnWidth(ACTION_COL, 90)

v.addWidget(t)

w.show()
sys.exit(app.exec())
