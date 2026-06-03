# PySide6 现代化控件库

一组面向业务后台的现代化 PySide6 自定义控件。包含两个核心控件：

- **MyTable** — Excel 风格表格：每列筛选、双箭头排序、列拖拽、行勾选、单元格编辑、行删除、行内按钮（本文档）
- **MyCombo** — 多选下拉勾选输入框：真实可编辑、输入即过滤、三个操作按钮（全选 / 反选 / 取消）— 详见 [MY_COMBO.md](MY_COMBO.md)

---

## 1. 概览

### 1.1 文件结构

```
D:\Myside\
├── widgets\
│   ├── __init__.py                 # 公共导出: MyTable, ActionDelegate, MyCombo
│   ├── my_table.py        # ~36 KB
│   └── my_combo.py        # ~46 KB
├── main.py                         # MyTable 演示窗口
├── test_my_combo.py                # MyCombo MVP 调用脚本
├── pyproject.toml
├── README.md                       # 本文件 — MyTable 文档
└── MY_COMBO.md                     # MyCombo 专属文档
```

### 1.2 依赖

- Python ≥ 3.12
- PySide6 ≥ 6.11（已通过 `uv add PySide6` 安装）

### 1.3 运行

```powershell
uv run python main.py
```

### 1.4 导入

```python
from widgets import MyTable, MyCombo, ActionDelegate
```

---

## 2. MyTable

继承自 `QTableView`，**始终通过一个内部的 QSortFilterProxyModel 包装真实数据模型**。所有行号 API 以 *源行号*（source row）为准，避免筛选 / 排序后行号错乱。

### 2.1 快速开始

```python
from PySide6.QtWidgets import QApplication
import sys
from widgets import MyTable

app = QApplication(sys.argv)

table = MyTable(skip_filter_columns=[4])  # 禁用第 4 列（操作列）的筛选入口
table.set_data(
    ["ID", "姓名", "部门", "城市", "操作"],
    [
        [1, "张伟", "研发部", "北京", ""],
        [2, "王芳", "市场部", "上海", ""],
        [3, "李娜", "财务部", "广州", ""],
    ],
)
table.set_column_numeric(2, enabled=True)   # "部门" 列按数字比较(可选)
table.set_column_numeric(3, enabled=True)   # "城市" 列按数字比较
table.resize(700, 400)
table.show()
sys.exit(app.exec())
```

数字列的弹窗会多一个"按数字比较"开关：勾上后列表/搜索框隐藏，出现**多个条件行**。每行 = `运算符 + 数字 + ×`，可以点"+ 添加条件"加行；所有条件用 AND 组合（要"工资在 (20000, 25000) 范围"就直接 `(>, 20000)` + `(<, 25000)`）。运算符支持 `=`, `!=`, `>`, `>=`, `<`, `<=` 六种。

### 2.2 API 参考

#### 构造与数据填充

| 方法 | 说明 |
|---|---|
| `MyTable(parent=None)` | 构造空表 |
| `set_data(headers: list[str], rows: list[list[Any]])` | 一次性填充表头与数据，内部建立 `QStandardItemModel` |
| `setModel(model)` | 直接接入自定义模型（推荐 `QStandardItemModel`；其它 `QAbstractItemModel` 也可用但勾选/编辑功能依赖 `QStandardItemModel`） |
| `sourceModel() -> QStandardItemModel \| None` | 取出**源模型**（不是 proxy） |
| `proxyModel() -> QSortFilterProxyModel` | 取出筛选 proxy（继承自 `QSortFilterProxyModel`） |

#### 行勾选

| 方法 | 说明 |
|---|---|
| `set_checkable_rows(enabled: bool, column: int = 0)` | 启用/禁用行勾选；`column` 指定哪一列作为复选框列（该列自动跳过筛选 UI） |
| `checked_rows() -> list[int]` | 返回当前已勾选的**源行号**列表 |
| `set_row_checked(source_row: int, checked: bool)` | 程序化勾选/取消某一行 |
| `set_all_checked(checked: bool)` | 全部勾选 / 全部取消 |

#### 单元格编辑

| 方法 | 说明 |
|---|---|
| `set_editable_columns(columns)` | `True` 表示所有列可编辑；列号列表表示白名单；`False` / `None` 表示禁用编辑 |

编辑触发：双击 / 按 F2 / 选中后单击。勾选列与"被排除"的列自动不可编辑。

#### 行删除 / 新增

| 方法 | 说明 |
|---|---|
| `delete_rows(source_rows: Iterable[int]) -> list[int]` | 按源行号删除任意行，返回实际删除的行号（降序） |
| `delete_selected_rows() -> list[int]` | 删除当前**视图选中**（蓝色高亮）的行 |
| `delete_checked_rows() -> list[int]` | 删除所有勾选的行 |
| `append_row(values: list[Any]) -> int` | 追加一行；如启用了勾选列，对应位置传 `bool` |

#### 筛选

| 方法 | 说明 |
|---|---|
| `clear_filters()` | 清除所有列的筛选（文本 + 数字），重置漏斗图标 |
| `set_filter_skipped_columns(columns)` | 批量禁用指定列的筛选入口（漏斗图标不画、点击无响应）—— 给"操作"列这种纯 UI 列用 |
| `set_column_numeric(column, enabled=True)` | 把某列标记为**数字列**，弹窗顶部出现"按数字比较"开关 |
| `column_numeric_filter(column) -> list[tuple[str, float]] \| None` | 读取某列当前的数字比较 filter；`None` 表示没启用；`[(">", 20000), ("<", 25000)]` 表示 2 个条件 AND |

**默认行为**：弹窗打开时所有可见项**视觉上全勾选**（看起来"全选"），但语义上是"不过滤"——只有当用户**取消勾选**某项后，"确定"才真正下发 filter。这样默认开/关筛选不会误伤行数。

**数字比较**：勾上"按数字比较"开关 → 列表/搜索框隐藏，出现**条件列表**。每行 `运算符 + 数字 + ×`；点"+ 添加条件"追加行（至少保留 1 行）。所有条件用 **AND** 组合，常见用法：
- 范围筛选：`工资 > 20000 AND < 25000`
- 闭区间：`年龄 >= 18 AND <= 35`
- 排除特定值：`工资 > 0 AND != 25000`

运算符支持 `=`, `!=`, `>`, `>=`, `<`, `<=` 六种。proxy 内部用 `float(cell) op value` 比较，无法转成 float 的行会被**过滤掉**（而不是通过）。

#### 信号

| 信号 | 参数 | 触发时机 |
|---|---|---|
| `rowsDeleted` | `list[int]`（被删的源行号，降序） | 调用任意 `delete_*` 方法且确实删除了行 |
| `rowChecked` | `int, bool`（源行号，是否勾选） | 单行勾选状态变化 |
| `cellEdited` | `int, int, object`（源行号，列号，新值） | 用户编辑了一个**可编辑列**的单元格 |

#### 完整示例

```python
from PySide6.QtCore import Qt
from widgets import MyTable, ActionDelegate

table = MyTable()
table.set_data(
    ["", "ID", "姓名", "部门", "操作"],
    [[False, 1, "张伟", "研发部", ""],
     [False, 2, "王芳", "市场部", ""]]
)

# 第 0 列勾选框
table.set_checkable_rows(True, column=0)

# 第 2、3 列可编辑（双击编辑）
table.set_editable_columns([2, 3])

# 最后一列内联"删除"按钮
delegate = ActionDelegate("删除", parent=table)
delegate.clicked.connect(lambda src_row: table.delete_rows([src_row]))
table.setItemDelegateForColumn(4, delegate)

# 事件回调
table.rowChecked.connect(lambda r, c: print(f"行 {r} 勾选状态: {c}"))
table.cellEdited.connect(lambda r, c, v: print(f"行 {r} 列 {c} 改为 {v!r}"))
table.rowsDeleted.connect(lambda rows: print(f"删除了行: {rows}"))

# 批量操作
table.set_all_checked(True)
table.delete_checked_rows()
```

### 2.3 ActionDelegate（行内按钮）

在某一列每行渲染一个可点击的按钮。

```python
class ActionDelegate(QStyledItemDelegate):
    clicked = Signal(int)                       # 参数: 源行号
    def __init__(self, text: str = "删除", parent: QTableView | None = None)
```

| 参数 | 说明 |
|---|---|
| `text` | 按钮文字（默认"删除"） |
| `parent` | 必须是承载表格的 `QTableView`，用于 hover 高亮 |

用法：

```python
delete_btn = ActionDelegate("删除", parent=table)
delete_btn.clicked.connect(lambda src_row: table.delete_rows([src_row]))
table.setItemDelegateForColumn(action_column, delete_btn)
table.setColumnWidth(action_column, 90)
```

按钮样式：圆角白底 + 红色文字 / 边框，hover 时浅红色填充。

### 2.4 表头视觉规则

每个表头单元从左到右最多包含 3 部分：

```
|  列名   ↕排序双箭头   漏斗   |
```

- **排序双箭头**：始终上下两个三角形并存
  - 默认（未排序当前列）：鼠标 hover 时显示灰色双箭头
  - 升序：上箭头变蓝，下箭头保持灰
  - 降序：下箭头变蓝，上箭头保持灰
- **漏斗**：
  - 默认隐藏，鼠标 hover 表头才显示灰色描边漏斗
  - 列已启用筛选：始终显示**蓝色实心漏斗 + 右上角红点**
  - **被 `set_filter_skipped_columns` 禁用的列**：漏斗永远不画，鼠标 hover 也不响应——适合"操作"列（内联按钮）、"选择"列（带 checkbox）等纯 UI 列

两者位置固定不重叠（排序在漏斗左侧，间隔 6 px）。如果列被 `set_filter_skipped_columns` 禁用，排序双箭头会贴右边缘显示。

### 2.5 注意事项

1. **行号始终是源行号**。`checked_rows()`、`delete_*`、`rowChecked` 信号等返回 / 接收的都是源模型的行索引。即使用户对视图做了排序或筛选，行号也不会变。
2. **勾选列不可编辑、不会弹出筛选菜单**。`set_checkable_rows(True, column=0)` 会自动把第 0 列从可编辑列表和筛选 UI 中排除。
3. **`set_data` 会替换整个模型**，并会断开旧模型的 `itemChanged` 信号；如需保留数据请改用 `setModel(your_model)`。
4. **行内按钮的事件区域**：`ActionDelegate.editorEvent` 只在 `option.rect.contains(...)` 范围内捕获点击，按钮覆盖整个单元格；若想让按钮更小，请把列宽调小。
5. **拖动列顺序后**，`columnCount()` 与列号 API 仍按逻辑顺序工作（与 Qt 的 `QHeaderView.swapSections` 一致）。
6. **数字列筛选**：`set_column_numeric` 只影响**弹窗 UI**（是否显示"按数字比较"开关），不影响数据模型。proxy 内部按 `float(cell_data)` 比较；**无法转 float 的行会被过滤掉**（比如空串、非数字字符串），跟"等于"行为一致。
7. **筛选默认"全勾选 = 不过滤"**：弹窗打开时所有项视觉全勾，但 `_on_ok` 只在用户主动**取消**过某项后才下发 `set[str]` filter。直接点"确定"会 emit `None` = 不过滤。
8. **文本 filter 与数字 filter 在同一列上互斥**：勾上"按数字比较"并确定后，自动清掉该列的文本 filter（反之亦然）。

---

## 3. MyCombo

> **MyCombo 的完整文档已拆到独立文件 [MY_COMBO.md](MY_COMBO.md)**，包含：
>
> - 快速开始 + `set_dict_items` / `swap` 用法
> - 完整 API 参考（构造、数据 / 选中、弹窗控制、信号）
> - 弹窗 3 按钮（全选 / 反选 / 取消）的"作用于可见项"语义
> - 键盘交互（任意字符 / ↓↑ / Esc / Enter）
> - 视觉细节（2 px 焦点下划线、聚焦变蓝、已选计数）
> - **解锁输入框 `string_only` 模式**（默认多选 + 自由编辑两用）
> - 44-key 主题系统 + `set_theme()` 运行时切换
> - 完整示例（含 `QCompleter`）
> - 实现原理（类协作图、5 个关键流程）
> - 踩坑记录（点一下就关、取消按钮歧义、`set_theme` QLayout 警告）
>
> 跑得起来的最短调用见根目录 [`test_my_combo.py`](test_my_combo.py)（40 行的真实 GUI 窗口）。

## 4. 实现原理

### 4.1 MyTable 类协作图

```
┌─────────────────────────────────────────────────────────┐
│                  MyTable (QTableView)           │
│  ┌──────────────────────────────────────────────────┐   │
│  │  _FilterHeaderView  (自定义 QHeaderView)         │   │
│  │   • 自绘漏斗图标 (hover 显示 / active 高亮)      │   │
│  │   • 自绘双箭头排序指示器                         │   │
│  │   • 漏斗点击 → emit filterClicked → 弹窗         │   │
│  └──────────────────────────────────────────────────┘   │
│                                                         │
│  setModel(proxy)                                        │
│         │                                               │
│         ▼                                               │
│  _MultiColumnFilterProxy (QSortFilterProxyModel)        │
│   • dict[col] -> set(allowed values)                    │
│   • filterAcceptsRow: 多列条件 AND                      │
│         │                                               │
│         ▼                                               │
│  QStandardItemModel (源数据，由 set_data 创建)           │
└─────────────────────────────────────────────────────────┘

弹出窗口（按需创建）：
  _FilterPopup (QFrame, Qt.Popup)
   • 升/降序按钮
   • 搜索框（中文 IME 正常）
   • _CheckListWidget (勾选列表)
   • 清除筛选 / 取消 / 确定

行内动作（可选）：
  ActionDelegate (QStyledItemDelegate)
   • paint() 绘按钮外观
   • editorEvent() 捕获点击 → 映射 proxy→source → emit clicked(src_row)
```

### 4.2 MyTable 关键流程

#### (1) 数据流

```
QStandardItemModel ──► _MultiColumnFilterProxy ──► QTableView
       │                       │                       │
       │                       └ filterAcceptsRow      │
       │                         + sort()              │
       └── itemChanged() ──► _on_source_item_changed  ─┤
                                                       │
                              cellEdited / rowChecked ─┘
```

view 永远拿 proxy；任何 `index` 都需要 `proxy.mapToSource()` 才能拿到源行号。

#### (2) 筛选流程

```
用户点表头漏斗
   │
   ▼
_FilterHeaderView.mousePressEvent()
   │ 判断点击位置在 icon_rect 内 + 图标可见 (hover 或 active)
   ▼
emit filterClicked(column, global_pos)
   │
   ▼
MyTable._show_filter_menu()
   │ 收集源模型该列的所有唯一值
   ▼
_FilterPopup (QFrame, Qt.Popup) 显示
   │ 用户勾选 / 取消 / 搜索 / 升序 / 降序
   ▼
emit filterChanged(col, allowed_set | None)
   │
   ▼
MyTable._on_filter_changed()
   │
   ├─► proxy.set_column_filter(col, allowed)  → invalidateFilter()
   │
   └─► header.set_active(col, allowed is not None)  → 漏斗变蓝+红点
```

#### (3) 排序流程

- Qt 自带的 `setSortIndicatorShown(False)` 关闭原生指示器
- `_FilterHeaderView.paintSection` 在每次重绘时自己画双箭头：
  - 当前列 == `sortIndicatorSection()` → 高亮当前方向
  - hover 但未排序 → 灰色双箭头（提示可点）
  - 其它 → 不画
- 点击表头列名 / 点击双箭头位置 → 走 Qt 默认的 `sectionClicked` → `sortByColumn()`
- 点击漏斗位置 → `mousePressEvent` 内 return（不冒泡），不触发排序

#### (4) 行勾选 / 编辑 / 删除

- **勾选列**：`set_checkable_rows` 调用 `_apply_flags_to_all`，给该列每个 item 加 `Qt.ItemIsUserCheckable` 并初始化为 `Qt.Unchecked`，同时把该列加进 `_skip_filter_columns`（不画漏斗）。
- **编辑列**：`set_editable_columns` 改 `setEditTriggers`，并给目标列 item 加 `Qt.ItemIsEditable` 标志位。
- **数据变更回调**：`QStandardItemModel.itemChanged` 信号被表统一接管 → `_on_source_item_changed`：
  - 该 item 在勾选列 → emit `rowChecked(row, checked)`
  - 该 item 在可编辑列 → emit `cellEdited(row, col, value)`
- **删除**：`delete_rows` 对源行号去重 + 降序遍历 `removeRow`，避免删除时索引变化。

### 4.3 MyCombo 实现原理

> MyCombo 的类协作图、5 个关键流程（焦点与 IME、输入即过滤、点击外部关闭、显示/编辑模式、作用于可见项的 3 按钮）全部在 [MY_COMBO.md § 11](MY_COMBO.md#11-实现原理) 详细说明。

---

## 5. 已修复的 Bug 复盘（踩坑记录）

按时间顺序整理，便于二次开发时避免重复踩坑。

### 5.1 点击勾选框反而切换不了

**现象**：`QListWidgetItem` 设了 `Qt.ItemIsUserCheckable`，但点击 indicator（小方框）后状态不变；点击文字反而能切换。

**根因**：Qt 自带的"点击 indicator 切换 checkState"行为已经触发了一次切换，再加上代码里 `itemClicked.connect(...)` 又手动切换一次 → 净结果是没变化（点文字时则是只切换一次）。

**修复**：
- 移除 `itemClicked` 的手动切换
- 自定义 `_CheckListWidget(QListWidget)`，重写 `mousePressEvent`：判断点击的 item 是否可勾选，若是则统一切换一次状态后 `event.accept()` 阻止默认行为

```python
class _CheckListWidget(QListWidget):
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            item = self.itemAt(event.position().toPoint())
            if item is not None and item.flags() & Qt.ItemIsUserCheckable:
                new_state = (Qt.Unchecked if item.checkState() == Qt.Checked
                             else Qt.Checked)
                item.setCheckState(new_state)
                event.accept()
                return
        super().mousePressEvent(event)
```

效果：点击行的任意位置（勾选框 / 文字 / 留白）都精确切换一次。

### 5.2 表格筛选弹窗里的搜索框不能输入中文

**现象**：弹出的列筛选菜单中有一个搜索框，英文能输入，中文 / 日文 / 韩文输入法完全没反应。

**根因**：原来弹窗用 `QMenu` 实现，`QMenu` 自身会拦截 IME 事件以做菜单导航（按字母跳到匹配项），导致 IME 组合事件无法到达搜索框。

**修复**：放弃 `QMenu`，改用 `QFrame(parent, Qt.Popup)`（保留 popup 行为：点击外部自动关闭），中文输入法立刻正常。

### 5.3 排序指示器与漏斗图标位置重叠

**现象**：表头右侧 Qt 自带的排序三角和我们自绘的漏斗叠在一起，互相挡。

**修复**：
- `setSortIndicatorShown(False)` 关掉原生指示器
- 在 `paintSection()` 中自绘"上下双箭头" SVG（活跃方向蓝色）
- 用一组几何常量 `FILTER_SIZE / FILTER_MARGIN / SORT_W / SORT_GAP` 严格约束位置：排序在漏斗左侧固定 6 px 间隔，永不重叠
- 表头 stylesheet `padding-right: 42px` 给两个图标留够空间
- 用单测断言：`for col in range(N): sort.right() <= filter.left()`

### 5.4 漏斗一直显示太喧闹

**现象**：每一列表头都常驻一个漏斗图标，视觉噪声大。

**修复**：在 `_FilterHeaderView` 引入 `_hover_section`，`mouseMoveEvent` 跟踪当前 hover 列、`leaveEvent` 复位。`paintSection` 改为：

```python
if not active and not hover:
    return       # 默认完全不画
```

只在 hover 该列或该列已有筛选时才画漏斗。`mousePressEvent` 也只在图标可见时才响应点击，避免点不到的位置触发筛选。

### 5.5 多选下拉点一次勾选就关闭面板（**最严重**）

> 已迁到 [MY_COMBO.md § 12.1](MY_COMBO.md#121-多选下拉点一次勾选就关闭面板最严重)：FocusOut 关闭逻辑 + `Qt.Tool` 窗口 DPI 误判两个根因 + 改用 widget 父链判断的修复代码。

### 5.6 弹窗"取消"按钮语义歧义

> 已迁到 [MY_COMBO.md § 12.2](MY_COMBO.md#122-弹窗取消按钮语义歧义)：原"取消"按钮同时清除勾选+关面板，拆成"全选/反选/取消"三按钮单一职责。

### 5.7 `set_theme()` 触发 `QLayout` 警告

> 已迁到 [MY_COMBO.md § 12.3](MY_COMBO.md#123-set_theme-触发-qlayout-警告)：`_apply_style()` 同时跑 stylesheet 和 widget tree 导致 `set_theme()` 二次添加布局；拆为 `_apply_style()` (stylesheet only) + `_build_widgets()` (once) 修复。

### 5.8 输入框焦点位置不明显

**现象**：用户分不清主输入框在哪、是否聚焦。

**修复**：给 `QLineEdit` 加 2 px 底部边框：默认浅灰、聚焦变蓝；同时保留外层圆角边框聚焦时变蓝，形成双重焦点提示。两种状态都用 2 px（不变），避免聚焦时文字位置抖动 1 px。

### 5.9 筛选默认"全勾选"应该是"不过滤"

**v1 错误方案（已废弃）**：引入 `_unfiltered: bool` 状态，弹窗打开时所有项视觉上已勾选但 flag 标记"未筛选"；用户取消勾选 → flag 翻 False → 真正的 filter 激活。

**问题**：
- 视觉状态 ≠ 实际状态，**用户认知负担大**：明明看到"全勾"却要点"确定"才生效，第一次用必然困惑。
- 弹窗打开后用户顺手再点"全选"试图"反选"（清空），得到的是空 selection + `_unfiltered=False` → 走 `set()` 分支 → 表格 0 行。**没达到"反选"预期，反而清空了表格。**
- Excel / Outlook / 大多数表格控件的 filter 弹窗默认就是"全不勾选"，用户主动勾选要保留的值——这才符合"点什么是筛选什么"的操作直觉。

**v2 正确方案（Excel-like，零心智负担）**：
- 删除 `_unfiltered` flag。**弹窗打开默认全部 Unchecked**（除非有 prior filter 还原）。
- `确定` 按钮语义改写：
  - 空 selection → `filterChanged.emit(column, None)` = 不过滤 = 显示全部
  - 非空 selection → `filterChanged.emit(column, set(_selected))` = 只保留勾选项
- "全选" `QCheckBox` 改为 tristate toggle（Unchecked/PartiallyChecked/Checked）：
  - 第一次点（Unchecked）→ Checked（全勾）
  - 第二次点（Checked）→ Unchecked（全不勾 = "反选效果"）
  - 部分勾时点 → Checked（全勾）
- "清除筛选" 按钮保留——显式清掉所有列的 filter（含 numeric）。
- 视觉验证（截图为证）：
  - 首次打开（无 prior）：5 个城市全 Unchecked，"全选"是 Unchecked
  - 点"全选" 1 次：5 个全 Checked，"全选"是 Checked
  - 点"全选" 2 次：5 个全 Unchecked，"全选"是 Unchecked ← "反选效果"
  - reopen with prior `{"北京","上海"}`：前 2 个 Checked，后 3 个 Unchecked，"全选"是 PartiallyChecked

**二次修复 — 真实 click 路径下第二次 click 无效**：

v2 第一版用 `if self._select_all.checkState() == Qt.Checked: state = Unchecked else: state = Checked` 决定 toggle 方向。看起来对，但用 `QTest.mouseClick` 真实点击复测时第二次 click 无任何反应（5/5 item 保持 Checked）。

根因：`QCheckBox.setTristate(True)` 内部有 3-state cycle（Unchecked → PartiallyChecked → Checked → Unchecked），我们在 handler 里又 `setCheckState(state)` 显式覆盖状态，**把 Qt 的 "next click" 状态机搞乱**——Qt 下一次 click 时基于混乱状态做 cycle，结果状态没变、clicked 信号仍发、handler 跑、但 list 不动。

修复：不再依赖 `self._select_all.checkState()`，**直接看 list 的实际状态**：
```python
n = self._list.count()
all_checked = n > 0 and all(
    self._list.item(i).checkState() == Qt.Checked for i in range(n)
)
state = Qt.Unchecked if all_checked else Qt.Checked
```

这样无论 Qt 怎么改 QCheckBox 自己的 state，都以 list 数据为准。复测 `QTest.mouseClick` × 3 + 4 个场景（空/prior/partial/search）全部 PASS。

### 5.10 数字列需要"按数字比较"开关

**现象**：工资 / 年龄这种数字列，列表里有 30, 35, 41... 多选时只能 `set = {30, 35}` 这种枚举式筛选，要找"年龄 > 30 的所有员工"做不了。

**修复**：
- `MyTable.set_column_numeric(column, enabled=True)` 标记列
- `MyTable.__init__(skip_filter_columns=[...])` 在构造时禁用不需要筛选的列
- `_FilterPopup` 加"按数字比较" `QCheckBox` —— 勾上后列表/搜索框 `hide()`，显示"运算符 `QComboBox` + 数字 `QDoubleSpinBox`"
- `_MultiColumnFilterProxy` 加 `set_column_numeric_filter(column, op, value)` —— 6 个 op：=, !=, >, >=, <, <=；非 float 行被过滤掉
- 文本 filter 和数字 filter 同一列互斥 —— 选数字模式时自动清掉文本 filter，反之亦然

### 5.11 数字列需要"多条件 AND"范围筛选

**现象**：单 op+value 满足不了"工资 > 20000 且 < 25000"这种范围筛选；用户只能要么 `> 20000`（把 25500 也带进来），要么 `< 25000`（把 13500 也带进来），或者放弃数字 filter 改回多选枚举。

**修复**：
- 数据：`proxy.set_column_numeric_filter(column, conditions)` 接受 `list[tuple[str, float]]`；多个条件按 **AND** 组合
- UI：抽出 `_NumericConditionRow` 内部类，封装 `QComboBox + QDoubleSpinBox + QToolButton(×)`
- popup 用动态 `QVBoxLayout` 装多个 row + 一个"+ 添加条件"按钮；至少保留 1 行（删到 1 行时不删而是 reset 为默认值）
- 打开 popup 时从 `numeric_filter` 恢复所有行；初始空则放 1 个 `("=", 0.0)` 默认行
- 信号 `numericFilterChanged` 从 `(column, op, value)` 改成 `(column, list|None)`，传 `None` 表示清空
- `MyTable.column_numeric_filter` 返回 `list | None`（之前是单 tuple — 内部 API breaking，但项目里没消费者）

### 5.12 表头上下箭头跟漏斗重叠 / 出现两列上下箭头

**现象**：表头里**同一列**上能看到 2 个上下箭头 —— 一个是 Qt 默认的 sort indicator，另一个是我们 `_FilterHeaderView.paintSection` 自绘的双箭头；两个叠加在一起。同时排序列的 sort indicator 又跟 hover 列的漏斗离得很近，看着像重叠。

**根因**：
- `_FilterHeaderView.__init__` 调了 `self.setSortIndicatorShown(False)` 关掉 Qt 默认 sort indicator
- 但 `QTableView.setHorizontalHeader(header)` 和 `QTableView.setSortingEnabled(True)` **会重置**该 flag 回 `True`
- 之后 `super().paintSection(...)` 仍然画原生 sort indicator，**叠加**在我们自绘双箭头上 = 视觉上"两列上下箭头"

**修复**：在 `MyTable.__init__` 末尾，**所有** `setHorizontalHeader / setSortingEnabled / setSelectionBehavior / setEditTriggers / ...` 都完成**之后**，再调一次 `self._header.setSortIndicatorShown(False)`，确保最终状态正确。

```python
self.setSortingEnabled(True)
self.setAlternatingRowColors(True)
self.setSelectionBehavior(QAbstractItemView.SelectRows)
...
# 关键: 必须在 setHorizontalHeader / setSortingEnabled 之后再次关闭
self._header.setSortIndicatorShown(False)
```

视觉验证（`_FilterHeaderView` 的 paintSection 仍保留）：
- 排序列：1 个自绘双箭头（升序上蓝下灰，降序上灰下蓝）
- hover 列：1 个灰色双箭头 + 灰色漏斗，6 px 间距不重叠
- skip 列：排序箭头贴右边缘，无漏斗

---

## 附：开发与测试

烟雾测试可以在无显示环境下跑（CI 友好）：

```powershell
$env:QT_QPA_PLATFORM = "minimal"
uv run python -c "from main import DemoWindow; from PySide6.QtWidgets import QApplication; from PySide6.QtCore import QTimer; import sys; app = QApplication(sys.argv); w = DemoWindow(); w.show(); QTimer.singleShot(150, app.quit); sys.exit(app.exec())"
```

完整可视化运行：

| 控件 | 命令 |
|---|---|
| **MyTable** | `uv run python main.py` |
| **MyCombo** | `uv run python test_my_combo.py` |


