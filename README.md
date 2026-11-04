# mypyside6 — 四个自绘 Qt 控件

PySide6 实现的四个可复用控件：**Badge**（数字角标）、**MyCombo**（多选下拉）、
**MyTable**（带列筛选 / 勾选 / 行内操作的表）、**DragBar**（可拖拽工具栏）。

设计原则：**控件不写死任何文案 / 尺寸 / 颜色**。每个控件都有一套默认配置常量，
在构造时用关键字参数或一个字典覆盖即可，默认外观与行为保持不变。

```bash
uv run python demo.py     # 运行四个控件的演示
```

```
myside6/
├── demo.py          # 演示（4 个 Tab）
├── widgets/         # 控件本体
│   ├── badge.py
│   ├── my_combo.py
│   ├── my_table.py
│   └── drag_bar.py
├── pyproject.toml
└── uv.lock
```

---

## 最小可运行示例

把下面这段存成 `mini.py`（与 `widgets/` 同级），然后 `uv run python mini.py`，
四个控件会同时出现在一个窗口里。**全程只覆盖了 3 个配置项，其余全走默认值。**

```python
import sys

from PySide6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget

from widgets import Badge, DragBar, MyCombo, MyTable

app = QApplication(sys.argv)
win = QWidget()
lay = QVBoxLayout(win)

combo = MyCombo(texts={"ok": "应用"})                # 只改「确定」按钮文案
combo.set_items(["北京", "上海", "广州"])
combo.selectionChanged.connect(lambda v: print("选中:", v))

table = MyTable(metrics={"row_height": 34})          # 只改行高
table.set_data(["城市", "人口"], [["北京", 2189], ["上海", 2487]])

btn = QPushButton("下载")
Badge(target=btn, color="#1a73e8").bind(["a", "b"])  # 角标自动跟随列表长度

bar = DragBar(style={"background": "#fafafa", "border_radius": 8})
bar.add_item("folder", "文件夹", "folder")
bar.add_item("calc", "计算器", "accessories-calculator")
bar.snapshot()                                       # 记录重置基线

lay.addWidget(combo)
lay.addWidget(table)
lay.addWidget(btn)
lay.addWidget(bar)
win.resize(560, 460)
win.show()
sys.exit(app.exec())
```

各控件最少只要 1~2 行就能用起来：

| 控件 | 最小用法 | 效果 |
| --- | --- | --- |
| `MyCombo` | `MyCombo().set_items(["北京", "上海"])` | 空配置即可多选下拉 |
| `MyTable` | `MyTable().set_data(["城市"], [["北京"]])` | 自动列宽 + 漏斗筛选 |
| `Badge` | `Badge(target=btn).bind(data)` | 角标自动跟数据条数 |
| `DragBar` | `DragBar().add_item("folder", "文件夹", "folder")` | 可拖拽、可删除 |

---

## 通用约定

| 概念 | 含义 |
| --- | --- |
| `texts` | 所有可见文案（按钮、占位符、提示、tooltip、后缀） |
| `metrics` | 所有尺寸（高度、宽度、内边距、图标大小、行高） |
| `theme` / `style` | 所有颜色（背景、边框、主色、悬停色） |

三者都是「默认 dict + 你的 dict」浅合并：**只传需要改的键**就行。

```python
from widgets import (
    MyCombo, COMBO_TEXTS, COMBO_METRICS,
    MyTable, TABLE_TEXTS, TABLE_METRICS,
    DragBar, DRAGBAR_STYLE,
    Badge,
)
```

```python
# 只改一个按钮文案，其余全部保持默认
combo = MyCombo(texts={"ok": "Apply"})
# 只把行高改成 36
table = MyTable(metrics={"row_height": 36})
# 只换垃圾桶图标
bar = DragBar(trash_icon="✖")
```

---

## Badge — 数字角标

贴在目标控件右上角的圆形数字角标，数字宽度自适应（1 位 → 4 位）。

```python
from widgets import Badge

Badge(target=btn, color="#ea4335").bind(["a", "b", "c"])   # → 3
```

### 构造参数

| 参数 | 默认 | 说明 |
| --- | --- | --- |
| `target` | `None` | 依附的控件（角标会父化到它的顶层窗口，不被裁剪） |
| `color` | `"#ea4335"` | 背景色 |
| `text_color` | `"#ffffff"` | 文字色 |
| `max_count` | `999` | 超过后显示为 `999+` |
| `min_size` | `20` | 最小直径（px） |
| `padding` | `8` | 文字两侧留白，重新计算直径时使用 |
| `font_size` | `None` | 像素字号，`None` 用控件默认字体 |
| `overflow_suffix` | `"+"` | 溢出后缀，可改成 `"…"` 或 `"+"` |
| `offset` | `(0, 0)` | 相对右上角的额外偏移 |
| `poll_ms` | `None` | 轮询间隔；传值等价于调用 `Badge.set_poll_interval()` |

### 方法

| 方法 | 说明 |
| --- | --- |
| `bind(source)` | 绑定数据源，返回 `self` 便于链式调用 |
| `refresh()` | 立即重新读取数据源 |
| `set_count(n)` / `count` | 设置数字（`<=0` 时自动隐藏） |
| `set_color(c)` / `set_text_color(c)` | 改配色 |
| `set_max_count(n)` | 改溢出上限 |
| `Badge.set_poll_interval(ms)` | **类方法**，调整共享轮询间隔（默认 300 ms） |

`bind()` 支持的数据源：

| 类型 | 行为 |
| --- | --- |
| `QAbstractItemModel` | 监听 `rowsInserted` / `rowsRemoved` / `modelReset`，实时更新 |
| 带 `changed` 信号的对象 | 实时更新 |
| `list` / `dict` / `str` / `callable` | 由轮询定时器每 ~300 ms 重读 |

需要「改列表立刻刷新」时用现成的包装类型：

```python
from widgets import Badge, BadgeList, BadgeDict

items = BadgeList(["a", "b"])
Badge(target=btn).bind(items)
items.append("c")           # 角标立即变 3

d = BadgeDict({"x": 1})
Badge(target=btn2).bind(d)
d["y"] = 2                  # 角标立即变 2
```

> 角标由目标控件持有强引用，`Badge(target=btn).bind(items)` 这种不回存变量的写法
> 不会被垃圾回收；控件销毁时角标一起销毁。

---

## MyCombo — 多选下拉

可编辑的多选下拉框：主控件是真正的 `QLineEdit`，可输入、选择、复制粘贴；
输入即过滤；下拉面板不会抢走焦点（中文输入法可正常使用）。

```python
cb = MyCombo(placeholder="选择城市...")
cb.set_items(["北京", "上海", "广州"])
cb.selectionChanged.connect(lambda v: print(v))
```

### 构造参数

| 参数 | 默认 | 说明 |
| --- | --- | --- |
| `parent` | `None` | 父控件 |
| `placeholder` | `texts["placeholder"]` | 空状态提示，覆盖 `texts["placeholder"]` |
| `theme` | `DEFAULT_THEME` | 配色字典（见下） |
| `texts` | `DEFAULT_TEXTS` | 文案字典 |
| `search_in_popup` | `True` | 面板内是否显示搜索框 |
| `string_only` | `False` | 解锁输入框为自由文本模式 |
| `columns` | `2` | 面板列数 |
| `max_col_chars` | `20` | 单列最大字符数；`0` = 不限 |
| `min_height` | `34` | 收起态高度 |
| `min_width` | `200` | `sizeHint` 的宽度下限 |
| `arrow_width` | `26` | 右侧箭头按钮宽度 |
| `popup_min_width` | `260` | 面板宽度下限 |
| `popup_min_height` | `240` | 面板高度下限 |
| `list_min_height` | `180` | 列表最小高度 |
| `list_max_height` | `320` | 列表最大高度（超出滚动） |
| `item_min_height` | `24` | 列表行高下限 |
| `popup_chrome` | `44` | 面板左右边框 + 内边距预算（算列宽用） |
| `separator` | `texts["separator"]` | 已选标签的连接符，默认 `", "` |

### `texts` 键

| 键 | 默认 |
| --- | --- |
| `placeholder` | `请选择...` |
| `search_placeholder` | `搜索...` |
| `sort_asc` / `sort_desc` | `↑ 升序` / `↓ 降序` |
| `select_all` / `invert` / `reset` | `全选` / `反选` / `重置` |
| `cancel` / `ok` | `取消` / `确定` |
| `count` | `已选 {n} 项`（`{n}` 会被替换） |
| `hover_only` / `hover_only_tip` | `仅筛此项` / `把筛选替换为只看这一项` |
| `separator` | `, ` |

### 主题

`DEFAULT_THEME` / `GOOGLE_THEME` / `TENCENT_THEME` / `GITHUB_THEME`，
也可用 `THEMES["github"]` 取。全部是完整字典，取一份改单个键即可。

```python
from widgets import THEMES

cb.set_theme({**THEMES["tencent"], "border_radius": 8})
```

主要键：`background`、`text_color`、`border_color`、`border_color_focus`、
`border_width`、`border_radius`、`underline_color(_focus)`、`underline_width`、
`arrow_color(_hover)`、`selection_bg`、`font_size`、`padding`、
`popup_background`、`popup_border_color`、`popup_border_radius`、
`list_background`、`list_border_color`、`list_border_radius`、`list_font_size`、
`list_item_padding`、`list_item_hover_bg`、`list_item_selected_bg/fg`、
`btn_background`、`btn_hover_bg`、`btn_border_color`、`btn_border_radius`、
`btn_padding`、`btn_font_size`、`btn_primary_bg`、`btn_primary_hover_bg`、
`btn_primary_color`、`btn_primary_border`、`btn_hint_color`、
`search_background`、`search_border_color`、`search_border_focus`、
`search_border_radius`、`search_padding`、`search_height`。

### 方法

| 方法 | 说明 |
| --- | --- |
| `set_items(iterable)` | 元素可为 `label` 或 `(label, value)` |
| `set_dict_items(d, swap=False)` | 默认 `value` 做标签、`key` 做值；`swap=True` 反向 |
| `items()` | 返回 `[(label, value), ...]` |
| `selected_values()` / `selected_labels()` | 当前选中 |
| `set_selected_values(values)` / `clear_selection()` / `select_all()` | 批量设置 |
| `value()` | 输入框当前文本（`string_only` 模式下即用户输入） |
| `line_edit()` | 取出内部 `QLineEdit`（可挂 validator） |
| `show_popup()` / `hide_popup()` | 手动开关面板 |
| `set_theme(d)` / `set_columns(n)` / `set_max_col_chars(n)` | 运行时调整 |
| `set_search_in_popup(b)` / `is_search_in_popup()` | 面板内搜索框开关 |
| `set_string_only(b)` / `is_string_only()` | 自由文本模式开关 |
| `theme()` / `texts()` / `metrics()` | 返回当前配置副本 |

信号：`selectionChanged(list)`、`popupShown()`、`popupHidden()`。

---

## MyTable — 筛选 / 勾选 / 编辑 / 删除

带「Excel 式列筛选」的表格：文本勾选、数值比较（多条 AND）、日期范围三种模式；
列头可拖拽重排、点击排序；可选行勾选、单元格编辑、行内操作按钮。
日期筛选面板的年份/月份既可在网格中点选，也可直接键入跳转；年份面板支持滚轮逐年平移窗口（2016→2015…／2036→2037…）。

```python
from widgets import MyTable, ActionDelegate, ACTION_STYLES

table = MyTable(skip_filter_columns=[6])
table.set_data(
    headers=["", "姓名", "部门", "城市", "年龄", "入职日期", "操作"],
    rows=[[False, "张三", "技术", "北京", 30, "2021-03-15", ""]],
)
table.set_checkable_rows(True, 0)
table.set_editable_columns([1, 2, 3, 4, 5])
table.set_column_numeric(4)          # 年龄列启用「按数字比较」

d = ActionDelegate("删除", parent=table, style=ACTION_STYLES["delete_solid"])
d.clicked.connect(lambda row: table.delete_rows([row]))
table.setItemDelegateForColumn(6, d)
```

### 构造参数

| 参数 | 默认 | 说明 |
| --- | --- | --- |
| `skip_filter_columns` | `()` | 不显示筛选图标的列（如操作列） |
| `texts` | `DEFAULT_TEXTS` | 文案字典 |
| `metrics` | `DEFAULT_METRICS` | 尺寸字典 |

### `texts` 键

筛选面板：`sort_asc` `sort_desc` `select_all` `search_placeholder` `invert`
`reset` `cancel` `ok` `hover_only` `hover_only_tip` `blank`（空值显示，默认 `(空白)`）
`reset_tip_text` `numeric_toggle` `add_condition` `add_condition_tip`
`remove_condition_tip` `reset_tip_numeric` `op_eq` `op_ne` `op_gt` `op_ge` `op_lt` `op_le`
`date_toggle` `date_hint` `ignore_sep` `ignore_sep_tip` `reset_tip_date`

日期选择器：`preset_7d` `preset_30d` `preset_month` `preset_year` `preset_all`
`prev_month_tip` `next_month_tip` `pick_year_tip` `pick_month_tip` `today` `today_tip`
`year_placeholder` `month_placeholder` `jump` `year_hint`（含 `{min}` `{max}`）
`month_hint` `year_data_hint`
（含 `{lo}` `{hi}`）`unbounded` `no_range` `year_suffix` `month_suffix`
`date_format`（默认 `yyyy-MM-dd`）`weekdays`（7 个元素的元组）

表体：`delete_selected` `delete_checked`（含 `{n}`）`check_all` `uncheck_all` `clear_filters`

### `metrics` 键

| 键 | 默认 | 说明 |
| --- | --- | --- |
| `row_height` | 30 | 行高 |
| `table_font_size` / `header_font_size` | 13 | 表体 / 表头字号 |
| `header_pad_left` / `header_pad_right` | 10 / 42 | 表头内边距（右侧留给筛选图标） |
| `min_section` / `default_section` | 80 / 140 | 列最小 / 默认宽度 |
| `filter_icon_size` / `filter_margin` | 16 / 6 | 漏斗图标尺寸 / 右边距 |
| `sort_w` / `sort_h` / `sort_gap` / `sort_text_gap` | 8 / 14 / 6 / 6 | 排序双箭头 |
| `check_box_size` / `check_box_margin` | 14 / 8 | 表头复选框 |
| `check_column_width` | 56 | 勾选列宽 |
| `col_extra` / `col_min` | 30 / 120 | `set_data` 自动列宽：`内容宽 + col_extra`，不小于 `col_min` |
| `cal_cell_w` / `cal_cell_h` / `cal_header_h` | 34 / 28 / 24 | 日历格子 / 星期行 |
| `year_span` | 10 | 年份网格为「当前年 ± year_span」 |
| `year_min` / `year_max` | 1900 / 2999 | 年份输入框校验范围 |
| `year_edit_width` / `year_edit_height` | 84 / 24 | 年份 / 月份输入框 |
| `choice_min_width` | 58 | 年 / 月网格按钮最小宽 |
| `list_min_height` / `list_max_height` / `list_min_width` | 180 / 280 / 220 | 筛选列表 |
| `action_radius` 等 | 6 / 6 / 4 / 80 / 30 | 行内按钮默认值（见 `ActionDelegate`） |

### 方法

| 方法 | 说明 |
| --- | --- |
| `set_data(headers, rows)` | 用 Python 数据填充（自动列宽） |
| `setModel(m)` / `sourceModel()` / `proxyModel()` | 模型接口（自动包一层筛选代理） |
| `append_row(values)` | 追加一行，返回源行号 |
| `delete_rows(rows)` / `delete_selected_rows()` / `delete_checked_rows()` | 删除，返回被删的源行号 |
| `set_checkable_rows(True, col=0)` | 该列显示复选框，表头出现「全选」 |
| `checked_rows()` / `set_row_checked(row, b)` / `set_all_checked(b)` | 勾选状态 |
| `set_editable_columns(True / [列] / False)` | 单元格编辑 |
| `set_column_numeric(col, on=True)` | 该列启用数值比较模式 |
| `clear_filters()` | 清除所有列的筛选 |
| `set_filter_skipped_columns(cols)` | 运行时设置不显示漏斗的列 |

信号：`rowsDeleted(list)`、`rowChecked(int, bool)`、`cellEdited(int, int, object)`。

### ActionDelegate（行内按钮）

```python
ActionDelegate(text="删除", parent=table, *,
               style=None,          # 或 ACTION_STYLES["confirm"]
               radius=6, margin_x=6, margin_y=4, min_width=80, min_height=30)
```

`ACTION_STYLES` 预设：`delete` `confirm` `info` `warning` 及
`delete_solid` `confirm_solid` `info_solid` `warning_solid`。
`style` 键：`bg_normal` `bg_hover` `border` `color` `filled`。

---

## DragBar — 可拖拽工具栏

图标 + 文字的工具条：拖拽排序、拖到垃圾桶删除、可跨 Bar 拖放、
Ctrl 多选 / Shift 范围选、撤销（重置）到上次 `snapshot()`。

```python
from widgets import DragBar

apple = {"background": "rgba(250,250,250,0.88)",
         "border": "1px solid rgba(200,200,205,0.5)",
         "border_radius": 10}

bar = DragBar(spacing=8, style=apple)
bar.add_item("folder", "文件夹", "folder")     # name, text, icon
bar.add_item("calc", "计算器", "accessories-calculator")
bar.snapshot()                                 # 记录重置基线
bar.item_moved.connect(lambda name, idx: print(name, idx))
```

`icon` 支持主题图标名、本地路径、HTTP(S) URL。

### 构造参数

| 参数 | 默认 | 说明 |
| --- | --- | --- |
| `fixed_length` | `None` | 固定长度（横向=宽，纵向=高） |
| `spacing` | `6` | 图标间距 |
| `style` | `DEFAULT_STYLE` | 完整配置字典 |
| `closable` | `True` | 右上角显示关闭按钮 |
| `vertical` | `False` | 纵向排列 |
| `item_size` | `64` | 图标块边长 |
| `icon_size` | `28` | 图标绘制尺寸 |
| `label_font_size` | `8` | 文字字号 |
| `trash_size` / `reset_size` | `(56, 60)` | 垃圾桶 / 重置区尺寸 |
| `trash_icon` / `reset_icon` | `🗑` / `↺` | 两个区的图标字符 |
| `close_text` | `×` | 关闭按钮文字 |
| `show_trash` / `show_reset` | `True` | 是否显示这两个区 |

### `DEFAULT_STYLE` 键

容器：`background` `border` `border_radius` `padding`

图标块：`item_size` `icon_size` `icon_top` `label_top` `label_height`
`label_font_size` `item_radius` `item_text_color` `item_icon_color`
`item_hover_fill` `item_selected_fill` `accent` `placeholder_icon`
`icon_font_family` `drag_gap`

区域：`show_trash` `show_reset` `trash_size` `trash_icon` `trash_font_size`
`reset_size` `reset_icon` `reset_font_size` `reset_hover_fill`
`reset_hover_color` `zone_radius`

配色：`danger` `muted` `mid`

关闭按钮：`close_text` `close_size` `close_font_size` `close_color`
`close_hover_color` `close_tip` `header_height`

### 方法

| 方法 | 说明 |
| --- | --- |
| `add_item(item, text=None, icon=None)` | 追加；`item` 可传 `DragBarItem`；重名返回 `None` |
| `insert_item(index, item, text=None, icon=None)` | 插入到指定位置 |
| `remove_item(name)` / `clear()` | 删除 |
| `items()` / `selected_items()` | 当前项 / 选中项名 |
| `select_all()` / `deselect_all()` | 选择 |
| `set_spacing(px)` / `set_style(d)` | 运行时调整，`set_style` 会立刻换肤 |
| `snapshot()` | 记录当前项为重置基线 |
| `reset()` | 恢复到基线 |

信号：`item_moved(str, int)`、`item_removed(str)`、`selection_changed(list)`、`closed()`。

`DragBarItem` 本身：`name`、`text`、`icon_src`、`clicked(ctrl, shift)`、`icon_changed()`。

---

## 常见改动速查

```python
# 全局换英文界面
en = {
    "ok": "OK", "cancel": "Cancel", "select_all": "Select all",
    "invert": "Invert", "reset": "Reset", "search_placeholder": "Search...",
}
MyTable(texts=en)
MyCombo(texts=en)

# 更紧凑的表格
MyTable(metrics={"row_height": 26, "default_section": 110, "col_extra": 20})

# 更大的下拉行高 + 单列
MyCombo(columns=1, item_min_height=30, list_max_height=400)

# 只改角标溢出样式
Badge(target=btn, overflow_suffix="…", max_count=9)

# 极简工具条：不要垃圾桶和重置
DragBar(show_trash=False, show_reset=False, closable=False)
```
