"""
Theme system for PsCafe Management System.

Provides OS-aware dark/light theme detection and automatic palette switching.
Semantic colors (green=available, red=overdue, etc.) remain consistent across themes.
"""

from dataclasses import dataclass
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt


@dataclass
class ThemeColors:
    """Theme-dependent colors that change between dark and light modes."""
    bg_page: str
    bg_surface: str
    bg_input: str
    text_primary: str
    text_secondary: str
    text_muted: str
    text_tertiary: str
    border_card: str
    bg_disabled_card: str
    bg_overdue_card: str
    bg_overdue_badge: str
    text_credits: str
    bg_hover_overlay: str


DARK_THEME = ThemeColors(
    bg_page="#1E272C",
    bg_surface="#263238",
    bg_input="#37474F",
    text_primary="#ECEFF1",
    text_secondary="#B0BEC5",
    text_muted="#78909C",
    text_tertiary="#90A4AE",
    border_card="#37474F",
    bg_disabled_card="#424242",
    bg_overdue_card="#3E2727",
    bg_overdue_badge="#5C2B2B",
    text_credits="#546E7A",
    bg_hover_overlay="#DDDDDD",
)

LIGHT_THEME = ThemeColors(
    bg_page="#F5F5F5",
    bg_surface="#FFFFFF",
    bg_input="#F0F0F0",
    text_primary="#212121",
    text_secondary="#616161",
    text_muted="#9E9E9E",
    text_tertiary="#757575",
    border_card="#E0E0E0",
    bg_disabled_card="#EEEEEE",
    bg_overdue_card="#FFEBEE",
    bg_overdue_badge="#FFCDD2",
    text_credits="#9E9E9E",
    bg_hover_overlay="#E0E0E0",
)


class SemanticColors:
    """Semantic colors that stay the same in both themes."""
    ACCENT_GREEN = "#4CAF50"
    ACCENT_GREEN_HOVER = "#43A047"
    ACCENT_BLUE = "#2196F3"
    ACCENT_BLUE_DARK = "#1976D2"
    ACCENT_BLUE_HOVER = "#1565C0"
    ACCENT_RED = "#F44336"
    ACCENT_RED_DARK = "#D32F2F"
    ACCENT_RED_HOVER = "#C62828"
    ACCENT_RED_END_HOVER = "#DA190B"
    ACCENT_ORANGE = "#FF9800"
    ACCENT_ORANGE_HOVER = "#F57C00"
    ACCENT_PURPLE = "#9C27B0"
    ACCENT_PURPLE_HOVER = "#7B1FA2"
    ACCENT_SLATE = "#607D8B"
    ACCENT_SLATE_HOVER = "#546E7A"
    ACCENT_GRAY = "#9E9E9E"
    ACCENT_GRAY_HOVER = "#757575"
    ACCENT_CANCEL = "#546E7A"
    ACCENT_CANCEL_HOVER = "#455A64"
    ACCENT_WARNING = "#FF5722"
    BG_BTN_DISABLED = "#CCCCCC"


def _build_palette(colors: ThemeColors) -> QPalette:
    """Build a QPalette from theme colors."""
    palette = QPalette()

    palette.setColor(QPalette.Window, QColor(colors.bg_page))
    palette.setColor(QPalette.WindowText, QColor(colors.text_primary))
    palette.setColor(QPalette.Base, QColor(colors.bg_surface))
    palette.setColor(QPalette.AlternateBase, QColor(colors.bg_input))
    palette.setColor(QPalette.Text, QColor(colors.text_primary))
    palette.setColor(QPalette.Button, QColor(colors.bg_input))
    palette.setColor(QPalette.ButtonText, QColor(colors.text_primary))
    palette.setColor(QPalette.Highlight, QColor(SemanticColors.ACCENT_BLUE_DARK))
    palette.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
    palette.setColor(QPalette.Mid, QColor(colors.border_card))
    palette.setColor(QPalette.Dark, QColor("#1A2327" if colors is DARK_THEME else "#BDBDBD"))
    palette.setColor(QPalette.PlaceholderText, QColor(colors.text_muted))
    palette.setColor(QPalette.ToolTipBase, QColor(colors.bg_surface))
    palette.setColor(QPalette.ToolTipText, QColor(colors.text_primary))
    palette.setColor(QPalette.Link, QColor(SemanticColors.ACCENT_BLUE_DARK))
    palette.setColor(QPalette.LinkVisited, QColor(SemanticColors.ACCENT_PURPLE))

    return palette


def apply_theme(app):
    """Apply Fusion style with theme-aware palette to the application.

    Also sets up automatic theme switching when the OS theme changes.
    Call this instead of app.setStyle("Fusion").
    """
    app.setStyle("Fusion")

    hints = app.styleHints()
    is_dark = hints.colorScheme() == Qt.ColorScheme.Dark
    colors = DARK_THEME if is_dark else LIGHT_THEME
    app.setPalette(_build_palette(colors))

    hints.colorSchemeChanged.connect(
        lambda scheme: _on_theme_changed(app, scheme)
    )


def _on_theme_changed(app, scheme):
    """Handle OS theme change."""
    is_dark = scheme == Qt.ColorScheme.Dark
    colors = DARK_THEME if is_dark else LIGHT_THEME
    app.setPalette(_build_palette(colors))


def get_theme_colors() -> ThemeColors:
    """Get the current theme colors based on OS theme."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        return DARK_THEME
    hints = app.styleHints()
    is_dark = hints.colorScheme() == Qt.ColorScheme.Dark
    return DARK_THEME if is_dark else LIGHT_THEME


def get_semantic() -> type:
    """Get semantic colors (same in both themes)."""
    return SemanticColors


def style(text_color=None, bg_color=None, border_color=None, extra=""):
    """Build a stylesheet color string from theme tokens.

    Args:
        text_color: ThemeColors field name (e.g. "text_muted") or hex color
        bg_color: ThemeColors field name or hex color
        border_color: ThemeColors field name or hex color
        extra: Additional CSS properties appended as-is

    Returns:
        A stylesheet string with resolved colors.
    """
    colors = get_theme_colors()
    parts = []

    if text_color is not None:
        val = getattr(colors, text_color, text_color)
        parts.append(f"color: {val};")
    if bg_color is not None:
        val = getattr(colors, bg_color, bg_color)
        parts.append(f"background-color: {val};")
    if border_color is not None:
        val = getattr(colors, border_color, border_color)
        parts.append(f"border: 1px solid {val};")
    if extra:
        parts.append(extra)

    return " ".join(parts)
