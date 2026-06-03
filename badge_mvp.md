# Badge MVP 最小示例

## 文件

| 文件 | 说明 |
|------|------|
| `badge_mvp.py` | 单文件可运行脚本，展示 Badge 与 `list` 和 `int`/`callable` 的绑定 |

## 用法

```bash
# Badge 绑定 list（定时器自动轮询 ~300ms）
items = ["a", "b", "c"]
Badge(target=btn).bind(items)

# Badge 绑定 int（静态值，不自动更新）
Badge(target=btn).bind(len(items))

# Badge 绑定 callable（定时器自动轮询 ~300ms）
Badge(target=btn).bind(lambda: len(items))
```

## Badge.bind() 支持的数据源

| 类型 | 更新方式 | 说明 |
|------|----------|------|
| `list` / `dict` / `str` | 定时器轮询 | 容器长度的变化在 ~300ms 内反映到界面 |
| `int` | 静态 | 传入时显示一次，不自动更新 |
| `callable` | 定时器轮询 | 每 ~300ms 调用一次取返回值 |
| `QAbstractItemModel` | Qt 信号驱动 | 实时响应 `rowsInserted` / `rowsRemoved` / `modelReset` |
| 带 `changed` 信号的对象 | Qt 信号驱动 | 如 `BadgeList` / `BadgeDict`，实时响应 |

## MVP 脚本 (`badge_mvp.py`)

```python
"""Badge MVP — 最小可运行示例"""
import sys
from PySide6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget
from widgets import Badge

app = QApplication(sys.argv)
w = QWidget()
w.setWindowTitle("Badge MVP")

items = ["a", "b", "c"]

btn = QPushButton("点击添加")
btn_clr = QPushButton("清空")

v = QVBoxLayout(w)
v.addWidget(btn)
v.addWidget(btn_clr)
v.addStretch()

Badge(target=btn).bind(items)

btn.clicked.connect(lambda: items.append(f"x{len(items)}"))
btn_clr.clicked.connect(items.clear)

w.show()
sys.exit(app.exec())
```
