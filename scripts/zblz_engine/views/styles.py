"""
ZBLZ Engine - UI Styles and Themes
Dark theme styling for the application.

Modify these constants to customize the appearance.
"""

# Color Palette
COLORS = {
    "background": "#1a1a2e",
    "background_light": "#16213e",
    "surface": "#0f3460",
    "surface_hover": "#1a4a7a",
    "primary": "#e94560",
    "primary_hover": "#ff6b6b",
    "text": "#eaeaea",
    "text_secondary": "#a0a0a0",
    "border": "#2a2a4a",
    "success": "#4ade80",
    "warning": "#fbbf24",
    "error": "#ef4444",
}

# Main application stylesheet
DARK_THEME = f"""
QMainWindow {{
    background-color: {COLORS["background"]};
}}

QWidget {{
    background-color: {COLORS["background"]};
    color: {COLORS["text"]};
    font-family: "Segoe UI", "Ubuntu", "Noto Sans", sans-serif;
    font-size: 13px;
}}

QLabel {{
    color: {COLORS["text"]};
    padding: 2px;
}}

QLabel#title {{
    font-size: 24px;
    font-weight: bold;
    color: {COLORS["primary"]};
}}

QLabel#subtitle {{
    font-size: 12px;
    color: {COLORS["text_secondary"]};
}}

QLabel#section-header {{
    font-size: 14px;
    font-weight: bold;
    color: {COLORS["text"]};
    padding: 8px 0;
}}

QPushButton {{
    background-color: {COLORS["surface"]};
    color: {COLORS["text"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 6px;
    padding: 10px 20px;
    font-weight: bold;
    min-height: 20px;
}}

QPushButton:hover {{
    background-color: {COLORS["surface_hover"]};
    border-color: {COLORS["primary"]};
}}

QPushButton:pressed {{
    background-color: {COLORS["primary"]};
}}

QPushButton:disabled {{
    background-color: {COLORS["background_light"]};
    color: {COLORS["text_secondary"]};
}}

QPushButton#primary {{
    background-color: {COLORS["primary"]};
    border-color: {COLORS["primary"]};
}}

QPushButton#primary:hover {{
    background-color: {COLORS["primary_hover"]};
}}

QLineEdit, QTextEdit {{
    background-color: {COLORS["background_light"]};
    color: {COLORS["text"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 6px;
    padding: 8px 12px;
    selection-background-color: {COLORS["primary"]};
}}

QLineEdit:focus, QTextEdit:focus {{
    border-color: {COLORS["primary"]};
}}

QLineEdit:read-only, QTextEdit:read-only {{
    background-color: {COLORS["background"]};
}}

QSlider::groove:horizontal {{
    border: 1px solid {COLORS["border"]};
    height: 8px;
    background: {COLORS["background_light"]};
    border-radius: 4px;
}}

QSlider::handle:horizontal {{
    background: {COLORS["primary"]};
    border: none;
    width: 20px;
    height: 20px;
    margin: -6px 0;
    border-radius: 10px;
}}

QSlider::handle:horizontal:hover {{
    background: {COLORS["primary_hover"]};
}}

QSlider::sub-page:horizontal {{
    background: {COLORS["primary"]};
    border-radius: 4px;
}}

QListWidget {{
    background-color: {COLORS["background_light"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 6px;
    padding: 4px;
}}

QListWidget::item {{
    padding: 8px;
    border-radius: 4px;
}}

QListWidget::item:selected {{
    background-color: {COLORS["surface"]};
}}

QListWidget::item:hover {{
    background-color: {COLORS["surface_hover"]};
}}

QGroupBox {{
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
    margin-top: 16px;
    padding-top: 16px;
    font-weight: bold;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    color: {COLORS["primary"]};
}}

QTabWidget::pane {{
    border: 1px solid {COLORS["border"]};
    border-radius: 6px;
    background-color: {COLORS["background"]};
}}

QTabBar::tab {{
    background-color: {COLORS["background_light"]};
    color: {COLORS["text_secondary"]};
    padding: 10px 20px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
}}

QTabBar::tab:selected {{
    background-color: {COLORS["surface"]};
    color: {COLORS["text"]};
}}

QTabBar::tab:hover:!selected {{
    background-color: {COLORS["surface_hover"]};
}}

QStatusBar {{
    background-color: {COLORS["background_light"]};
    color: {COLORS["text_secondary"]};
    border-top: 1px solid {COLORS["border"]};
}}

QScrollBar:vertical {{
    background-color: {COLORS["background"]};
    width: 12px;
    border-radius: 6px;
}}

QScrollBar::handle:vertical {{
    background-color: {COLORS["surface"]};
    border-radius: 6px;
    min-height: 20px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {COLORS["surface_hover"]};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QToolTip {{
    background-color: {COLORS["surface"]};
    color: {COLORS["text"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 4px;
    padding: 4px 8px;
}}

QCheckBox {{
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid {COLORS["border"]};
    background-color: {COLORS["background_light"]};
}}

QCheckBox::indicator:checked {{
    background-color: {COLORS["primary"]};
    border-color: {COLORS["primary"]};
}}

QCheckBox::indicator:hover {{
    border-color: {COLORS["primary"]};
}}
"""
