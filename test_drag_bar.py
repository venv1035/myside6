"""
DragBar 交互演示
=================
运行 ``uv run python test_drag_bar.py``

功能：
- Ctrl+单击 切换多选，Shift+单击 范围选中
- 拖拽选中项到新位置排序
- 拖到末尾垃圾桶（🗑）删除
- 两个 Bar 之间跨 Bar 拖拽
- 空区域拖拽：橡皮框批量选中
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
w.resize(620, 520)

v = QVBoxLayout(w)
v.setSpacing(8)

# ── Bar 1: 自动撑开 ──────────────────────────────────────────────────
v.addWidget(QLabel("Bar 1 — 自动撑开（可直接拖拽排序、跨 Bar 拖拽）"))
bar1 = DragBar(spacing=8)
for name, text, icon in [
    ("folder", "文件夹", "folder"),
    ("calc", "计算器", "accessories-calculator"),
    ("note", "记事本", "accessories-text-editor"),
    ("term", "终端", "utilities-terminal"),
    ("browser", "浏览器", "web-browser"),
]:
    bar1.add_item(name, text, QIcon.fromTheme(icon))
v.addWidget(bar1)

# ── Bar 2: 固定宽度（换行） ───────────────────────────────────────────
v.addWidget(QLabel("Bar 2 — 固定 300px 换行（也可接收跨 Bar 拖拽）"))
bar2 = DragBar(fixed_length=300, spacing=8)
for i in range(5):
    bar2.add_item(f"item{i}", f"项{i}", QIcon.fromTheme("document-properties"))
bar2.add_item("trash_me", "可删", QIcon.fromTheme("document-properties"))
v.addWidget(bar2)

# ── 日志 ─────────────────────────────────────────────────────────────
log = QLabel("操作日志…")
log.setStyleSheet("color: #888; padding: 2px;")
v.addWidget(log)

def log_msg(msg):
    log.setText(msg)

bar1.item_moved.connect(lambda n, i: log_msg(f"Bar1 移动: {n} → {i}"))
bar1.item_removed.connect(lambda n: log_msg(f"Bar1 删除: {n}"))
bar1.selection_changed.connect(
    lambda s: log_msg(f"Bar1 选中: {', '.join(s) if s else '(空)'}")
)
bar2.item_moved.connect(lambda n, i: log_msg(f"Bar2 移动: {n} → {i}"))
bar2.item_removed.connect(lambda n: log_msg(f"Bar2 删除: {n}"))
bar2.selection_changed.connect(
    lambda s: log_msg(f"Bar2 选中: {', '.join(s) if s else '(空)'}")
)

# ── 操作按钮 ──────────────────────────────────────────────────────────
h = QHBoxLayout()
btn_sel = QPushButton("Bar1 全选")
btn_desel = QPushButton("取消全选")
btn_add = QPushButton("Bar1 添加")
btn_info = QPushButton("打印选中")
h.addWidget(btn_sel)
h.addWidget(btn_desel)
h.addWidget(btn_add)
h.addWidget(btn_info)
h.addStretch()
v.addLayout(h)

btn_sel.clicked.connect(bar1.select_all)
btn_desel.clicked.connect(bar1.deselect_all)

counter = [6]
btn_add.clicked.connect(lambda: (
    bar1.add_item(f"x{counter[0]}", f"新增{counter[0]}",
                  QIcon.fromTheme("document-new")),
    counter.__setitem__(0, counter[0] + 1),
))
btn_info.clicked.connect(
    lambda: log_msg(f"Bar1 选中项: {bar1.selected_items()}")
)

w.show()
sys.exit(app.exec())
