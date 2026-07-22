"""
Central Configuration for AI Banking Customer Insights & Marketplace Platform
"""
import os

# ──────────────────────────────────────────────
# Application Metadata
# ──────────────────────────────────────────────
APP_NAME = "AI Banking Customer Insights"
APP_VERSION = "1.0.0"
APP_ICON = ":material/account_balance:"

# ──────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_DIR = os.path.join(BASE_DIR, "database")
DATABASE_PATH = os.path.join(DATABASE_DIR, "banking.db")
MODELS_DIR = os.path.join(BASE_DIR, "models")
DATASETS_DIR = os.path.join(BASE_DIR, "datasets")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# Ensure directories exist
for d in [DATABASE_DIR, MODELS_DIR, DATASETS_DIR, REPORTS_DIR, ASSETS_DIR]:
    os.makedirs(d, exist_ok=True)

# ──────────────────────────────────────────────
# JWT Configuration
# ──────────────────────────────────────────────
JWT_SECRET = "ai-banking-insights-secret-key-2024-production"
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24

# ──────────────────────────────────────────────
# Role Definitions
# ──────────────────────────────────────────────
ROLES = {
    "admin": "Admin",
    "bank_manager": "Manager",
    "data_analyst": "Analyst",
    "customer": "Customer",
    "vendor": "Vendor",
    "guest": "Guest",
}

# ──────────────────────────────────────────────
# Demo Login Credentials
# ──────────────────────────────────────────────
DEMO_USERS = [
    {"username": "admin",    "password": "admin123",    "full_name": "System Administrator", "role": "admin",        "email": "admin@aibanking.com"},
    {"username": "manager",  "password": "manager123",  "full_name": "Sarah Johnson",        "role": "bank_manager", "email": "sarah.johnson@aibanking.com"},
    {"username": "analyst",  "password": "analyst123",  "full_name": "David Wilson",         "role": "data_analyst", "email": "david.wilson@aibanking.com"},
    {"username": "customer", "password": "customer123", "full_name": "Ravi Kumar",           "role": "customer",     "email": "ravi.kumar@marketplace.com"},
    {"username": "vendor",   "password": "vendor123",   "full_name": "John Smith",           "role": "vendor",       "email": "john@techworld.com"},
]

# ──────────────────────────────────────────────
# Page Access Control (role → allowed pages)
# ──────────────────────────────────────────────
PAGE_ACCESS = {
    # ── Banking Pages ──
    "Dashboard":              ["admin", "bank_manager", "data_analyst"],
    "Data Upload":            ["admin", "data_analyst"],
    "Data Preprocessing":     ["admin", "data_analyst"],
    "Database Manager":       ["admin"],
    "Customer Management":    ["admin", "bank_manager"],
    "Transaction Analytics":  ["admin", "bank_manager", "data_analyst"],
    "Loan Analytics":         ["admin", "bank_manager"],
    "EDA":                    ["admin", "data_analyst"],
    "Customer Segmentation":  ["admin", "bank_manager", "data_analyst"],
    "Churn Prediction":       ["admin", "bank_manager"],
    "CLV Prediction":         ["admin", "bank_manager"],
    "Product Recommendation": ["admin", "bank_manager"],
    "Deposit Prediction":     ["admin", "bank_manager"],
    "AI Business Insights":   ["admin", "bank_manager"],
    "Reports":                ["admin", "bank_manager", "data_analyst"],
    "Admin":                  ["admin"],
    "Settings":               ["admin", "bank_manager", "data_analyst"],
    # ── Marketplace Pages ──
    "Vendor Management":      ["admin"],
    "Product Catalog":        ["admin", "vendor"],
    "Category Management":    ["admin"],
    "Shop":                   ["admin", "customer", "vendor", "guest"],
    "Cart & Checkout":        ["customer"],
    "Wishlist":               ["customer"],
    "My Orders":              ["customer"],
    "Order Management":       ["admin", "vendor"],
    "Inventory Management":   ["admin", "vendor"],
    "Shipping & Logistics":   ["admin", "vendor"],
    "Returns & Refunds":      ["admin", "vendor", "customer"],
    "Reviews & Ratings":      ["admin", "customer"],
    "Notifications":          ["admin", "bank_manager", "data_analyst", "customer", "vendor"],
    "Vendor Dashboard":       ["vendor"],
    "Sales Analytics":        ["admin"],
    "Commission Report":      ["admin", "vendor"],
    "Marketplace Reports":    ["admin"],
}

# ──────────────────────────────────────────────
# Model Paths
# ──────────────────────────────────────────────
MODEL_PATHS = {
    "segmentation":   os.path.join(MODELS_DIR, "segmentation.pkl"),
    "churn":          os.path.join(MODELS_DIR, "churn.pkl"),

    "clv":            os.path.join(MODELS_DIR, "clv.pkl"),

    "recommendation": os.path.join(MODELS_DIR, "recommendation.pkl"),

    "deposit":        os.path.join(MODELS_DIR, "deposit.pkl"),
}

# ──────────────────────────────────────────────
# Banking Theme Colors
# ──────────────────────────────────────────────
COLORS = {
    "primary":       "#1B2A4A",   # Dark Navy
    "secondary":     "#2E86AB",   # Steel Blue
    "accent":        "#D4AF37",   # Gold
    "success":       "#28A745",   # Green
    "warning":       "#FFC107",   # Amber
    "danger":        "#DC3545",   # Red
    "info":          "#17A2B8",   # Teal
    "light":         "#F8F9FA",   # Light Gray
    "dark":          "#0D1B2A",   # Darkest Navy
    "card_bg":       "#FFFFFF",
    "sidebar_bg":    "#1B2A4A",
    "text_primary":  "#1B2A4A",
    "text_secondary":"#6C757D",
    "gradient_start":"#1B2A4A",
    "gradient_end":  "#2E86AB",
}

# Chart color sequence for Plotly
CHART_COLORS = [
    "#2E86AB", "#1B2A4A", "#D4AF37", "#5B6B8A", "#4B9CBE",
    "#6CA6C1", "#8EBAD0", "#C1D5E0", "#A4B8C4",
]

# ──────────────────────────────────────────────
# Data Configuration
# ──────────────────────────────────────────────
REGIONS = ["North", "South", "East", "West", "Central"]
BRANCHES = [
    "Main Branch", "Downtown", "Airport Road", "Tech Park", "Mall Road",
    "Station Area", "University", "Industrial Area", "Suburb", "Highway"
]
OCCUPATIONS = [
    "Salaried", "Self-Employed", "Business Owner", "Professional",
    "Government", "Student", "Retired", "Freelancer"
]
ACCOUNT_TYPES = ["Savings", "Current", "Fixed Deposit", "Recurring Deposit"]
LOAN_TYPES = ["Home Loan", "Personal Loan", "Auto Loan", "Business Loan", "Education Loan"]
CARD_TYPES = ["Credit", "Debit", "Prepaid"]
TRANSACTION_TYPES = ["Deposit", "Withdrawal", "Transfer", "Payment", "Refund"]
TRANSACTION_CHANNELS = ["Branch", "ATM", "Online", "Mobile", "POS"]
PRODUCT_LIST = [
    "Savings Account", "Current Account", "Credit Card", "Home Loan",
    "Personal Loan", "Fixed Deposit", "Insurance", "Investment Plan"
]

# ──────────────────────────────────────────────
# Pagination
# ──────────────────────────────────────────────
DEFAULT_PAGE_SIZE = 20

# ──────────────────────────────────────────────
# Marketplace Configuration
# ──────────────────────────────────────────────
UPLOAD_DIR = os.path.join(BASE_DIR, "uploaded_files", "products")
os.makedirs(UPLOAD_DIR, exist_ok=True)

PRODUCT_CATEGORIES = [
    "Electronics", "Fashion", "Home & Decor", "Groceries", "Sports & Fitness",
    "Books & Stationery", "Health & Beauty", "Toys & Games", "Automotive",
    "Garden & Outdoors",
]

ORDER_STATUSES = [
    "Placed", "Confirmed", "Processing", "Shipped",
    "In Transit", "Delivered", "Cancelled", "Returned",
]

PAYMENT_METHODS = ["UPI", "Credit Card", "Debit Card", "Net Banking", "Wallet"]

SHIPMENT_STATUSES = [
    "Pending", "Packed", "Shipped", "In Transit", "Out for Delivery", "Delivered",
]

DEFAULT_COMMISSION_RATE = 10.0  # percentage

TAX_RATES = {
    "GST_5":  5.0,
    "GST_12": 12.0,
    "GST_18": 18.0,
    "GST_28": 28.0,
}

CURRENCIES = {
    "INR": {"name": "Indian Rupee",  "symbol": "\u20b9", "rate_to_usd": 0.012},
    "USD": {"name": "US Dollar",     "symbol": "$",      "rate_to_usd": 1.0},
    "EUR": {"name": "Euro",          "symbol": "\u20ac", "rate_to_usd": 1.08},
    "GBP": {"name": "British Pound", "symbol": "\u00a3", "rate_to_usd": 1.27},
}

DEFAULT_CURRENCY = "INR"

# FastAPI config (optional, disabled by default)
API_ENABLED = False
API_HOST = "127.0.0.1"
API_PORT = 8000
