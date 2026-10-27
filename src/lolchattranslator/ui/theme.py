"""主题定义：深蓝黑电竞风配色 + 金色强调的 Qt 样式表。

设计理念：呼应游戏氛围的深色主题，金色作为品牌色点缀，
低饱和度的蓝灰作为层级背景，保证长时间使用不刺眼。
"""

# 配色常量
COLOR_BG = "#0a0f16"           # 主背景（更深）
COLOR_PANEL = "#111a26"        # 面板
COLOR_PANEL_ALT = "#16222e"    # 次级面板
COLOR_BORDER = "#24303f"       # 边框
COLOR_ACCENT = "#c9a24b"       # 金色强调（品牌色）
COLOR_ACCENT_HOVER = "#dbb65f"
COLOR_ACCENT_DIM = "#8a6d2f"   # 金色暗色
COLOR_TEXT = "#e8eef4"         # 主文本
COLOR_TEXT_MUTED = "#8494a5"   # 次要文本
COLOR_SUCCESS = "#3fb950"
COLOR_ERROR = "#f85149"
COLOR_WARNING = "#d29922"
COLOR_INFO = "#58a6ff"

FONT_FAMILY = "Segoe UI, Microsoft YaHei UI, PingFang SC, sans-serif"


def build_stylesheet() -> str:
    """生成全局 QSS。"""
    return f"""
    /* ============ 全局 ============ */
    * {{
        font-family: "{FONT_FAMILY}";
        font-size: 13px;
        color: {COLOR_TEXT};
        outline: none;
    }}

    QMainWindow, QWidget {{
        background-color: {COLOR_BG};
    }}

    /* ============ 侧边栏 ============ */
    QFrame#sidebar {{
        background-color: {COLOR_PANEL};
        border-right: 1px solid {COLOR_BORDER};
    }}
    QLabel#appTitle {{
        font-size: 17px;
        font-weight: 700;
        color: {COLOR_ACCENT};
        padding: 4px 2px 14px 2px;
    }}
    QLabel#sidebarHint {{
        color: {COLOR_TEXT_MUTED};
        font-size: 11px;
    }}

    /* 导航按钮 */
    QPushButton#navBtn {{
        background: transparent;
        border: none;
        border-radius: 8px;
        padding: 10px 14px;
        text-align: left;
        color: {COLOR_TEXT_MUTED};
        font-size: 13px;
    }}
    QPushButton#navBtn:hover {{
        background: {COLOR_PANEL_ALT};
        color: {COLOR_TEXT};
    }}
    QPushButton#navBtn:checked {{
        background: {COLOR_PANEL_ALT};
        color: {COLOR_ACCENT};
        font-weight: 600;
        border-left: 3px solid {COLOR_ACCENT};
    }}

    /* ============ 通用标签 ============ */
    QLabel#muted {{
        color: {COLOR_TEXT_MUTED};
    }}
    QLabel#sectionTitle {{
        color: {COLOR_ACCENT};
        font-size: 14px;
        font-weight: 600;
    }}

    /* ============ 按钮 ============ */
    QPushButton {{
        background-color: {COLOR_PANEL_ALT};
        border: 1px solid {COLOR_BORDER};
        border-radius: 6px;
        padding: 8px 16px;
        color: {COLOR_TEXT};
    }}
    QPushButton:hover {{
        background-color: #1d2a3a;
        border-color: {COLOR_ACCENT_DIM};
    }}
    QPushButton:pressed {{
        background-color: #16222e;
    }}
    QPushButton:disabled {{
        color: #556272;
        background-color: #131c27;
        border-color: #1d2732;
    }}

    QPushButton#primary {{
        background-color: {COLOR_ACCENT};
        border: none;
        color: #14100a;
        font-weight: 700;
        padding: 9px 20px;
    }}
    QPushButton#primary:hover {{
        background-color: {COLOR_ACCENT_HOVER};
    }}
    QPushButton#primary:pressed {{
        background-color: {COLOR_ACCENT_DIM};
    }}

    QPushButton#danger {{
        background-color: transparent;
        border: 1px solid #5a2a28;
        color: {COLOR_ERROR};
    }}
    QPushButton#danger:hover {{
        background-color: #2a1514;
        border-color: {COLOR_ERROR};
    }}

    /* ============ 输入控件 ============ */
    QLineEdit, QComboBox, QSpinBox {{
        background-color: {COLOR_PANEL};
        border: 1px solid {COLOR_BORDER};
        border-radius: 6px;
        padding: 7px 12px;
        color: {COLOR_TEXT};
        selection-background-color: {COLOR_ACCENT};
        selection-color: #14100a;
    }}
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{
        border-color: {COLOR_ACCENT};
    }}
    QLineEdit:disabled {{
        background-color: #0e1620;
        color: #556272;
    }}

    QTextEdit {{
        background-color: {COLOR_PANEL};
        border: 1px solid {COLOR_BORDER};
        border-radius: 8px;
        padding: 12px;
        color: {COLOR_TEXT};
        selection-background-color: {COLOR_ACCENT};
        selection-color: #14100a;
    }}
    QTextEdit:focus {{
        border-color: {COLOR_ACCENT_DIM};
    }}

    QComboBox::drop-down {{
        border: none;
        width: 26px;
    }}
    QComboBox::down-arrow {{
        image: none;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 5px solid {COLOR_TEXT_MUTED};
        margin-right: 8px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {COLOR_PANEL};
        border: 1px solid {COLOR_BORDER};
        selection-background-color: {COLOR_ACCENT};
        selection-color: #14100a;
        outline: none;
    }}

    /* ============ 滑块 ============ */
    QSlider::groove:horizontal {{
        height: 6px;
        background: {COLOR_BORDER};
        border-radius: 3px;
    }}
    QSlider::sub-page:horizontal {{
        background: {COLOR_ACCENT};
        border-radius: 3px;
    }}
    QSlider::handle:horizontal {{
        width: 18px;
        height: 18px;
        margin: -6px 0;
        background: {COLOR_ACCENT};
        border-radius: 9px;
        border: 2px solid #14100a;
    }}
    QSlider::handle:horizontal:hover {{
        background: {COLOR_ACCENT_HOVER};
    }}

    /* ============ Tab 页 ============ */
    QTabWidget::pane {{
        border: 1px solid {COLOR_BORDER};
        border-radius: 6px;
        top: -1px;
    }}
    QTabBar::tab {{
        background: transparent;
        color: {COLOR_TEXT_MUTED};
        padding: 9px 20px;
        border: none;
        border-bottom: 2px solid transparent;
    }}
    QTabBar::tab:hover {{
        color: {COLOR_TEXT};
    }}
    QTabBar::tab:selected {{
        color: {COLOR_ACCENT};
        border-bottom: 2px solid {COLOR_ACCENT};
        font-weight: 600;
    }}

    /* ============ 状态栏 ============ */
    QStatusBar {{
        background-color: {COLOR_PANEL};
        color: {COLOR_TEXT_MUTED};
        border-top: 1px solid {COLOR_BORDER};
    }}
    QStatusBar::item {{
        border: none;
    }}

    /* ============ 滚动条 ============ */
    QScrollBar:vertical {{
        background: transparent;
        width: 10px;
        margin: 2px;
    }}
    QScrollBar::handle:vertical {{
        background: {COLOR_BORDER};
        border-radius: 4px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {COLOR_ACCENT_DIM};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    QScrollBar:horizontal {{
        background: transparent;
        height: 10px;
        margin: 2px;
    }}
    QScrollBar::handle:horizontal {{
        background: {COLOR_BORDER};
        border-radius: 4px;
        min-width: 30px;
    }}

    /* ============ 提示 ============ */
    QToolTip {{
        background-color: {COLOR_PANEL_ALT};
        color: {COLOR_TEXT};
        border: 1px solid {COLOR_ACCENT_DIM};
        padding: 6px 10px;
        border-radius: 4px;
    }}
    """
