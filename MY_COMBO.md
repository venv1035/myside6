# MyCombo 控件文档

> 本文档专门介绍 `MyCombo` 多选下拉勾选输入框。**与 `MyTable` 完全分离**：Excel 风格表格相关的内容请看 [README.md](README.md)。

---

## 1. 简介

继承自 `QWidget`。视觉上是一个 `QLineEdit + 下拉箭头`，行为上是一个**真正可输入的多选下拉框**：用户可以输入文字（同时即过滤下拉列表），输入框始终持有键盘焦点和 IME，下拉面板永远不会和编辑冲突。

核心特点：

- **真实可编辑** — 不是把下拉当"选择器"，用户随时能输入文字
- **IME 友好** — 弹窗用 `Qt.Tool | Frameless + WA_ShowWithoutActivating` + `NoFocus` 子控件，永不抢 IME 焦点
- **输入即过滤** — 任意字符按下都自动开弹窗并按子串过滤列表
- **3 个操作按钮**（全选 / 反选 / 取消）— 全部作用于**当前可见项**，结合输入过滤可做"批量勾选所有含 XX 的项"
- **键值对友好** — `set_dict_items({key: value})` 一行接入；`swap=True` 互换
- **可解锁为"自由输入"** — `string_only=True` 时输入框变成完全可编辑的纯文本框，所有多选 / 勾选 / 按钮 / 信号行为**完全保留**
- **44-key 主题** — 一个 `DEFAULT_THEME` dict 覆盖所有可视部分，运行时 `set_theme()` 立即切换

---

## 2. 快速开始

```python
from PySide6.QtWidgets import QApplication
import sys
from widgets import MyCombo

app = QApplication(sys.argv)

cb = MyCombo(placeholder="请选择城市...")
cb.set_items(["北京", "上海", "广州", "深圳", "杭州", "成都"])
cb.set_selected_values(["北京", "上海"])
cb.selectionChanged.connect(lambda values: print("当前选中:", values))
cb.resize(300, 34)
cb.show()
sys.exit(app.exec())
```

当数据本身就是一份 *代码 → 展示文本* 的 dict 时，用 `set_dict_items` 一行搞定：

```python
COUNTRY_CN = {
    "name":    "中国",
    "towname": "华夏",
    "abbr":    "CN",
}
cb.set_dict_items(COUNTRY_CN)
# 下拉框显示 "中国" / "华夏" / "CN"
# selectionChanged 回调收到 ["name"] / ["name", "abbr"] 等 key
```

如果反过来，dict 的 key 是给人看的，value 是程序要用的：

```python
DISPLAY_TO_CODE = {"北京": "BJ", "上海": "SH", "广州": "GZ"}
cb.set_dict_items(DISPLAY_TO_CODE, swap=True)
# 下拉框显示 "北京" / "上海" / "广州"
# selectionChanged 回调收到 ["BJ"] / ["SH", "GZ"] 等 value
```

> 重复 value 不会冲突：item 按 `value`（默认模式下即 dict 的 key）区分勾选状态。

---

## 3. API 参考

### 3.1 构造

```python
MyCombo(
    parent: QWidget | None = None,
    placeholder: str = "请选择...",
    buttons_position: str = "top",     # "top" 或 "bottom"
    theme: dict | None = None,         # 颜色 / 圆角 / 字号 主题覆盖
    search_in_popup: bool = True,     # 弹窗内是否带搜索框
    string_only: bool = False,           # 是否为"自由输入"模式（弹窗只作提示）
)
```

| 参数 | 说明 |
|---|---|
| `placeholder` | 输入框无选中、无输入时显示的占位文字 |
| `buttons_position` | 弹窗中"全选/反选/取消"按钮区的位置：列表上方 (`"top"`) 或下方 (`"bottom"`) |
| `theme` | 部分覆盖 `DEFAULT_THEME` 的主题字典（见下文 *主题* 一节） |
| `search_in_popup` | 弹窗内**是否带搜索框**。默认 `True`——会在按钮区和列表之间显示一个 `QLineEdit`，与主控件双向同步；设为 `False` 时弹窗退回纯勾选面板，过滤只能在主控件输入 |
| `string_only` | **解锁输入框**。默认 `False`（多选勾选：输入框显示当前已选项的标签拼接）。设为 `True` 时输入框**完全可编辑**且不会被选中项覆盖，但**所有多选/勾选/按钮/信号行为完全不变**——只是多了一个 `value() -> str` 让你拿到用户输入的字符串。详见下文 *解锁输入框（string_only）* 一节 |

### 3.2 数据 / 选中

| 方法 | 说明 |
|---|---|
| `set_items(items)` | 接受字符串列表（label = value）或 `(label, value)` 元组列表 |
| `set_dict_items(d, *, swap=False)` | 从 `{key: value}` 批量填充。默认 *value* 展示，*key* 操作；`swap=True` 互换 |
| `items() -> list[tuple[str, object]]` | 返回当前所有项（始终是规范化后的 `(label, value)` 形式） |
| `selected_values() -> list` | 已选项的 value 列表（保持 items 中的顺序） |
| `selected_labels() -> list[str]` | 已选项的 label 列表 |
| `set_selected_values(values)` | 程序化设置选中项 |
| `select_all()` | 选中全部 |
| `clear_selection()` | 取消所有选中 |
| `value() -> str` | 当前输入框原始文本（**单一字符串**，不是列表）。`string_only` 模式下用于读取用户自由输入 |
| `input_text() -> str` | `value()` 的别名 |

### 3.3 弹窗控制

| 方法 | 说明 |
|---|---|
| `show_popup()` | 打开下拉面板 |
| `hide_popup()` | 关闭下拉面板 |
| `line_edit() -> QLineEdit` | 暴露内部 `QLineEdit`（可挂 validator / completer 等） |
| `is_search_in_popup() -> bool` | 当前是否启用弹窗内搜索框 |
| `set_search_in_popup(enabled: bool)` | 运行时切换弹窗内搜索框。若弹窗已打开会先关再开 |
| `is_string_only() -> bool` | 输入框当前是否处于"自由编辑"模式 |
| `set_string_only(enabled: bool)` | 运行时切换自由编辑开关。切回 `False` 时立即把当前多选状态渲染回输入框 |
| `set_theme(theme: dict)` | 运行时切换主题。完整覆盖 `DEFAULT_THEME` 中给出的 key |

### 3.4 信号

| 信号 | 参数 | 触发时机 |
|---|---|---|
| `selectionChanged` | `list`（最新的 selected_values） | 选中集变化（用户勾选 / API 调用） |
| `popupShown` | — | 弹窗打开时 |
| `popupHidden` | — | 弹窗关闭时 |

---

## 4. 弹窗 3 按钮的语义

按钮区从左到右：**全选 / 反选 / 取消**

| 按钮 | 作用范围 | 是否关闭面板 |
|---|---|---|
| **全选** | 当前**可见**项（结合输入框过滤）→ 全部勾选 | 否 |
| **反选** | 当前**可见**项 → 反转勾选状态 | 否 |
| **取消** | 当前**可见**项 → 全部取消勾选 | 否 |

> 「作用于可见项」的统一语义意味着：在输入框中输入关键词 → 列表只显示匹配项 → 此时点"全选"等同于"批量选中所有匹配 XX 的项"。

关闭弹窗由 **Esc 键**、**点击外部**、**鼠标 hover-leave 220 ms** 触发，**不**由按钮触发——避免误操作丢失"批量选"的中间状态。

---

## 5. 键盘交互

| 键 | 行为 |
|---|---|
| **任意字符** | 自动打开弹窗，把输入文字作为搜索关键词，列表实时过滤 |
| **↓ / ↑** | 弹窗未打开时打开弹窗 |
| **Esc** | 关闭弹窗 |
| **Enter** | 切换"当前唯一可见项"的勾选状态（输入 → Enter 快速添加） |

---

## 6. 视觉细节

- **输入框底部 2 px 边框**：默认浅灰 `#e8eaed`，聚焦变蓝 `#1a73e8`，提示输入焦点位置
- **外层圆角边框**：默认灰，聚焦时整体变蓝
- 已选项显示在输入框内为逗号分隔标签（`A, B, C`）；用户开始输入后才会切换为搜索模式
- 弹窗右上角实时显示 `已选 N 项`
- **hover-leave 220 ms** 自动关闭弹窗（键盘操作不触发——`focusWidget() is not None` 时不计时）

---

## 7. 解锁输入框（string_only）

**核心承诺**：`string_only=True` **保留**多选/勾选/按钮/信号的所有行为——`selected_values()` 仍然返回多选勾选结果，`selectionChanged` 仍然只在勾选变化时发射，"全选/反选/取消"按钮也都还在。

**与默认模式的差异**：

1. **用户在输入框里编辑过之后**，input 框就锁定为用户输入——后续的勾选/取消勾选**不会**覆盖它（这是"自由编辑"）
2. **关闭弹窗时**不再强制把已选标签渲染回 input 框——用户的自由编辑会保留下来
3. 提供 `value() -> str` 直接拿到当前 input 框文本（**单一字符串**，不是列表）

`string_only=False` 时，input 框是"已选标签的拼接只读展示"——任何勾选变化都会**立即**反映到 input 框。`string_only=True` 时，input 框从"展示态"切换为"用户态"——用户一旦开始输入，input 框就**属于**用户。

典型场景：有一份 `code → display` 映射（如 `{"name": "中国"}`），希望给用户参考但**不强迫**他必须从表里选——用户可以随便输：

```python
COUNTRY_CN = {"name": "中国", "towname": "华夏", "abbr": "CN"}
cb = MyCombo(
    placeholder="请输入或从下拉中选择…",
    string_only=True,
)
cb.set_dict_items(COUNTRY_CN)
cb.resize(300, 34)
cb.show()

# 用户在弹窗勾选 "name" -> input 框 = "中国"
# 用户继续在弹窗勾选 "towname" -> input 框 = "中国, 华夏"
# 用户自己编辑 input 框 -> input 框 = 用户输入（不再被覆盖）
# 最终值（字符串）:
print("user text:", cb.value())            # -> "用户输入的任意内容"
print("checked :", cb.selected_values())   # -> ["name", "towname"]
```

行为对照（操作流程与默认模式**完全相同**，差异只在"用户编辑后"）：

| 操作 | `string_only=False` | `string_only=True` |
|---|---|---|
| 点击输入框 | 弹窗打开，进入"搜索"模式 | **完全相同** |
| 在弹窗勾选项 | `selected_values` 变化，input 框变 "已选, 已选" | **完全相同** |
| 点击全选 / 反选 / 取消 | 操作可见项 | **完全相同** |
| 关闭弹窗 | input 框 = "已选, 已选" | input 框 = "已选, 已选"（如果用户没编辑过）；= 用户编辑（如果编辑过） |
| 用户在 input 框编辑 | 通常被覆盖 | **永远不被覆盖**（`value()` 拿到用户输入） |
| `selected_values()` | 勾选的 value 列表 | **完全相同**——多选 API 不受影响 |
| `selectionChanged` | 勾选变化时发射 | **完全相同**——不在每次按键时发射 |
| `value()` / `input_text()` | input 框文本（**单一字符串**） | **完全相同**——aux 模式下的主返回值 |

要点：

1. **`value()` 返回字符串**——不是列表。这是"用户最终值"的入口。
2. **多选仍然工作**——弹窗里的勾选行为、`selected_values()`、`set_selected_values()`、`clear_selection()`、`select_all()` 全部不变。
3. **"自由编辑"是有条件的**——用户**编辑过** input 框之后才"自由"；如果用户**只**勾选，input 框仍然跟随勾选状态。
4. **切换安全**：`set_string_only(False)` 切回正常模式时，立即把当前勾选状态**渲染**回输入框。

---

## 8. 主题与可定制 key

主控件、弹窗、按钮、列表、搜索框的所有可视部分都集中在 [`DEFAULT_THEME`](widgets/my_combo.py) 一个 dict 里。调用时传 `theme={...}` 覆盖子集；运行时调 `set_theme({...})` 立即生效。三个开箱即用的预设：

```python
from widgets import (
    MyCombo,
    DEFAULT_THEME, GOOGLE_THEME, TENCENT_THEME, GITHUB_THEME, THEMES,
)

cb_google  = MyCombo(theme=GOOGLE_THEME)
cb_tencent = MyCombo(theme=TENCENT_THEME)   # 腾讯蓝 + 方角
cb_github  = MyCombo(theme=GITHUB_THEME)    # 灰边 + 蓝聚焦 + 绿 primary

# 按名字取
cb = MyCombo(theme=THEMES["github"])

# 在预设基础上做局部微调
my_theme = {**TENCENT_THEME, "border_radius": 0, "btn_primary_bg": "#ff5722"}
cb = MyCombo(theme=my_theme)

# 运行时切换（如切换深色）
cb.set_theme({"background": "#202124", "text_color": "#e8eaed", ...})
```

可定制 key 分组（44 项，详见 [`DEFAULT_THEME`](widgets/my_combo.py)）：

| 分组 | 关键 key |
|---|---|
| 主输入框 | `background`, `text_color`, `border_color`, `border_color_focus`, `border_width`, `border_radius`, `underline_color`, `underline_color_focus`, `underline_width`, `arrow_color`, `arrow_color_hover`, `selection_bg`, `font_size`, `padding` |
| 弹窗外框 | `popup_background`, `popup_border_color`, `popup_border_width`, `popup_border_radius` |
| 列表 | `list_background`, `list_border_color`, `list_border_radius`, `list_font_size`, `list_item_padding`, `list_item_hover_bg`, `list_item_selected_bg`, `list_item_selected_fg` |
| 按钮（全选 / 反选 / 取消） | `btn_background`, `btn_hover_bg`, `btn_border_color`, `btn_border_radius`, `btn_padding`, `btn_font_size`, `btn_primary_bg`, `btn_primary_hover_bg`, `btn_primary_color`, `btn_primary_border`, `btn_hint_color` |
| **弹窗内搜索框** | `search_background`, `search_border_color`, `search_border_focus`, `search_border_radius`, `search_padding`, `search_height` |

---

## 9. 完整示例（含搜索 + 标签 + 自定义按钮位置）

```python
cb = MyCombo(
    placeholder="选择标签...",
    buttons_position="bottom",
)
cb.set_items([
    ("高优先级", "P0"),
    ("中优先级", "P1"),
    ("低优先级", "P2"),
    ("紧急",   "URGENT"),
    ("已完成", "DONE"),
])

# 初始选中
cb.set_selected_values(["P0", "URGENT"])

# 实时回调
cb.selectionChanged.connect(lambda vals: print("values:", vals))

# 给底层 QLineEdit 加自动补全
from PySide6.QtWidgets import QCompleter
completer = QCompleter([label for label, _ in cb.items()])
cb.line_edit().setCompleter(completer)
```

MVP 调用见 [`test_my_combo.py`](test_my_combo.py)。

---

## 10. 注意事项

1. **不要再给弹窗内的子控件设置 `setFocusPolicy`**。整个弹窗及其所有子控件都被 `__init__` 末尾统一设为 `Qt.NoFocus`，这是输入框 IME 不被打断的关键。
2. **不要给 popup 安装额外的 application-level event filter**。已有一个 `_OutsideClickFilter` 在弹窗显示时被装到 `QApplication`，关闭时被移除；如果你额外装了，注意不要影响 `MouseButtonPress` 的传递。
3. **value 的相等性**：内部用一个 `_key` 函数比较——基本类型（`str / int / float / bool / None`）按值比较，其它对象按 `id()` 比较。所以如果你传自定义对象作为 value 又重新创建对象，可能匹配不上。建议用基本类型作为 value。
4. **失焦不会关闭弹窗**。这是有意为之：弹窗内子控件 NoFocus，`focusWidget()` 在点击勾选时会变成 `None`，如果按"失焦即关闭"会导致点一下就关。关闭由"点击外部 widget"驱动。
5. **弹窗坐标**：`show_popup` 内会做屏幕边界检测，如果屏幕下方放不下会翻转到上方。多显示器场景由 `QApplication.screenAt(global_pos)` 自动定位。
6. **`_apply_style` 与 `_build_widgets` 必须分离**——前者只跑 stylesheet，后者只跑一次 widget tree；合并会导致 `set_theme()` 触发 `QLayout: Attempting to add QLayout ... which already has a layout` 警告。

---

## 11. 实现原理

### 11.1 类协作图

```
┌─────────────────────────────────────────────────────────┐
│        MyCombo (QWidget)                    │
│  ┌─────────────────────┐  ┌──────────────────┐          │
│  │     QLineEdit       │  │   QToolButton ▾  │          │
│  │  • textEdited       │  │  • clicked       │          │
│  │  • eventFilter:     │  │     toggle popup │          │
│  │     ↓↑ Esc Enter    │  └──────────────────┘          │
│  └─────────────────────┘                                │
└─────────────────────────────────────────────────────────┘

弹出窗口（持久持有，show / hide）：
  _MultiSelectPopup (QFrame, Qt.Tool | Frameless)
   • WA_ShowWithoutActivating  ← 不激活窗口
   • 全部子控件 setFocusPolicy(Qt.NoFocus)
   ┌─────────────────────────────────────┐
   │  全选  反选  取消        已选 0 项  │   ← 按钮区
   ├─────────────────────────────────────┤
   │  ☐ Apple                            │   ← _CheckListWidget
   │  ☑ Banana                           │      (重写 mousePressEvent
   │  ☐ Cherry                           │       让点击任何位置都切换勾选)
   └─────────────────────────────────────┘

application 级事件过滤器（仅在 popup 显示期间装上）：
  _OutsideClickFilter (QObject)
   • 拦截全局 MouseButtonPress
   • 沿 obj.parentWidget() 链查找 popup / combo
   • 都不在 → 关闭 popup
```

### 11.2 关键流程

#### (1) 焦点与 IME（最关键的设计）

为了让 `QLineEdit` **持续持有焦点**（这样中文 / 日韩输入法能正常工作），同时弹窗里又能正常勾选：

| 措施 | 作用 |
|---|---|
| 弹窗 `Qt.Tool \| Qt.FramelessWindowHint` | top-level 但不上任务栏 |
| 弹窗 `WA_ShowWithoutActivating = True` | 显示弹窗时不激活窗口、不抢焦点 |
| 弹窗 + 所有子控件 `setFocusPolicy(Qt.NoFocus)` | 点击弹窗任何位置都不会让任何子控件成为 `focusWidget()` |
| **不**在 `FocusOut` 关闭 popup | 失焦时 `focusWidget()` 会是 `None`，按"失焦关闭"会一点即关 |

#### (2) 输入即过滤

```
用户在 QLineEdit 中按下任意字符
   │
   ▼
QLineEdit.textEdited(text)
   │
   ▼
MyCombo._on_text_edited(text)
   │
   ├─► self._editing = True       ← 进入"搜索模式"
   ├─► show_popup() (若未打开)
   └─► popup.apply_filter(text)   ← 根据子串隐藏不匹配项
```

退出搜索模式：`hide_popup()` 内会把 `self._editing` 设回 `False`，并把已选项重新写回 `QLineEdit`。

#### (3) 点击外部关闭

```
QApplication 收到 MouseButtonPress
   │
   ▼
_OutsideClickFilter.eventFilter(obj, event)
   │ 不查坐标，只看 obj 的 parentWidget() 链
   │
   ▼
MyCombo._on_outside_click(obj)
   │ 沿 obj.parentWidget() 向上走
   │   碰到 self._popup → 在弹窗内 → 不关
   │   碰到 self        → 在主控件内 → 不关
   │   走到 None        → 真外部 → hide_popup()
```

为什么不查坐标？因为 `Qt.Tool` 顶层窗口在多显示器 / 高 DPI / 不同窗口管理器下，`geometry().contains(globalPos)` 偶尔会把弹窗内边缘误判为外部。

#### (4) 显示模式 vs 编辑模式

```
                    ┌─ self._editing = False ─┐
   QLineEdit 显示    │                          │
   "Apple, Banana"  │                          │  ← 默认渲染
                    │                          │
                  user types                   │
                    │                          │
                    ▼                          │
   self._editing = True                        │
   QLineEdit 显示用户输入的内容                │
   弹窗按内容过滤                              │
                    │                          │
                    └────── hide_popup ────────┘
```

`_render_selection_to_edit()` 在 `self._editing = True` 时是 no-op，确保用户正在打字时不会被覆盖。

#### (5) 全选 / 反选 / 取消的"作用于可见项"语义

`apply_filter(text)` 通过 `QListWidgetItem.setHidden(True/False)` 隐藏不匹配项。

`_select_all_visible / _invert_visible / _clear_visible` 三个方法都遍历 list widget，**只对 `not isHidden()` 的项生效**。所以"输入 Bj → 全选" = "全选所有名字含 Bj 的项"。

---

## 12. 踩坑记录

### 12.1 多选下拉点一次勾选就关闭面板（**最严重**）

**现象**：在多选下拉的弹窗里点任意一项，面板立即关闭——用户无法连续多选。

**根因**：两个问题叠加：

1. **主因**：`QLineEdit` 的 `FocusOut` 事件被监听，里面写：
   ```python
   if fw is None or (fw is not self._edit and not self._is_descendant_of_popup(fw)):
       self.hide_popup()
   ```
   当用户点弹窗内任意一项，弹窗内所有子控件都是 `Qt.NoFocus`（这是不抢 IME 焦点的必需手段），点击后 `QApplication.focusWidget()` 返回 `None`，于是 `fw is None` 命中 → 立刻关闭弹窗。
2. **次因**：原来的"点击外部关闭"用 `popup.geometry().contains(globalPos)` 判断"是否在弹窗内"，对 `Qt.Tool` 窗口在某些 DPI / 多屏环境下会把内边缘误判为外部。

**修复**：
- **彻底移除 focus-out 关闭逻辑**：弹窗关闭只由"点击外部"驱动
- `_OutsideClickFilter` 改用 **widget 父链** 判断而非坐标：

```python
def _on_outside_click(self, obj):
    w = obj
    while w is not None:
        if w is self._popup or w is self:
            return        # 点在弹窗或主控件内
        w = w.parentWidget()
    self.hide_popup()
```

不依赖坐标系、不受 DPI / 窗口标志影响，事件目标是谁就以它的 parent chain 为准。

### 12.2 弹窗"取消"按钮语义歧义

**现象**：原来"取消"按钮做了两件事——清除可见勾选 **并** 关闭面板。用户反馈语义不清。

**修复**：拆为三个按钮，各司其职：

| 按钮 | 仅做 |
|---|---|
| **全选** | 勾选可见项 |
| **反选** | 反转可见项 |
| **取消** | 取消可见项的勾选（不关闭） |

每个按钮单一职责，避免误操作。关闭弹窗由 Esc 键、点击外部、鼠标 hover-leave 触发。

### 12.3 `set_theme()` 触发 QLayout 警告

**现象**：调用 `set_theme({...})` 时控制台打 `QLayout: Attempting to add QLayout "" to _MultiSelectPopup "MultiSelectPopup", which already has a layout`。

**根因**：原来的 `_apply_style()` 方法**同时**做两件事——`setStyleSheet(...)` **和** `QVBoxLayout(self)` 构建 widget tree。第二次调用时（`set_theme`）会把 `QVBoxLayout` 又往同一个 popup 上塞一次。

**修复**：把这两步拆开：
- `_apply_style()` — **只**写 stylesheet
- `_build_widgets()` — **只**构建一次 widget tree，从 `__init__` 末尾调用一次

```python
def __init__(self, ...):
    ...
    self._build_widgets()      # 一次性构建布局 / 按钮 / 列表 / 搜索框
    self._apply_style()        # 写 stylesheet
    ...

def set_theme(self, theme):
    self._theme = {**DEFAULT_THEME, **(theme or {})}
    self._apply_style()        # 只刷 stylesheet, 不重建 widget tree
```

效果：`set_theme()` 0 warnings，`__init__` 0 warnings。

---

> 完。`MyTable` 相关的内容请看 [README.md](README.md)。
