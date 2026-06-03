"""
Badge bind() 综合演示
=====================
运行 ``uv run python test_badge.py`` 弹出窗口。

演示绑定的数据源全部不用手动 refresh —— 内部 300ms 定时器自动轮询。
"""
import sys
from PySide6.QtGui import QStandardItemModel
from PySide6.QtWidgets import (
    QApplication, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
)
from widgets import Badge, MyTable, ActionDelegate

app = QApplication(sys.argv)
app.setStyle("Fusion")

w = QWidget()
w.setWindowTitle("Badge 自动轮询演示")
w.resize(700, 520)

v = QVBoxLayout(w)
v.setSpacing(12)

# ====== 1. 普通 list（无包装，定时器自动轮询）=============================
row1 = QHBoxLayout()
row1.addWidget(QLabel("list"))
btn_add = QPushButton("添加")
btn_clr = QPushButton("清空")
row1.addWidget(btn_add)
row1.addWidget(btn_clr)
row1.addStretch()
v.addLayout(row1)

data_list = ["a", "b", "c"]
Badge(target=btn_add, color="#1a73e8").bind(data_list)

btn_add.clicked.connect(lambda: data_list.append(f"x{len(data_list)}"))
btn_clr.clicked.connect(data_list.clear)

# ====== 2. 普通 dict（无包装，定时器自动轮询）=============================
row2 = QHBoxLayout()
row2.addWidget(QLabel("dict"))
btn_add_k = QPushButton("加一项")
btn_clr_d = QPushButton("清空")
row2.addWidget(btn_add_k)
row2.addWidget(btn_clr_d)
row2.addStretch()
v.addLayout(row2)

data_dict = {"name": "张三"}
Badge(target=btn_add_k, color="#43a047").bind(data_dict)

def add_kv():
    data_dict[f"k{len(data_dict)}"] = 0
btn_add_k.clicked.connect(add_kv)
btn_clr_d.clicked.connect(data_dict.clear)

# ====== 3. callable ======================================================
counter = [5]
row3 = QHBoxLayout()
row3.addWidget(QLabel("callable"))
btn_inc = QPushButton("+1")
btn_dec = QPushButton("-1")
row3.addWidget(btn_inc)
row3.addWidget(btn_dec)
row3.addStretch()
v.addLayout(row3)

Badge(target=btn_inc, color="#fb8c00").bind(lambda: counter[0])

btn_inc.clicked.connect(lambda: counter.__setitem__(0, counter[0] + 1))
btn_dec.clicked.connect(lambda: counter.__setitem__(0, max(0, counter[0] - 1)))

# ====== 4. QStandardItemModel（Qt 信号驱动）===============================
row4 = QHBoxLayout()
row4.addWidget(QLabel("QStandardItemModel"))
btn_add_row = QPushButton("插入行")
btn_rm_row = QPushButton("删除末行")
row4.addWidget(btn_add_row)
row4.addWidget(btn_rm_row)
row4.addStretch()
v.addLayout(row4)

model = QStandardItemModel(3, 1)
Badge(target=btn_add_row, color="#8e24aa").bind(model)

btn_add_row.clicked.connect(lambda: model.insertRow(model.rowCount()))
btn_rm_row.clicked.connect(lambda: model.removeRow(model.rowCount() - 1)
                            if model.rowCount() > 0 else None)

# ====== 5. MyTable model（Qt 信号驱动）====================================
v.addWidget(QLabel("MyTable (auto-track)"))
top = QHBoxLayout()
btn_del = QPushButton("删除选中行")
top.addWidget(btn_del)
top.addStretch()
v.addLayout(top)

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

Badge(target=btn_del, color="#ea4335").bind(table.sourceModel())
btn_del.clicked.connect(lambda: table.delete_selected_rows())

w.show()
sys.exit(app.exec())
