"""主题定义：深色电竞风视觉系统（v1.2.0 重制）。

设计目标
--------
- **层次**：用 3 层表面色（bg / surface / surface-2）+ 1 层描边区分卡片与背景，
  不再靠亮度堆叠，长时间看着不累。
- **品牌**：延续金色（Rift Gold）作为主行动色，蓝色作为信息色，绿色只表示“成功/运行中”。
- **触感**：所有可点击元素都有 hover / pressed / disabled 三态，主按钮用渐变，
  次级按钮用描边，危险操作只给红字。

调色板集中在文件顶部，改主题只需要动这里。
"""

# ---- 调色板 ----
COLOR_BG = "#080C13"
COLOR_BG_2 = "#0C121C"
COLOR_SURFACE = "#121A27"
COLOR_SURFACE_2 = "#182233"
COLOR_SURFACE_3 = "#1F2B3E"
COLOR_BORDER = "#233047"
COLOR_BORDER_STRONG = "#2F4059"

COLOR_TEXT = "#E9EFF7"
COLOR_TEXT_MUTED = "#93A3B8"
COLOR_TEXT_FAINT = "#64748B"

COLOR_ACCENT = "#C9A24B"
COLOR_ACCENT_HI = "#E7C572"
COLOR_ACCENT_DIM = "#7A5F26"

COLOR_SUCCESS = "#4ADE80"
COLOR_ERROR = "#F87171"
COLOR_WARNING = "#FBBF24"
COLOR_INFO = "#60A5FA"

FONT_FAMILY = "Microsoft YaHei UI"
FONT_MONO = "Cascadia Mono, Consolas, monospace"

RADIUS_CARD = 14
RADIUS_CTRL = 9


def build_stylesheet() -> str:
    """生成全局 QSS。"""
    return f"""
    /* ================= 全局 ================= */
    QWidget {{
        color: {COLOR_TEXT};
        font-family: "{FONT_FAMILY}";
        font-size: 13px;
    }}
    QMainWindow, QWidget#appRoot {{
        background-color: {COLOR_BG};
    }}
    QToolTip {{
        background-color: {COLOR_SURFACE_3};
        color: {COLOR_TEXT};
        border: 1px solid {COLOR_BORDER_STRONG};
        border-radius: 8px;
        padding: 7px 11px;
    }}

    /* ================= 侧边栏 ================= */
    QFrame#sidebar {{
        background-color: {COLOR_BG_2};
        border-right: 1px solid {COLOR_BORDER};
    }}
    QLabel#brandName {{
        color: {COLOR_TEXT};
        font-size: 16px;
        font-weight: 700;
    }}
    QLabel#brandSub {{
        color: {COLOR_TEXT_FAINT};
        font-size: 10px;
        letter-spacing: 0.5px;
    }}
    QLabel#navSection {{
        color: {COLOR_TEXT_FAINT};
        font-size: 10px;
        font-weight: 600;
        padding: 6px 10px 2px 10px;
        letter-spacing: 1px;
    }}
    QPushButton#navBtn {{
        background: transparent;
        border: 1px solid transparent;
        border-radius: {RADIUS_CTRL}px;
        padding: 10px 12px;
        text-align: left;
        color: {COLOR_TEXT_MUTED};
        font-size: 13px;
    }}
    QPushButton#navBtn:hover {{
        background-color: {COLOR_SURFACE};
        color: {COLOR_TEXT};
    }}
    QPushButton#navBtn:checked {{
        background-color: {COLOR_SURFACE_2};
        border: 1px solid {COLOR_BORDER_STRONG};
        color: {COLOR_ACCENT_HI};
        font-weight: 600;
    }}
    QLabel#navKey {{
        color: {COLOR_TEXT_FAINT};
        font-size: 10px;
        font-family: "{FONT_MONO}";
    }}

    /* 侧边栏底部信息卡 */
    QFrame#sideCard {{
        background-color: {COLOR_SURFACE};
        border: 1px solid {COLOR_BORDER};
        border-radius: 12px;
    }}
    QLabel#sideCardTitle {{
        color: {COLOR_TEXT_FAINT};
        font-size: 10px;
        font-weight: 600;
        letter-spacing: 1px;
    }}
    QLabel#sideCardKey {{
        color: {COLOR_TEXT_MUTED};
        font-size: 11px;
    }}
    QLabel#sideCardValue {{
        color: {COLOR_TEXT};
        font-size: 11px;
        font-family: "{FONT_MONO}";
    }}

    /* ================= 顶栏 ================= */
    QFrame#topBar {{
        background: transparent;
        border: none;
        border-bottom: 1px solid {COLOR_BORDER};
    }}
    QLabel#pageTitle {{
        color: {COLOR_TEXT};
        font-size: 19px;
        font-weight: 700;
    }}
    QLabel#pageSubtitle {{
        color: {COLOR_TEXT_FAINT};
        font-size: 11px;
    }}

    /* ================= 卡片 ================= */
    QFrame#card {{
        background-color: {COLOR_SURFACE};
        border: 1px solid {COLOR_BORDER};
        border-radius: {RADIUS_CARD}px;
    }}
    QFrame#cardAccent {{
        background-color: {COLOR_SURFACE};
        border: 1px solid {COLOR_BORDER_STRONG};
        border-radius: {RADIUS_CARD}px;
    }}
    QLabel#cardTitle {{
        color: {COLOR_TEXT};
        font-size: 13px;
        font-weight: 600;
    }}
    QLabel#cardHint {{
        color: {COLOR_TEXT_FAINT};
        font-size: 11px;
    }}
    QLabel#muted {{
        color: {COLOR_TEXT_MUTED};
        font-size: 11px;
    }}
    QLabel#dotGold {{
        color: {COLOR_ACCENT};
        font-size: 15px;
    }}
    QLabel#dotGreen {{
        color: {COLOR_SUCCESS};
        font-size: 15px;
    }}
    QFrame#divider {{
        background-color: {COLOR_BORDER};
        border: none;
        max-height: 1px;
        min-height: 1px;
    }}

    /* ================= 状态胶囊 ================= */
    QLabel#chip {{
        background-color: {COLOR_SURFACE_2};
        border: 1px solid {COLOR_BORDER};
        border-radius: 10px;
        padding: 4px 10px;
        color: {COLOR_TEXT_MUTED};
        font-size: 11px;
    }}
    QLabel#chipOk {{
        background-color: rgba(74, 222, 128, 28);
        border: 1px solid rgba(74, 222, 128, 90);
        border-radius: 10px;
        padding: 4px 10px;
        color: {COLOR_SUCCESS};
        font-size: 11px;
    }}
    QLabel#chipGold {{
        background-color: rgba(201, 162, 75, 30);
        border: 1px solid rgba(201, 162, 75, 95);
        border-radius: 10px;
        padding: 4px 10px;
        color: {COLOR_ACCENT_HI};
        font-size: 11px;
    }}
    QLabel#chipWarn {{
        background-color: rgba(251, 191, 36, 26);
        border: 1px solid rgba(251, 191, 36, 85);
        border-radius: 10px;
        padding: 4px 10px;
        color: {COLOR_WARNING};
        font-size: 11px;
    }}

    /* ================= 按钮 ================= */
    QPushButton {{
        background-color: {COLOR_SURFACE_2};
        border: 1px solid {COLOR_BORDER};
        border-radius: {RADIUS_CTRL}px;
        padding: 8px 15px;
        color: {COLOR_TEXT};
    }}
    QPushButton:hover {{
        background-color: {COLOR_SURFACE_3};
        border-color: {COLOR_BORDER_STRONG};
    }}
    QPushButton:pressed {{
        background-color: {COLOR_SURFACE};
    }}
    QPushButton:disabled {{
        color: {COLOR_TEXT_FAINT};
        background-color: {COLOR_BG_2};
        border-color: {COLOR_BORDER};
    }}

    QPushButton#primaryBtn {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLOR_ACCENT}, stop:1 {COLOR_ACCENT_HI});
        border: none;
        border-radius: {RADIUS_CTRL}px;
        color: #17120A;
        font-weight: 700;
        padding: 10px 20px;
    }}
    QPushButton#primaryBtn:hover {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLOR_ACCENT_HI}, stop:1 #F2D48C);
    }}
    QPushButton#primaryBtn:pressed {{
        background: {COLOR_ACCENT};
    }}
    QPushButton#primaryBtn:disabled {{
        background: {COLOR_SURFACE_3};
        color: {COLOR_TEXT_FAINT};
    }}

    QPushButton#ghostBtn {{
        background: transparent;
        border: 1px solid {COLOR_BORDER_STRONG};
        color: {COLOR_TEXT_MUTED};
        padding: 7px 13px;
    }}
    QPushButton#ghostBtn:hover {{
        border-color: {COLOR_ACCENT_DIM};
        color: {COLOR_TEXT};
        background-color: {COLOR_SURFACE_2};
    }}

    QPushButton#chipBtn {{
        background-color: {COLOR_SURFACE_2};
        border: 1px solid {COLOR_BORDER};
        border-radius: 12px;
        padding: 6px 12px;
        color: {COLOR_TEXT_MUTED};
        font-size: 12px;
    }}
    QPushButton#chipBtn:hover {{
        border-color: {COLOR_ACCENT_DIM};
        color: {COLOR_ACCENT_HI};
        background-color: {COLOR_SURFACE_3};
    }}

    QPushButton#dangerBtn {{
        background: transparent;
        border: 1px solid rgba(248, 113, 113, 90);
        color: {COLOR_ERROR};
    }}
    QPushButton#dangerBtn:hover {{
        background-color: rgba(248, 113, 113, 26);
        border-color: {COLOR_ERROR};
    }}

    /* ================= 输入控件 ================= */
    QLineEdit, QComboBox, QSpinBox {{
        background-color: {COLOR_BG_2};
        border: 1px solid {COLOR_BORDER};
        border-radius: {RADIUS_CTRL}px;
        padding: 8px 12px;
        color: {COLOR_TEXT};
        selection-background-color: {COLOR_ACCENT};
        selection-color: #17120A;
    }}
    QLineEdit:hover, QComboBox:hover, QSpinBox:hover {{
        border-color: {COLOR_BORDER_STRONG};
    }}
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{
        border-color: {COLOR_ACCENT};
        background-color: {COLOR_SURFACE};
    }}
    QLineEdit:disabled {{
        color: {COLOR_TEXT_FAINT};
        background-color: {COLOR_BG};
    }}

    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}
    QComboBox::down-arrow {{
        image: none;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 5px solid {COLOR_TEXT_MUTED};
        margin-right: 9px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {COLOR_SURFACE_2};
        border: 1px solid {COLOR_BORDER_STRONG};
        border-radius: 8px;
        padding: 4px;
        selection-background-color: {COLOR_ACCENT};
        selection-color: #17120A;
        outline: none;
    }}

    QTextEdit {{
        background-color: {COLOR_BG_2};
        border: 1px solid {COLOR_BORDER};
        border-radius: 10px;
        padding: 12px;
        color: {COLOR_TEXT};
        selection-background-color: {COLOR_ACCENT};
        selection-color: #17120A;
        font-size: 13px;
    }}
    QTextEdit:hover {{
        border-color: {COLOR_BORDER_STRONG};
    }}
    QTextEdit:focus {{
        border-color: {COLOR_ACCENT_DIM};
        background-color: {COLOR_BG};
    }}

    /* ================= 滑块 ================= */
    QSlider::groove:horizontal {{
        height: 4px;
        background: {COLOR_BORDER};
        border-radius: 2px;
    }}
    QSlider::sub-page:horizontal {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLOR_ACCENT_DIM}, stop:1 {COLOR_ACCENT});
        border-radius: 2px;
    }}
    QSlider::handle:horizontal {{
        width: 16px;
        height: 16px;
        margin: -7px 0;
        background: {COLOR_ACCENT_HI};
        border-radius: 8px;
        border: 2px solid #17120A;
    }}
    QSlider::handle:horizontal:hover {{
        background: #F5E0A8;
    }}

    /* ================= Tab ================= */
    QTabWidget::pane {{
        border: 1px solid {COLOR_BORDER};
        border-radius: {RADIUS_CARD}px;
        background-color: {COLOR_SURFACE};
        top: -1px;
    }}
    QTabBar::tab {{
        background: transparent;
        color: {COLOR_TEXT_MUTED};
        padding: 10px 22px;
        margin-right: 4px;
        border: none;
        border-bottom: 2px solid transparent;
    }}
    QTabBar::tab:hover {{
        color: {COLOR_TEXT};
    }}
    QTabBar::tab:selected {{
        color: {COLOR_ACCENT_HI};
        border-bottom: 2px solid {COLOR_ACCENT};
        font-weight: 600;
    }}

    /* ================= 复选 / 滚动条 / 状态栏 ================= */
    QCheckBox {{
        color: {COLOR_TEXT_MUTED};
        spacing: 9px;
    }}
    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
        border-radius: 5px;
        border: 1px solid {COLOR_BORDER_STRONG};
        background: {COLOR_BG_2};
    }}
    QCheckBox::indicator:hover {{
        border-color: {COLOR_ACCENT_DIM};
    }}
    QCheckBox::indicator:checked {{
        background: {COLOR_ACCENT};
        border-color: {COLOR_ACCENT};
    }}

    QScrollBar:vertical {{
        background: transparent;
        width: 9px;
        margin: 2px;
    }}
    QScrollBar::handle:vertical {{
        background: {COLOR_BORDER_STRONG};
        border-radius: 4px;
        min-height: 28px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {COLOR_ACCENT_DIM};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    QScrollBar:horizontal {{
        background: transparent;
        height: 9px;
        margin: 2px;
    }}
    QScrollBar::handle:horizontal {{
        background: {COLOR_BORDER_STRONG};
        border-radius: 4px;
        min-width: 28px;
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0;
    }}

    QStatusBar {{
        background-color: {COLOR_BG_2};
        color: {COLOR_TEXT_MUTED};
        border-top: 1px solid {COLOR_BORDER};
        padding-left: 12px;
    }}
    QStatusBar::item {{
        border: none;
    }}
    QSplitter::handle {{
        background-color: transparent;
        height: 10px;
    }}
    """
