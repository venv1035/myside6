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
- Bar1 苹果风格配色，右上角 X 可隐藏
- 重置按钮（↺）恢复初始图标和排序
"""
import sys
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

# ── Apple-style theme dict ─────────────────────────────────────────────────
APPLE_STYLE = {
    "background": "rgba(250, 250, 250, 0.88)",
    "border": "1px solid rgba(200, 200, 205, 0.5)",
    "border_radius": 10,
}

# ── Bar 1: 苹果风格 + 自动撑开 ──────────────────────────────────────────
v.addWidget(QLabel("Bar 1 — 苹果风格（拖拽排序、跨 Bar 拖拽、右上角 X 可关闭）"))
bar1 = DragBar(spacing=8, style=APPLE_STYLE, closable=True)
items_data = [
    ("folder", "文件夹", "folder"),
    ("calc", "计算器", "accessories-calculator"),
    ("note", "记事本", "accessories-text-editor"),
    ("term", "终端", "utilities-terminal"),
    ("browser", "浏览器", "web-browser"),
]
for name, text, icon in items_data:
    bar1.add_item(name, text, icon)
bar1.snapshot()  # save initial state for reset
v.addWidget(bar1)

# ── Bar 2: 固定宽度（换行） ───────────────────────────────────────────
v.addWidget(QLabel("Bar 2 — 固定 300px 换行（也可接收跨 Bar 拖拽）"))
bar2 = DragBar(fixed_length=300, spacing=8, closable=True)
for i in range(5):
    bar2.add_item(f"item{i}", f"项{i}", "document-properties")
bar2.add_item("trash_me", "可删", "document-properties")
bar2.snapshot()
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
btn_reset1 = QPushButton("Bar1 重置")
btn_reset2 = QPushButton("Bar2 重置")
btn_show1 = QPushButton("显示 Bar1")
btn_show2 = QPushButton("显示 Bar2")
h.addWidget(btn_sel)
h.addWidget(btn_desel)
h.addWidget(btn_add)
h.addWidget(btn_info)
h.addWidget(btn_reset1)
h.addWidget(btn_reset2)
h.addWidget(btn_show1)
h.addWidget(btn_show2)
h.addStretch()
v.addLayout(h)

btn_sel.clicked.connect(bar1.select_all)
btn_desel.clicked.connect(bar1.deselect_all)

counter = [6]
btn_add.clicked.connect(lambda: (
    bar1.add_item(f"x{counter[0]}", f"新增{counter[0]}",
                  "document-new"),
    counter.__setitem__(0, counter[0] + 1),
))
btn_info.clicked.connect(
    lambda: log_msg(f"Bar1 选中项: {bar1.selected_items()}")
)
btn_reset1.clicked.connect(bar1._on_reset)
btn_reset2.clicked.connect(bar2._on_reset)
btn_show1.clicked.connect(bar1.show)
btn_show2.clicked.connect(bar2.show)

w.show()
sys.exit(app.exec())
