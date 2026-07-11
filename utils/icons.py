"""
Reusable Icon-Rendering Utility using Material Symbols Outlined
"""

# Map emojis and names to Material Symbol equivalents
SYMBOL_MAP = {
    # Sidebar & Navigation
    "🏠": "home",
    "📊": "dashboard",
    "📤": "upload_file",
    "🛠️": "build",
    "🗄️": "database",
    "👥": "group",
    "💳": "credit_card",
    "🏦": "account_balance",
    "📈": "analytics",
    "🎯": "track_changes",
    "🔮": "change_circle",
    "💎": "insights",
    "💡": "recommend",
    "💰": "savings",
    "🤖": "smart_toy",
    "📑": "description",
    "🔑": "admin_panel_settings",
    "⚙️": "settings",
    "🚪": "logout",
    "🔓": "login",
    "🔍": "search",
    "💵": "attach_money",
    "🛡️": "shield",
    "⏳": "schedule",
    "🏷️": "label",
    "📅": "calendar_today",
    "🧮": "calculate",
    "📥": "download",
    "⭐": "star",
    "✅": "check_circle",
    "❌": "cancel",
    "⚠️": "warning",
    "ℹ️": "info",
    "👤": "person",
    "⚙": "settings",
    "🔧": "build",
    "📊": "bar_chart",
    "❓": "help",
    "❌": "close",
    
    # Text-based friendly keys
    "home": "home",
    "dashboard": "dashboard",
    "upload": "upload_file",
    "preprocessing": "build",
    "database": "database",
    "customer": "group",
    "transaction": "credit_card",
    "loan": "account_balance",
    "eda": "analytics",
    "segmentation": "track_changes",
    "churn": "change_circle",
    "clv": "insights",
    "recommendation": "recommend",
    "ai": "smart_toy",
    "reports": "description",
    "admin": "admin_panel_settings",
    "settings": "settings",
    "logout": "logout",
    "login": "login",
    "search": "search",
    "money": "attach_money",
    "risk": "shield",
    "tenure": "schedule",
    "download": "download",
    "star": "star",
    "check": "check_circle",
    "cancel": "cancel",
    "warning": "warning",
    "info": "info",
    "user": "person",
}

def get_symbol_name(name: str) -> str:
    """
    Returns the clean Material Symbol name corresponding to the input emoji or text.
    """
    clean_name = str(name).strip()
    return SYMBOL_MAP.get(clean_name, SYMBOL_MAP.get(clean_name.lower(), clean_name))

def get_native_icon(name: str) -> str:
    """
    Returns the native Streamlit Material Symbol format (e.g., :material/icon_name:).
    """
    symbol = get_symbol_name(name)
    return f":material/{symbol}:"

def render_html_icon(name: str, size: str = "24px", color: str = None, classes: str = "") -> str:
    """
    Renders a Material Symbols Outlined icon as an HTML span string.
    """
    symbol = get_symbol_name(name)
    style = f"font-size: {size}; vertical-align: middle; line-height: 1;"
    if color:
        style += f" color: {color};"
    
    class_attr = f"class='material-symbols-outlined {classes}'" if classes else "class='material-symbols-outlined'"
    return f'<span {class_attr} style="{style}">{symbol}</span>'
