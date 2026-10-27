"""四个自定义控件演示。运行：uv run python demo.py"""
from __future__ import annotations

import sys

from PySide6.QtGui import QStandardItemModel
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from widgets import ACTION_STYLES, ActionDelegate, Badge, DragBar, MyCombo, MyTable

TITLE_CSS = "font-size: 14px; font-weight: 600; color: #202124;"
HINT_CSS = "color: #5f6368; font-size: 12px;"


def _label(text: str, css: str) -> QLabel:
    lab = QLabel(text)
    lab.setWordWrap(True)
    lab.setStyleSheet(css)
    return lab


def _page(title: str, hint: str) -> tuple[QWidget, QVBoxLayout]:
    """每个 Tab 的骨架：标题 + 说明 + 一个纵向布局。"""
    page = QWidget()
    v = QVBoxLayout(page)
    v.addWidget(_label(title, TITLE_CSS))
    v.addWidget(_label(hint, HINT_CSS))
    return page, v


def _row(*widgets: QWidget) -> QHBoxLayout:
    h = QHBoxLayout()
    for w in widgets:
        h.addWidget(w)
    h.addStretch()
    return h


# ---------------------------------------------------------------- MyCombo
def page_combo() -> QWidget:
    page, v = _page("MyCombo — 多选下拉",
                    "点击勾选；输入过滤；悬停选项右侧会出现 [仅筛此项]。")

    cb = MyCombo(placeholder="选择城市...")
    cb.set_items(["北京", "上海", "广州", "深圳", "杭州", "成都"])

    cb_kv = MyCombo(placeholder="选择标签...")
    cb_kv.set_items(["北京北京北京北京北京北京北京北京北京北京北",
                     "上海", "广州", "深圳", "杭州", "成都"])

    status = QLabel("当前选中: -")
    status.setStyleSheet("color: #5f6368;")

    def update() -> None:
        parts = []
        if cb.selected_labels():
            parts.append("城市=" + "/".join(cb.selected_labels()))
        if cb_kv.selected_values():
            parts.append("标签=" + "/".join(str(x) for x in cb_kv.selected_values()))
        status.setText("当前选中: " + (" | ".join(parts) if parts else "-"))

    cb.selectionChanged.connect(update)
    cb_kv.selectionChanged.connect(update)

    v.addWidget(cb)
    v.addWidget(cb_kv)
    v.addWidget(status)
    v.addStretch(1)
    return page


# ---------------------------------------------------------------- MyTable
def page_table() -> QWidget:
    page, v = _page(
        "MyTable — 筛选 / 勾选 / 编辑 / 删除",
        "第 0 列勾选；双击可编辑；漏斗筛选；操作列按钮删除；"
        "年龄列可'按数字比较'，入职日期列可'按日期范围'："
        "标题栏的「年」「月」点开是网格面板，年份还能直接输入。",
    )

    check_col, action_col = 0, 6
    table = MyTable(skip_filter_columns=[action_col])
    table.set_data(
        headers=["", "姓名", "部门", "城市", "年龄", "入职日期", "操作"],
        rows=[
            [False, "张三", "技术", "北京", 30, "2021-03-15", ""],
            [False, "李四", "市场", "上海", 25, "2022/07/01", ""],
            [False, "王五", "技术", "广州", 35, "2019.11.20", ""],
            [False, "赵六", "财务", "北京", 28, "20230110", ""],
            [False, "陈七", "市场", "上海", 32, "2020-05-18", ""],
        ],
    )
    table.set_checkable_rows(True, check_col)
    table.set_editable_columns([1, 2, 3, 4, 5])
    table.set_column_numeric(4, True)

    deleter = ActionDelegate("删除", parent=table,
                             style=ACTION_STYLES["delete_solid"])
    deleter.clicked.connect(lambda src_row: table.delete_rows([src_row]))
    table.setItemDelegateForColumn(action_col, deleter)
    table.setColumnWidth(action_col, 90)
    table.setColumnWidth(check_col, 40)

    btn_all = QPushButton("全部勾选")
    btn_none = QPushButton("全部取消")
    btn_clear = QPushButton("清除筛选")
    btn_all.clicked.connect(lambda: table.set_all_checked(True))
    btn_none.clicked.connect(lambda: table.set_all_checked(False))
    btn_clear.clicked.connect(table.clear_filters)

    v.addWidget(table, 1)
    v.addLayout(_row(btn_all, btn_none, btn_clear))
    return page


# ------------------------------------------------------------------ Badge
def page_badge() -> QWidget:
    page, v = _page("Badge — 右上角数字角标",
                    "绑定 list / dict / callable / 模型，定时自动刷新。")

    btn_add, btn_clr = QPushButton("添加"), QPushButton("清空")
    data_list = ["a", "b", "c"]
    Badge(target=btn_add, color="#1a73e8").bind(data_list)
    btn_add.clicked.connect(lambda: data_list.append(f"x{len(data_list)}"))
    btn_clr.clicked.connect(data_list.clear)

    btn_inc, btn_dec = QPushButton("+1"), QPushButton("-1")
    counter = [5]
    Badge(target=btn_inc, color="#fb8c00").bind(lambda: counter[0])
    btn_inc.clicked.connect(lambda: counter.__setitem__(0, counter[0] + 1))
    btn_dec.clicked.connect(lambda: counter.__setitem__(0, max(0, counter[0] - 1)))

    btn_add_row, btn_rm_row = QPushButton("插入行"), QPushButton("删除末行")
    model = QStandardItemModel(3, 1)
    Badge(target=btn_add_row, color="#8e24aa").bind(model)
    btn_add_row.clicked.connect(lambda: model.insertRow(model.rowCount()))
    btn_rm_row.clicked.connect(
        lambda: model.removeRow(model.rowCount() - 1) if model.rowCount() > 0 else None
    )

    v.addLayout(_row(btn_add, btn_clr))
    v.addLayout(_row(btn_inc, btn_dec))
    v.addLayout(_row(btn_add_row, btn_rm_row))
    v.addStretch(1)
    return page


# ---------------------------------------------------------------- DragBar
def page_dragbar() -> QWidget:
    page, v = _page("DragBar — 可拖拽工具栏",
                    "Ctrl 多选 / Shift 范围选；拖拽排序；拖到垃圾桶删除；可跨 Bar 拖放。")

    apple = {
        "background": "rgba(250, 250, 250, 0.88)",
        "border": "1px solid rgba(200, 200, 205, 0.5)",
        "border_radius": 10,
    }
    bar1 = DragBar(spacing=8, style=apple, closable=True)
    for name, text, icon in [
        ("folder", "文件夹", "folder"),
        ("calc", "计算器", "accessories-calculator"),
        ("note", "记事本", "accessories-text-editor"),
        ("term", "终端", "utilities-terminal"),
        ("browser", "浏览器", "web-browser"),
    ]:
        bar1.add_item(name, text, icon)
    bar1.snapshot()

    bar2 = DragBar(fixed_length=300, spacing=8, closable=True)
    for i in range(5):
        bar2.add_item(f"item{i}", f"项{i}", "document-properties")
    bar2.snapshot()

    log = QLabel("操作日志…")
    log.setStyleSheet("color: #888;")
    bar1.item_moved.connect(lambda n, i: log.setText(f"Bar1 移动: {n} → {i}"))
    bar1.item_removed.connect(lambda n: log.setText(f"Bar1 删除: {n}"))
    bar2.item_moved.connect(lambda n, i: log.setText(f"Bar2 移动: {n} → {i}"))
    bar2.item_removed.connect(lambda n: log.setText(f"Bar2 删除: {n}"))

    btn_sel = QPushButton("Bar1 全选")
    btn_reset = QPushButton("Bar1 重置")
    btn_sel.clicked.connect(bar1.select_all)
    btn_reset.clicked.connect(bar1.reset)

    v.addWidget(bar1)
    v.addWidget(bar2)
    v.addWidget(log)
    v.addLayout(_row(btn_sel, btn_reset))
    v.addStretch(1)
    return page


# ------------------------------------------------------------------ shell
class DemoWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("自定义控件演示 — MyCombo / MyTable / Badge / DragBar")
        self.resize(980, 640)
        self.setStyleSheet(
            "QMainWindow { background: #f5f5f7; }"
            "QTabWidget::pane { border: 1px solid #dadce0; background: #fff; border-radius: 8px; }"
            "QTabBar::tab { padding: 8px 16px; }"
            "QPushButton { padding: 6px 14px; border-radius: 6px;"
            " border: 1px solid #dadce0; background: #fff; }"
            "QPushButton:hover { background: #f1f3f4; }"
        )
        tabs = QTabWidget()
        for page, name in (
            (page_combo, "MyCombo"),
            (page_table, "MyTable"),
            (page_badge, "Badge"),
            (page_dragbar, "DragBar"),
        ):
            tabs.addTab(page(), name)
        self.setCentralWidget(tabs)


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = DemoWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

