# MyTable 控件文档

> 本文档专门介绍 `MyTable` 表格控件。**与 `MyCombo` 完全分离**：多选下拉相关的内容请看 [MY_COMBO.md](MY_COMBO.md)。

---

## 1. 简介

继承自 `QTableView`，搭配 `QSortFilterProxyModel` 子类 `_MultiColumnFilterProxy`，实现 Excel 风格的多功能表格。

核心特点：

- **每列筛选** — 点击表头漏斗图标展开筛选弹窗（checkbox 列表 + 可选数值多条件）
- **双箭头排序** — 表头始终显示排序箭头（未排序时为中性灰、已排序时高亮激活方向）
- **列拖拽重排** — `setSectionsMovable(True)`，拖拽表头改变列顺序
- **行勾选** — 可选每行左侧 checkbox，点击**行内任意位置**自动勾选
- **拖选自动勾选** — 拖选 / Shift+Click / Ctrl+Click 选中行自动打勾
- **单元格编辑** — 可指定哪些列可双击 / Enter 编辑
- **行删除** — 内建 `delete_rows`、`delete_selected_rows`、`delete_checked_rows`
- **行内按钮** — `ActionDelegate` 在指定列绘制圆角按钮（支持空心 / 实心样式）
- **右键菜单** — 批量删除选中行 / 已勾选行 / 全选 / 清空筛选
- **全选 header checkbox** — 表头勾选列绘制「全选」checkbox（left-aligned, 14px）

---

## 2. 快速开始

```python
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout
import sys
from widgets import MyTable, ActionDelegate

app = QApplication(sys.argv)

w = QWidget()
w.resize(900, 400)
v = QVBoxLayout(w)

t = MyTable()
t.set_data(
    headers=["", "姓名", "部门", "城市", "年龄", "操作"],
    rows=[
        [False, "张三", "技术", "北京", 30, ""],
        [False, "李四", "市场", "上海", 25, ""],
        [False, "王五", "技术", "广州", 35, ""],
    ],
)
t.set_checkable_rows(True, 0)
t.set_editable_columns([1, 2, 3, 4])
t.set_column_numeric(4, True)

d = ActionDelegate("删除", parent=t)
d.clicked.connect(lambda src_row: t.delete_rows([src_row]))
t.setItemDelegateForColumn(5, d)
t.setColumnWidth(5, 90)

v.addWidget(t)
w.show()
sys.exit(app.exec())
```

---

## 3. API 参考

### 3.1 构造

```python
MyTable(
    parent: QWidget | None = None,
    *,
    skip_filter_columns: Iterable[int] = (),
)
```

| 参数 | 说明 |
|------|------|
| `parent` | 父控件 |
| `skip_filter_columns` | **不显示**筛选图标的列（如操作列、勾选列）。勾选列在 `set_checkable_rows` 时自动加入 |

初始化时默认启用：`SelectRows + ExtendedSelection`、`AlternatingRowColors`、列拖拽、隐藏行号、每行 30px 高。**`setSortIndicatorShown(False)` 在 `setHorizontalHeader` 和 `setSortingEnabled` 之后再次断言**（因 Qt 会重置该标志）。

### 3.2 数据

```python
set_data(headers: list[str], rows: list[list[Any]]) -> None
```

便利方法：创建 `QStandardItemModel`，逐项设置 `DisplayRole` + `EditRole`，通过 `setModel` 挂接到内部 proxy。内部自动调用 `_apply_flags_to_all` 设置每行 item 的 flags。最后 `resizeColumnsToContents + 30px` 最小 120px。

```python
sourceModel() -> QStandardItemModel | None
proxyModel() -> _MultiColumnFilterProxy
```

### 3.3 勾选列

```python
set_checkable_rows(enabled: bool, column: int = 0) -> None
```

- `enabled=True` — 第 `column` 列显示 checkbox，列宽 56px，自动加入 `skip_filter_columns`
- 表头对应位置绘制「全选」checkbox（14px indicator + "全选"文字）
- 点击行内任意位置（**跳过** checkbox 列本身）自动勾选该行
- 拖选 / Shift+Click 选中行自动勾选

辅助方法：

| 方法 | 返回 |
|------|------|
| `checked_rows() -> list[int]` | 已勾选的 **source** 行号列表 |
| `set_row_checked(source_row, checked)` | 指定行勾选状态 |
| `set_all_checked(checked)` | 批量设全部勾选 |
| `rowChecked` 信号 | `(source_row: int, checked: bool)` |

### 3.4 编辑

```python
set_editable_columns(columns: Sequence[int] | bool) -> None
```

| 参数 | 效果 |
|------|------|
| `True` | 所有列可编辑 |
| `[2, 3, 4, 5, 6]` | 仅这些列可编辑 |
| `False` / `None` | 全部不可编辑（默认） |

内部 `EditTriggers = DoubleClicked \| EditKeyPressed \| SelectedClicked`。

编辑发生变化时发射 `cellEdited(source_row, column, new_value)` 信号。

### 3.5 筛选

#### 启用数值筛选

```python
set_column_numeric(column: int, enabled: bool = True) -> None
```

标记某列为数值列——该列的筛选弹窗下方增加数值条件行（`>, <, =, >=, <=, !=`），多条件 AND。不影响数据模型。

#### 跳过筛选列

```python
set_filter_skipped_columns(columns: Iterable[int]) -> None
```

禁止指定列显示筛选图标（如操作列）。

#### 清空筛选

```python
clear_filters() -> None
```

清除所有列的筛选条件，重置表头 active 状态。

#### 筛选弹窗行为

| 特性 | 说明 |
|------|------|
| 默认全 Unchecked | **空 = 无筛选**（显示所有行） |
| 确定按钮 | 将暂存筛选条件应用到 proxy |
| 仅筛此项 | 鼠标 hover 可见项时弹出的浮窗按钮，**立即**应用（不点确定） |
| 全选 checkbox | tristate（☑全部/▣部分/□无），点击循环跳过中间态 |
| 关闭 | 确定/取消/Esc/外部点击关闭，**无 hover-leave 自动关闭** |
| "仅筛此项"按钮 parent = viewport | 避免鼠标从列表移入按钮时 viewport Leave 闪烁 |

### 3.6 排序

- 点击表头某列触发 proxy 排序（升序/降序切换）
- 表头始终显示双箭头（中性灰 / 高亮激活方向）
- 排序通过 `_MultiColumnFilterProxy.sort()` 驱动，**不与弹窗内升降序冲突**（弹窗升降序只影响弹窗列表可见项）

### 3.7 行操作

```python
delete_rows(source_rows: Iterable[int]) -> list[int]     # 删除指定 source 行（逆序 removeRow）
delete_selected_rows() -> list[int]                       # 删除当前选中行
delete_checked_rows() -> list[int]                        # 删除已勾选行
append_row(values: list[Any]) -> int                      # 追加一行，返回新行索引
```

| 信号 | 参数 | 触发时机 |
|------|------|----------|
| `rowsDeleted` | `list[int]` | 行被删除后（source 行号，降序） |
| `rowChecked` | `(int, bool)` | 某行勾选状态变化 |
| `cellEdited` | `(int, int, object)` | 单元格编辑完成（source_row, column, new_value） |

### 3.8 选择与自动勾选

```
setSelectionBehavior(SelectRows)      # 整行选择
setSelectionMode(ExtendedSelection)   # 可多选（拖选 / Ctrl+Click / Shift+Click）
```

内部连接 `selectionModel().selectionChanged` → `_on_sel_changed` 自动勾选被选中的行。

行为：

| 操作 | 效果 |
|------|------|
| 点击单行 | 选中 → 自动勾选 checkbox |
| Ctrl+Click | 切换选中 → 自动勾选新增选中行 |
| Shift+Click / 拖选 | 选中区间 → 全部自动勾选 |
| 取消选中 | **不取消勾选**（如需取消，直接点 checkbox 列） |

### 3.9 右键菜单

内建上下文菜单：

| 菜单项 | 条件显示 | 底层方法 |
|--------|----------|----------|
| 删除选中行 | 有选中行时 | `delete_selected_rows()` |
| 删除已勾选行 | 有已勾选行时 | `delete_checked_rows()` |
| 全选 / 取消全选 | `set_checkable_rows` 启用时 | `set_all_checked()` |
| 清空筛选 | 总是 | `clear_filters()` |

---

## 4. ActionDelegate 与 ACTION_STYLES

### 4.1 基础用法

```python
from widgets import MyTable, ActionDelegate, ACTION_STYLES

t = MyTable(skip_filter_columns=[5])
# ...
d = ActionDelegate("删除", parent=t)
d.clicked.connect(lambda src_row: t.delete_rows([src_row]))
t.setItemDelegateForColumn(5, d)
t.setColumnWidth(5, 90)
```

### 4.2 信号

```python
clicked = Signal(int)  # source 行号（自动 mapToSource）
```

### 4.3 样式字典

```python
def __init__(self, text="删除", parent=None, *, style=None)
```

`style` 参数接受一个字典，键为：

| 键 | 说明 | 默认值 |
|----|------|--------|
| `bg_normal` | 正常背景填充色 | `#ffffff` |
| `bg_hover` | hover 时背景填充色 | `#fdecea` |
| `border` | 边框颜色（空心按钮时） | `#ea4335` |
| `color` | 文字颜色 | `#c5221f` |
| `filled` | 是否为实心按钮（不画边框） | `False` |

`filled=False`（空心按钮）：白色背景 + 彩色边框 + 彩色文字，hover 时背景变浅色。
`filled=True`（实心按钮）：彩色背景 + 白色文字，无边框，hover 时用 `bg_hover` 加深。

### 4.4 预设

```python
ACTION_STYLES = {
    "delete":         dict(bg_normal="#ffffff", bg_hover="#fdecea", border="#ea4335", color="#c5221f"),
    "confirm":        dict(bg_normal="#ffffff", bg_hover="#e8f5e9", border="#43a047", color="#2e7d32"),
    "info":           dict(bg_normal="#ffffff", bg_hover="#e3f2fd", border="#1e88e5", color="#1565c0"),
    "warning":        dict(bg_normal="#ffffff", bg_hover="#fff3e0", border="#fb8c00", color="#e65100"),
    "delete_solid":   dict(bg_normal="#ea4335", bg_hover="#d93025", border="#ea4335", color="#ffffff", filled=True),
    "confirm_solid":  dict(bg_normal="#43a047", bg_hover="#2e7d32", border="#43a047", color="#ffffff", filled=True),
    "info_solid":     dict(bg_normal="#1e88e5", bg_hover="#1565c0", border="#1e88e5", color="#ffffff", filled=True),
    "warning_solid":  dict(bg_normal="#fb8c00", bg_hover="#e65100", border="#fb8c00", color="#ffffff", filled=True),
}
```

示例：

```python
# 空心（默认）
d = ActionDelegate("编辑", parent=t, style=ACTION_STYLES["confirm"])

# 实心蓝色
d = ActionDelegate("详情", parent=t, style=ACTION_STYLES["info_solid"])

# 自定义
d = ActionDelegate("发布", parent=t, style=dict(
    bg_normal="#ea4335", bg_hover="#d93025",
    border="#ea4335", color="#ffffff", filled=True,
))
```

---

## 5. NoFocusDelegate

`NoFocusDelegate` 是内建的自定义 `QStyledItemDelegate`：

```python
class NoFocusDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        opt = QStyleOptionViewItem(option)
        opt.state &= ~QStyle.State_HasFocus
        super().paint(painter, opt, index)
```

在 `MyTable.__init__` 末尾通过 `setItemDelegate(NoFocusDelegate(self))` 设为全表默认 delegate，清除所有单元格的焦点虚线矩形框。**对 `setItemDelegateForColumn` 指定的列 delegate 无影响**（列 delegate 优先于全表 delegate）。

---

## 6. 视觉定制

### 6.1 通过 Stylesheet

`MyTable` 的 `_apply_style()` 方法设置默认 stylesheet，覆盖 `QTableView`、`QHeaderView::section`、`QTableView::item` 样式。可在创建后覆写：

```python
t.setStyleSheet("""
    QTableView {
        font-size: 14px;
        selection-background-color: #cce5ff;
    }
""")
```

### 6.2 行高 / 列宽

```python
t.verticalHeader().setDefaultSectionSize(30)    # 默认行高
t.setColumnWidth(col, 90)                       # 手动列宽
```

---

## 7. 实现原理

### 7.1 类架构

```
MyTable (QTableView)
├── _MultiColumnFilterProxy (QSortFilterProxyModel)  ← 内部 proxy
│   └── QStandardItemModel                            ← 外部 source model（通过 set_data / setModel 设置）
├── _FilterHeaderView (QHeaderView)                   ← 自绘表头
│   ├── 漏斗图标 + 双箭头 + 全选 checkbox 在 paintSection 中自绘
│   └── mousePressEvent → filterClicked / checkAllClicked 信号
├── NoFocusDelegate                                    ← 全表 delegate（去焦点虚线）
├── ActionDelegate (per-column)                        ← 用户通过 setItemDelegateForColumn 安装
└── 右键菜单连接 customContextMenuRequested
```

### 7.2 筛选弹窗

```
_FilterPopup (QFrame, Qt.Popup)
├── items (checkbox list)
│   └── "仅筛此项" hover button (parent = list viewport)
├── numeric conditions (_NumericConditionRow × N)
│   └── [op combobox] [value spinbox] [× remove button]
├── 全选 checkbox (tristate)
└── 确定 / 取消 / 升序 / 降序 / 反选 / 重置
```

### 7.3 关键流程

| 流程 | 描述 |
|------|------|
| 筛选 | 用户点击漏斗 → `_show_filter_menu` → 弹窗 → 勾选/数值条件 → 确定 → `_on_filter_changed` → proxy.setColumnFilter |
| 排序 | 用户点表头 → `super().mousePressEvent` → proxy.sort() → indicator 激活 |
| 拖选勾选 | 选中行 → `selectionModel().selectionChanged` → `_on_sel_changed` → 设 checkbox Checked |
| 删除 | `delete_rows` → `source.removeRow`（逆序） → `rowsDeleted` 信号 |
| 全选 header | 点表头 checkbox → `checkAllClicked` → `_on_header_check_all` → 遍历设全部/取消 |

---

## 8. 注意事项

1. **`setSortIndicatorShown(False)` 必须在 `setHorizontalHeader` 之后再次断言**。`QTableView.setHorizontalHeader` 和 `setSortingEnabled(True)` 都会把该标志重置为 `True`。

2. **`ActionDelegate` 的 parent 必须是 QTableView**。因为内部通过 `parent.viewport()` 安装 `MouseMove` 事件过滤器来追踪 hover 行。如果 parent 不对，hover 高亮不工作。

3. **`setItemDelegate(NoFocusDelegate)` 必须在 `setItemDelegateForColumn` 之前调用**。否则 `NoFocusDelegate` 会覆盖列 delegate（虽然 Qt 内部列 delegate 优先，但最好是先设全表再设列）。

4. **`_on_row_clicked` 已移除**，不再通过 `clicked` 信号手动切换勾选。自动勾选由 `selectionChanged` 驱动（覆盖全部选中方式：鼠标拖选、Shift、Ctrl、键盘）。

5. **删除行不会自动取消选中**。删完后选中行号可能偏移，建议删除后清空选中或重设模型。

6. **数值筛选与文本筛选互斥** — 在同一列上设置数值条件会自动清除该列的文本 checkbox 筛选，反之亦然。

7. **弹窗只由确定/取消/Esc/外部点击关闭**，无 hover-leave 自动关闭逻辑。

---

## 9. 踩坑记录

### 9.1 筛选按钮点击触发排序

**根因**：`_FilterHeaderView.mousePressEvent` 先判断 `skip_filter_columns`，然后检测漏斗图标区域。旧代码中有一个 `visible` 条件检查（`section in _active_columns or section == _hover_section`），导致鼠标从 hover 到 click 之间如果 `_hover_section` 变化，漏斗点击被判为"不可见"而 fallthrough 到 `super().mousePressEvent` 触发排序。

**修复**：移除 `visible` 条件，只要坐标在漏斗图标区域内就直接触发弹窗。

### 9.2 表头全选 checkbox 点击失效

**根因**：`mousePressEvent` 中 `skip_filter_columns` 的检查在 `check_column` 之前，导致勾选列被跳过时全选 checkbox 无法触发。

**修复**：将 check column 检测移到 `skip_filter_columns` 之前。

### 9.3 删除后 `_on_row_clicked` 崩溃

**根因**：删除行后触发 `clicked` 信号，但 `proxy.sourceModel()` 返回 `None`，导致 `source_model.item(...)` 报 `AttributeError`。

**修复**：增加 `source_model is None` 守卫 + `mapToSource` 返回无效索引时跳过。

### 9.4 `ActionDelegate` 不显示

**根因**：`setItemDelegate(NoFocusDelegate(self))` 覆盖了之前通过 `setItemDelegateForColumn` 设置的列 delegate。

**修复**：先设全表 delegate，再设列 delegate（列 delegate 优先于全表 delegate，但顺序保证清晰）。

### 9.5 筛选弹窗内 hover 按钮闪烁

**根因**：hover button parent 设为了 popup，当鼠标从列表移入按钮时，列表 viewport 收到 Leave 事件重建按钮，导致闪烁。

**修复**：按钮 parent = `list.viewport()`，移动鼠标在 viewport 和 button 之间不触发 viewport Leave。

---

> 完。`MyCombo` 相关的内容请看 [MY_COMBO.md](MY_COMBO.md)。
