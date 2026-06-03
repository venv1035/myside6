"""
DragBar 交互演示
=================
运行 ``uv run python test_drag_bar.py``

- Ctrl+单击 切换选中
- Shift+单击 范围选中
- 拖拽选中项 移动到新位置
- 拖到末尾垃圾桶 删除
"""
import sys
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication, QGroupBox, QHBoxLayout, QLabel, QPushButton,
    QVBoxLayout, QWidget,
)
from widgets import DragBar

app = QApplication(sys.argv)
app.setStyle("Fusion")

w = QWidget()
w.setWindowTitle("DragBar 演示")
w.resize(580, 280)

v = QVBoxLayout(w)
v.setSpacing(12)

# ── 1. 自动撑开模式 ──────────────────────────────────────────────────
v.addWidget(QLabel("自动撑开模式（固定宽度=None）"))
bar1 = DragBar(spacing=8)
bar1.add_item("folder", "文件夹", QIcon.fromTheme("folder"))
bar1.add_item("calc", "计算器", QIcon.fromTheme("accessories-calculator"))
bar1.add_item("note", "记事本", QIcon.fromTheme("accessories-text-editor"))
bar1.add_item("term", "终端", QIcon.fromTheme("utilities-terminal"))
bar1.add_item("browser", "浏览器", QIcon.fromTheme("web-browser"))
v.addWidget(bar1)

# ── 2. 固定宽度模式（换行）────────────────────────────────────────────
v.addWidget(QLabel("固定宽度模式（300px，换行）"))
bar2 = DragBar(fixed_length=300, spacing=8)
for i in range(6):
    bar2.add_item(f"item{i}", f"项{i}", QIcon.fromTheme("document-properties"))
bar2.add_item("trash_test", "可删", QIcon.fromTheme("document-properties"))
v.addWidget(bar2)

# ── 3. 信号监控 ──────────────────────────────────────────────────────
log = QLabel("操作日志…")
log.setStyleSheet("color: #666; padding: 4px;")
v.addWidget(log)

bar1.item_moved.connect(lambda n, i: log.setText(f"移动: {n} → 位置 {i}"))
bar1.item_removed.connect(lambda n: log.setText(f"删除: {n}"))
bar1.selection_changed.connect(
    lambda s: log.setText(f"选中: {', '.join(s) if s else '(无)'}")
)

# ── 4. 操作按钮 ──────────────────────────────────────────────────────
h = QHBoxLayout()
btn_sel = QPushButton("全选")
btn_desel = QPushButton("取消全选")
btn_add = QPushButton("添加项")
btn_info = QPushButton("打印选中")
h.addWidget(btn_sel)
h.addWidget(btn_desel)
h.addWidget(btn_add)
h.addWidget(btn_info)
h.addStretch()
v.addLayout(h)

btn_sel.clicked.connect(bar1.select_all)
btn_desel.clicked.connect(bar1.deselect_all)

i = [6]
btn_add.clicked.connect(
    lambda: bar1.add_item(f"x{i[0]}", f"新增{i[0]}", QIcon.fromTheme("document-new"))
    or i.__setitem__(0, i[0] + 1)
)
btn_info.clicked.connect(
    lambda: log.setText(f"已选中: {bar1.selected_items()}")
)

w.show()
sys.exit(app.exec())
