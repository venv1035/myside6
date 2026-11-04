"""四个自绘控件：Badge / MyCombo / MyTable / DragBar。

四个控件统一支持 ``style=`` 外观字典，以及 ``style()`` / ``set_style()``
读写；MyCombo / MyTable 还支持 ``texts=`` 文案字典与 ``metrics=`` 尺寸
字典，以及对应的 ``texts()`` / ``set_texts()``、``metrics()`` /
``set_metrics()``。
"""
from .badge import Badge, BadgeDict, BadgeList
from .badge import DEFAULT_STYLE as BADGE_STYLE
from .drag_bar import DragBar, DragBarItem
from .my_combo import (
    DEFAULT_METRICS as COMBO_METRICS,
    DEFAULT_STYLE as COMBO_STYLE,
    DEFAULT_TEXTS as COMBO_TEXTS,
    GITHUB_STYLE,
    GOOGLE_STYLE,
    STYLES as COMBO_STYLES,
    TENCENT_STYLE,
    MyCombo,
)
from .my_table import (
    ACTION_STYLES,
    DEFAULT_METRICS as TABLE_METRICS,
    DEFAULT_STYLE as TABLE_STYLE,
    DEFAULT_TEXTS as TABLE_TEXTS,
    ActionDelegate,
    MyTable,
)

#: DragBar 的默认配置（字体 / 尺寸 / 图标字符 / 配色）。
DRAGBAR_STYLE: dict = DragBar.DEFAULT_STYLE

__all__ = [
    # ---- Badge ----
    "Badge",
    "BadgeList",
    "BadgeDict",
    "BADGE_STYLE",
    # ---- MyCombo ----
    "MyCombo",
    "COMBO_STYLE",
    "GOOGLE_STYLE",
    "TENCENT_STYLE",
    "GITHUB_STYLE",
    "COMBO_STYLES",
    "COMBO_TEXTS",
    "COMBO_METRICS",
    # ---- MyTable ----
    "MyTable",
    "ActionDelegate",
    "ACTION_STYLES",
    "TABLE_STYLE",
    "TABLE_TEXTS",
    "TABLE_METRICS",
    # ---- DragBar ----
    "DragBar",
    "DragBarItem",
    "DRAGBAR_STYLE",
]
