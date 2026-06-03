from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from widgets import MyTable, MyCombo, ActionDelegate


SAMPLE_HEADERS = ["", "ID", "姓名", "部门", "城市", "年龄", "工资", "操作"]
SAMPLE_ROWS = [
    [False, 1,  "张伟",  "研发部",  "北京", 28, 18500, ""],
    [False, 2,  "王芳",  "市场部",  "上海", 35, 22000, ""],
    [False, 3,  "李娜",  "财务部",  "广州", 41, 25500, ""],
    [False, 4,  "刘洋",  "研发部",  "深圳", 26, 17800, ""],
    [False, 5,  "陈静",  "人事部",  "北京", 33, 16500, ""],
    [False, 6,  "杨帆",  "市场部",  "杭州", 29, 19200, ""],
    [False, 7,  "赵磊",  "研发部",  "成都", 31, 20800, ""],
    [False, 8,  "黄敏",  "财务部",  "上海", 38, 24000, ""],
    [False, 9,  "周强",  "运营部",  "武汉", 27, 14500, ""],
    [False, 10, "吴丽",  "人事部",  "广州", 45, 23500, ""],
    [False, 11, "徐刚",  "研发部",  "北京", 30, 21000, ""],
    [False, 12, "孙颖",  "市场部",  "深圳", 36, 26800, ""],
    [False, 13, "马超",  "运营部",  "杭州", 24, 13500, ""],
    [False, 14, "朱琳",  "财务部",  "成都", 39, 22500, ""],
    [False, 15, "胡军",  "研发部",  "武汉", 32, 19500, ""],
]
CHECK_COL = 0
ACTION_COL = 7
AGE_COL = 5
SAL_COL = 6
EDITABLE_COLS = [2, 3, 4, 5, 6]


class DemoWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PySide6 现代化控件演示")
        self.resize(1180, 720)
        self.setStyleSheet(
            """
            QMainWindow { background: #f5f5f7; }
            QLabel#title { font-size: 16px; font-weight: 600; color: #202124; }
            QLabel#hint  { color: #5f6368; font-size: 12px; }
            QPushButton { padding: 6px 14px; border-radius: 6px; border: 1px solid #dadce0;
                          background: #ffffff; }
            QPushButton:hover { background: #f1f3f4; }
            QPushButton#danger { background: #ea4335; color: white; border-color: #ea4335; }
            QPushButton#danger:hover { background: #c5221f; }
            QPushButton#primary { background: #1a73e8; color: white; border-color: #1a73e8; }
            QPushButton#primary:hover { background: #1765cc; }
            """
        )

        central = QWidget(self)
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        # --- top: combobox demo --------------------------------------------
        title1 = QLabel("多选下拉勾选列表 (MyCombo)")
        title1.setObjectName("title")
        hint1 = QLabel("点击勾选框或文字都可切换；支持中文搜索；按钮位置可选。")
        hint1.setObjectName("hint")
        root.addWidget(title1)
        root.addWidget(hint1)

        row = QHBoxLayout()
        row.setSpacing(12)
        for caption, items, pos, attr in [
            ("部门(按钮在顶部):", sorted({r[3] for r in SAMPLE_ROWS}), "top", "cb_top"),
            ("城市(按钮在底部):", sorted({r[4] for r in SAMPLE_ROWS}), "bottom", "cb_bottom"),
        ]:
            col = QVBoxLayout()
            col.addWidget(QLabel(caption))
            cb = MyCombo()
            cb.set_items(items)
            cb.selectionChanged.connect(self._update_summary)
            setattr(self, attr, cb)
            col.addWidget(cb)
            row.addLayout(col)

        col_kv = QVBoxLayout()
        col_kv.addWidget(QLabel("标签 (label, value):"))
        self.cb_kv = MyCombo(placeholder="选择标签...")
        self.cb_kv.set_items([
            ("高优先级", "P0"),
            ("中优先级", "P1"),
            ("低优先级", "P2"),
            ("紧急",   "URGENT"),
            ("计划中", "PLANNED"),
            ("已完成", "DONE"),
        ])
        self.cb_kv.selectionChanged.connect(self._update_summary)
        col_kv.addWidget(self.cb_kv)
        row.addLayout(col_kv)
        root.addLayout(row)

        self.selected_label = QLabel("当前选中: -")
        self.selected_label.setObjectName("hint")
        root.addWidget(self.selected_label)

        # --- bottom: table view demo ---------------------------------------
        title2 = QLabel("现代化表格 (MyTable) - 编辑/勾选/筛选/删除/数字比较")
        title2.setObjectName("title")
        hint2 = QLabel(
            "第1列勾选框；姓名/部门/城市/年龄/工资可双击编辑；操作列没有筛选(已禁用)；"
            "年龄/工资是数字列 — 筛菜单里有'按数字比较'开关（=, ≠, >, ≥, <, ≤），"
            "可加多个条件(AND 关系)，如: 工资 > 20000 AND < 25000；"
            "默认筛选全勾选 = 不过滤；鼠标悬停表头显示↑↓排序与漏斗筛选；拖动表头可调整列序。"
        )
        hint2.setObjectName("hint")
        root.addWidget(title2)
        root.addWidget(hint2)

        self.table = MyTable(skip_filter_columns=[ACTION_COL])
        self.table.set_data(SAMPLE_HEADERS, SAMPLE_ROWS)
        self.table.set_checkable_rows(True, column=CHECK_COL)
        self.table.set_editable_columns(EDITABLE_COLS)
        # 数字列: 年龄 / 工资
        self.table.set_column_numeric(AGE_COL, enabled=True)
        self.table.set_column_numeric(SAL_COL, enabled=True)

        delete_delegate = ActionDelegate("删除", parent=self.table)
        delete_delegate.clicked.connect(self._on_delete_one)
        self.table.setItemDelegateForColumn(ACTION_COL, delete_delegate)
        self.table.setColumnWidth(ACTION_COL, 90)
        self.table.setColumnWidth(CHECK_COL, 40)

        self.table.rowChecked.connect(self._on_row_checked)
        self.table.cellEdited.connect(self._on_cell_edited)
        self.table.rowsDeleted.connect(self._on_rows_deleted)
        root.addWidget(self.table, 1)

        # --- action bar -----------------------------------------------------
        bar = QHBoxLayout()
        self.status_label = QLabel("就绪")
        self.status_label.setObjectName("hint")
        bar.addWidget(self.status_label)
        bar.addStretch(1)

        check_all_btn = QPushButton("全部勾选")
        check_all_btn.clicked.connect(lambda: self.table.set_all_checked(True))
        uncheck_all_btn = QPushButton("全部取消")
        uncheck_all_btn.clicked.connect(lambda: self.table.set_all_checked(False))
        clear_filter_btn = QPushButton("清除筛选")
        clear_filter_btn.clicked.connect(self.table.clear_filters)
        add_btn = QPushButton("新增一行")
        add_btn.setObjectName("primary")
        add_btn.clicked.connect(self._on_add_row)
        del_btn = QPushButton("删除勾选行")
        del_btn.setObjectName("danger")
        del_btn.clicked.connect(self._on_delete_checked)

        for b in (check_all_btn, uncheck_all_btn, clear_filter_btn, add_btn, del_btn):
            bar.addWidget(b)
        root.addLayout(bar)

        self._update_summary()

    # ---- callbacks -------------------------------------------------------
    def _update_summary(self) -> None:
        parts = []
        if self.cb_top.selected_labels():
            parts.append("部门=" + "/".join(self.cb_top.selected_labels()))
        if self.cb_bottom.selected_labels():
            parts.append("城市=" + "/".join(self.cb_bottom.selected_labels()))
        if self.cb_kv.selected_values():
            parts.append("标签=" + "/".join(str(v) for v in self.cb_kv.selected_values()))
        self.selected_label.setText("当前选中: " + (" | ".join(parts) if parts else "-"))

    def _on_row_checked(self, src_row: int, checked: bool) -> None:
        n = len(self.table.checked_rows())
        self.status_label.setText(f"行 {src_row} {'已勾选' if checked else '已取消'} ｜ 当前勾选 {n} 行")

    def _on_cell_edited(self, src_row: int, col: int, value) -> None:
        self.status_label.setText(f"编辑: 行{src_row} 列{col} -> {value!r}")

    def _on_rows_deleted(self, rows) -> None:
        self.status_label.setText(f"已删除行: {rows}")

    def _on_delete_one(self, src_row: int) -> None:
        self.table.delete_rows([src_row])

    def _on_delete_checked(self) -> None:
        rows = self.table.checked_rows()
        if not rows:
            QMessageBox.information(self, "提示", "请先勾选要删除的行")
            return
        ret = QMessageBox.question(
            self, "确认", f"确定删除已勾选的 {len(rows)} 行?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if ret == QMessageBox.Yes:
            self.table.delete_checked_rows()

    def _on_add_row(self) -> None:
        source = self.table.sourceModel()
        if source is None:
            return
        new_id = max((source.item(r, 1).data(Qt.DisplayRole)
                      for r in range(source.rowCount())
                      if source.item(r, 1) is not None),
                     default=0) + 1
        self.table.append_row([False, new_id, "新员工", "研发部", "北京", 25, 15000, ""])
        self.status_label.setText(f"新增行 ID={new_id}")


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = DemoWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
