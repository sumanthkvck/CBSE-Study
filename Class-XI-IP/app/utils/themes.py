"""
Theme definitions for IP Learn.
Each theme has a complete color palette used across all pages.
"""

THEMES = {
    "Dark": {
        "name": "Dark",
        "bg":        "#0F1117",
        "surface":   "#1A1D2E",
        "card":      "#242838",
        "border":    "#2E3350",
        "accent":    "#6C63FF",
        "accent2":   "#00D4AA",
        "warn":      "#FFB300",
        "danger":    "#FF4757",
        "success":   "#2ED573",
        "text":      "#E8EAED",
        "subtext":   "#8892B0",
        "code_bg":   "#0D1117",
        "sidebar_bg":"#1A1D2E",
    },
    "Light": {
        "name": "Light",
        "bg":        "#F8F9FA",
        "surface":   "#FFFFFF",
        "card":      "#F1F3F5",
        "border":    "#DEE2E6",
        "accent":    "#4C6EF5",
        "accent2":   "#0CA678",
        "warn":      "#E67700",
        "danger":    "#C92A2A",
        "success":   "#2F9E44",
        "text":      "#212529",
        "subtext":   "#6C757D",
        "code_bg":   "#F8F9FA",
        "sidebar_bg":"#FFFFFF",
    },
    "Elegant Pink": {
        "name": "Elegant Pink",
        "bg":        "#1A0A14",
        "surface":   "#2D1220",
        "card":      "#3D1A2C",
        "border":    "#5C2840",
        "accent":    "#E91E8C",
        "accent2":   "#FF6EB4",
        "warn":      "#FFB347",
        "danger":    "#FF4757",
        "success":   "#4CAF87",
        "text":      "#FAE0EC",
        "subtext":   "#C490A8",
        "code_bg":   "#150810",
        "sidebar_bg":"#2D1220",
    },
    "Elegant Blue": {
        "name": "Elegant Blue",
        "bg":        "#060D1A",
        "surface":   "#0D1B2E",
        "card":      "#132640",
        "border":    "#1E3A5F",
        "accent":    "#00A8FF",
        "accent2":   "#00D4FF",
        "warn":      "#FFB300",
        "danger":    "#FF4757",
        "success":   "#00E676",
        "text":      "#E0F0FF",
        "subtext":   "#7EB8D4",
        "code_bg":   "#040B14",
        "sidebar_bg":"#0D1B2E",
    },
}

DEFAULT_THEME = "Dark"


def get_theme(name: str) -> dict:
    return THEMES.get(name, THEMES[DEFAULT_THEME])


def theme_names() -> list:
    return list(THEMES.keys())
