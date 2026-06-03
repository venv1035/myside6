"""
Badge + MyTable 联动演示
========================
运行 ``uv run python test_badge.py`` 弹出窗口。

表格 10 行，Badge 通过 ``.bind(model)`` 自动追踪行数。
"""
import sys
from PySide6.QtWidgets import (
    QApplication, QHBoxLayout, QPushButton, QVBoxLayout, QWidget,
)
from widgets import Badge, MyTable, ActionDelegate

app = QApplication(sys.argv)
app.setStyle("Fusion")

w = QWidget()
w.setWindowTitle("Badge bind() 演示")
w.resize(700, 400)

v = QVBoxLayout(w)

# ---- top bar ---------------------------------------------------------------
top = QHBoxLayout()
btn_del = QPushButton("删除选中行")
top.addWidget(btn_del)
top.addStretch()
v.addLayout(top)

# ---- table ----------------------------------------------------------------
HEADERS = ["", "姓名", "部门", "城市", "年龄", "操作"]
ROWS = [
    [False, "张伟",  "研发部", "北京", 28, ""],
    [False, "王芳",  "市场部", "上海", 35, ""],
    [False, "李娜",  "财务部", "广州", 41, ""],
    [False, "刘洋",  "研发部", "深圳", 26, ""],
    [False, "陈静",  "市场部", "北京", 32, ""],
    [False, "赵敏",  "财务部", "上海", 29, ""],
    [False, "周杰",  "研发部", "广州", 38, ""],
    [False, "吴迪",  "市场部", "深圳", 27, ""],
    [False, "郑爽",  "财务部", "北京", 33, ""],
    [False, "孙丽",  "研发部", "上海", 31, ""],
]
ACTION_COL = 5
CHECK_COL = 0

table = MyTable(skip_filter_columns=[ACTION_COL])
table.set_data(HEADERS, ROWS)
table.set_checkable_rows(True, CHECK_COL)
table.set_editable_columns([1, 2, 3, 4])
table.set_column_numeric(4, True)

del_delegate = ActionDelegate("删除", parent=table)
del_delegate.clicked.connect(lambda row: table.delete_rows([row]))
table.setItemDelegateForColumn(ACTION_COL, del_delegate)
table.setColumnWidth(ACTION_COL, 90)

v.addWidget(table, 1)

# ---- badge bound to model — auto-tracks rowCount ---------------------------
Badge(target=btn_del, color="#ea4335").bind(table.sourceModel())

btn_del.clicked.connect(lambda: table.delete_selected_rows())

w.show()
sys.exit(app.exec())
