"""四个自绘控件：Badge / MyCombo / MyTable / DragBar。

每个控件都有一套默认配置（文案 / 尺寸 / 颜色），可以在构造时用关键字
或 ``texts`` / ``metrics`` / ``style`` 字典覆盖，默认外观保持不变。
"""
from .badge import Badge, BadgeDict, BadgeList
from .drag_bar import DragBar, DragBarItem
from .my_combo import (
    DEFAULT_METRICS as COMBO_METRICS,
)
from .my_combo import (
    DEFAULT_TEXTS as COMBO_TEXTS,
)
from .my_combo import (
    DEFAULT_THEME,
    GITHUB_THEME,
    GOOGLE_THEME,
    TENCENT_THEME,
    THEMES,
    MyCombo,
)
from .my_table import (
    DEFAULT_METRICS as TABLE_METRICS,
)
from .my_table import (
    DEFAULT_TEXTS as TABLE_TEXTS,
)
from .my_table import ACTION_STYLES, ActionDelegate, MyTable

#: DragBar 的默认配置（字体 / 尺寸 / 图标字符 / 配色）。
DRAGBAR_STYLE: dict = DragBar.DEFAULT_STYLE

__all__ = [
    # ---- Badge ----
    "Badge",
    "BadgeList",
    "BadgeDict",
    # ---- MyCombo ----
    "MyCombo",
    "DEFAULT_THEME",
    "GOOGLE_THEME",
    "TENCENT_THEME",
    "GITHUB_THEME",
    "THEMES",
    "COMBO_TEXTS",
    "COMBO_METRICS",
    # ---- MyTable ----
    "MyTable",
    "ActionDelegate",
    "ACTION_STYLES",
    "TABLE_TEXTS",
    "TABLE_METRICS",
    # ---- DragBar ----
    "DragBar",
    "DragBarItem",
    "DRAGBAR_STYLE",
]
from .badge import Badge, BadgeList, BadgeDict
from .drag_bar import DragBar, DragBarItem
from .my_table import MyTable, ActionDelegate, ACTION_STYLES
from .my_combo import (
    MyCombo,
    DEFAULT_THEME,
    GOOGLE_THEME,
    TENCENT_THEME,
    GITHUB_THEME,
    THEMES,
)

__all__ = [
    "Badge",
    "BadgeList",
    "BadgeDict",
    "DragBar",
    "DragBarItem",
    "MyTable",
    "ActionDelegate",
    "ACTION_STYLES",
    "MyCombo",
    "DEFAULT_THEME",
    "GOOGLE_THEME",
    "TENCENT_THEME",
    "GITHUB_THEME",
    "THEMES",
]
