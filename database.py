"""
Database Module — SQLite schema creation and synthetic data seeding.
Generates realistic banking data for all platform features.
"""
import sqlite3
import os
import datetime
import random
import numpy as np
import pandas as pd
import bcrypt
from config import (
    DATABASE_PATH, DATABASE_DIR, DEMO_USERS, REGIONS, BRANCHES,
    OCCUPATIONS, ACCOUNT_TYPES, LOAN_TYPES, CARD_TYPES,
    TRANSACTION_TYPES, TRANSACTION_CHANNELS, PRODUCT_CATEGORIES,
    ORDER_STATUSES, PAYMENT_METHODS, SHIPMENT_STATUSES,
    DEFAULT_COMMISSION_RATE
)

# ──────────────────────────────────────────────
# Connection Management
# ──────────────────────────────────────────────

def get_connection():
    """Get a SQLite connection with row factory enabled."""
    os.makedirs(DATABASE_DIR, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


# ──────────────────────────────────────────────
# Schema Creation
# ──────────────────────────────────────────────

def init_db():
    """Create all database tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # Users table (for authentication)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT,
            role TEXT NOT NULL DEFAULT 'data_analyst',
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now')),
            last_login TEXT
        )
    """)

    # Customers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            gender TEXT,
            age INTEGER,
            occupation TEXT,
            income REAL,
            region TEXT,
            branch TEXT,
            balance REAL DEFAULT 0,
            credit_score INTEGER,
            customer_since TEXT,
            email TEXT,
            phone TEXT,
            is_active INTEGER DEFAULT 1,
            risk_level TEXT DEFAULT 'Low',
            churn_score REAL DEFAULT 0,
            clv_score REAL DEFAULT 0,
            segment TEXT DEFAULT 'Regular'
        )
    """)

    # Accounts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            account_number TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL,
            account_type TEXT NOT NULL,
            balance REAL DEFAULT 0,
            status TEXT DEFAULT 'Active',
            opened_date TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        )
    """)

    # Transactions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL,
            account_number TEXT,
            amount REAL NOT NULL,
            date TEXT NOT NULL,
            type TEXT NOT NULL,
            channel TEXT,
            merchant TEXT,
            description TEXT,
            is_fraud INTEGER DEFAULT 0,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        )
    """)

    # Loans table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS loans (
            loan_id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL,
            loan_type TEXT NOT NULL,
            loan_amount REAL NOT NULL,
            interest_rate REAL,
            tenure_months INTEGER,
            emi REAL,
            status TEXT DEFAULT 'Active',
            applied_date TEXT,
            approved_date TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        )
    """)

    # Cards table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cards (
            card_number TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL,
            card_type TEXT NOT NULL,
            card_limit REAL DEFAULT 0,
            outstanding_amount REAL DEFAULT 0,
            status TEXT DEFAULT 'Active',
            issued_date TEXT,
            expiry_date TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        )
    """)

    # Audit logs table
    # NOTE: user_id intentionally has NO foreign key to users.id so that
    # audit records survive user deletion/deactivation.  This is deliberate.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            action TEXT NOT NULL,
            details TEXT,
            ip_address TEXT,
            timestamp TEXT DEFAULT (datetime('now'))
        )
    """)

    # ──────────────────────────────────────────────
    # Marketplace Tables
    # ──────────────────────────────────────────────

    # Vendors table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vendors (
            vendor_id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            business_name TEXT NOT NULL,
            owner_name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            gst_number TEXT,
            address TEXT,
            city TEXT,
            state TEXT,
            commission_rate REAL DEFAULT 10.0,
            status TEXT DEFAULT 'Pending',
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Categories table (hierarchical)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            category_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            parent_id TEXT,
            description TEXT,
            icon TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (parent_id) REFERENCES categories(category_id)
        )
    """)

    # Products table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id TEXT PRIMARY KEY,
            vendor_id TEXT NOT NULL,
            category_id TEXT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            mrp REAL,
            discount_pct REAL DEFAULT 0,
            sku TEXT,
            image_url TEXT,
            status TEXT DEFAULT 'Active',
            rating_avg REAL DEFAULT 0,
            rating_count INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id),
            FOREIGN KEY (category_id) REFERENCES categories(category_id)
        )
    """)

    # Warehouses table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS warehouses (
            warehouse_id TEXT PRIMARY KEY,
            vendor_id TEXT NOT NULL,
            name TEXT NOT NULL,
            address TEXT,
            city TEXT,
            state TEXT,
            pincode TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id)
        )
    """)

    # Inventory table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT NOT NULL,
            warehouse_id TEXT NOT NULL,
            quantity INTEGER DEFAULT 0,
            reserved INTEGER DEFAULT 0,
            reorder_level INTEGER DEFAULT 10,
            last_restocked TEXT,
            FOREIGN KEY (product_id) REFERENCES products(product_id),
            FOREIGN KEY (warehouse_id) REFERENCES warehouses(warehouse_id)
        )
    """)

    # Orders table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL,
            total_amount REAL NOT NULL,
            tax_amount REAL DEFAULT 0,
            shipping_amount REAL DEFAULT 0,
            discount_amount REAL DEFAULT 0,
            net_amount REAL NOT NULL,
            status TEXT DEFAULT 'Placed',
            shipping_address TEXT,
            shipping_city TEXT,
            shipping_state TEXT,
            shipping_pincode TEXT,
            notes TEXT,
            placed_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        )
    """)

    # Order Items table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT NOT NULL,
            product_id TEXT NOT NULL,
            vendor_id TEXT NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            unit_price REAL NOT NULL,
            total_price REAL NOT NULL,
            status TEXT DEFAULT 'Placed',
            FOREIGN KEY (order_id) REFERENCES orders(order_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id),
            FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id)
        )
    """)

    # Cart table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT NOT NULL,
            product_id TEXT NOT NULL,
            quantity INTEGER DEFAULT 1,
            added_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        )
    """)

    # Wishlist table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wishlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT NOT NULL,
            product_id TEXT NOT NULL,
            added_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        )
    """)

    # Reviews table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            review_id TEXT PRIMARY KEY,
            product_id TEXT NOT NULL,
            customer_id TEXT NOT NULL,
            rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
            title TEXT,
            comment TEXT,
            is_approved INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (product_id) REFERENCES products(product_id),
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        )
    """)

    # Payments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            payment_id TEXT PRIMARY KEY,
            order_id TEXT NOT NULL,
            amount REAL NOT NULL,
            method TEXT NOT NULL,
            status TEXT DEFAULT 'Pending',
            transaction_ref TEXT,
            paid_at TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (order_id) REFERENCES orders(order_id)
        )
    """)

    # Shipments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS shipments (
            shipment_id TEXT PRIMARY KEY,
            order_id TEXT NOT NULL,
            carrier TEXT,
            tracking_number TEXT,
            status TEXT DEFAULT 'Pending',
            estimated_delivery TEXT,
            shipped_at TEXT,
            delivered_at TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (order_id) REFERENCES orders(order_id)
        )
    """)

    # Refunds table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS refunds (
            refund_id TEXT PRIMARY KEY,
            order_id TEXT NOT NULL,
            payment_id TEXT NOT NULL,
            amount REAL NOT NULL,
            reason TEXT,
            status TEXT DEFAULT 'Requested',
            approved_at TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (order_id) REFERENCES orders(order_id),
            FOREIGN KEY (payment_id) REFERENCES payments(payment_id)
        )
    """)

    # Notifications table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            message TEXT,
            type TEXT DEFAULT 'info',
            is_read INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Commission Ledger table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS commission_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_id TEXT NOT NULL,
            order_id TEXT NOT NULL,
            order_amount REAL NOT NULL,
            commission_rate REAL NOT NULL,
            commission_amount REAL NOT NULL,
            status TEXT DEFAULT 'Pending',
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id),
            FOREIGN KEY (order_id) REFERENCES orders(order_id)
        )
    """)

    # Tax Rates table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tax_rates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            rate REAL NOT NULL,
            description TEXT,
            is_active INTEGER DEFAULT 1
        )
    """)

    # Currencies table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS currencies (
            code TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            symbol TEXT NOT NULL,
            rate_to_usd REAL DEFAULT 1.0,
            is_active INTEGER DEFAULT 1
        )
    """)

    # Create indexes for performance
    index_queries = [
        "CREATE INDEX IF NOT EXISTS idx_customers_region ON customers(region)",
        "CREATE INDEX IF NOT EXISTS idx_customers_branch ON customers(branch)",
        "CREATE INDEX IF NOT EXISTS idx_customers_occupation ON customers(occupation)",
        "CREATE INDEX IF NOT EXISTS idx_accounts_customer ON accounts(customer_id)",
        "CREATE INDEX IF NOT EXISTS idx_transactions_customer ON transactions(customer_id)",
        "CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date)",
        "CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(type)",
        "CREATE INDEX IF NOT EXISTS idx_loans_customer ON loans(customer_id)",
        "CREATE INDEX IF NOT EXISTS idx_loans_status ON loans(status)",
        "CREATE INDEX IF NOT EXISTS idx_cards_customer ON cards(customer_id)",
        "CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp)",
        # Marketplace indexes
        "CREATE INDEX IF NOT EXISTS idx_vendors_status ON vendors(status)",
        "CREATE INDEX IF NOT EXISTS idx_products_vendor ON products(vendor_id)",
        "CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id)",
        "CREATE INDEX IF NOT EXISTS idx_products_status ON products(status)",
        "CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id)",
        "CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)",
        "CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id)",
        "CREATE INDEX IF NOT EXISTS idx_cart_customer ON cart(customer_id)",
        "CREATE INDEX IF NOT EXISTS idx_wishlist_customer ON wishlist(customer_id)",
        "CREATE INDEX IF NOT EXISTS idx_reviews_product ON reviews(product_id)",
        "CREATE INDEX IF NOT EXISTS idx_payments_order ON payments(order_id)",
        "CREATE INDEX IF NOT EXISTS idx_shipments_order ON shipments(order_id)",
        "CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_commission_vendor ON commission_ledger(vendor_id)",
        "CREATE INDEX IF NOT EXISTS idx_inventory_product ON inventory(product_id)",
    ]
    for q in index_queries:
        cursor.execute(q)

    conn.commit()
    conn.close()


# ──────────────────────────────────────────────
# Synthetic Data Generation
# ──────────────────────────────────────────────

def _generate_name(gender):
    """Generate a realistic full name based on gender."""
    male_first = ["James", "Robert", "Michael", "William", "David", "Richard", "Joseph",
                  "Thomas", "Charles", "Daniel", "Matthew", "Anthony", "Mark", "Steven",
                  "Andrew", "Paul", "Joshua", "Kenneth", "Kevin", "Brian", "George",
                  "Timothy", "Ronald", "Edward", "Jason", "Jeffrey", "Ryan", "Jacob",
                  "Gary", "Nicholas", "Eric", "Jonathan", "Stephen", "Larry", "Justin",
                  "Scott", "Brandon", "Benjamin", "Samuel", "Raymond"]
    female_first = ["Mary", "Patricia", "Jennifer", "Linda", "Barbara", "Elizabeth",
                    "Susan", "Jessica", "Sarah", "Karen", "Lisa", "Nancy", "Betty",
                    "Margaret", "Sandra", "Ashley", "Dorothy", "Kimberly", "Emily",
                    "Donna", "Michelle", "Carol", "Amanda", "Melissa", "Deborah",
                    "Stephanie", "Rebecca", "Sharon", "Laura", "Cynthia", "Kathleen",
                    "Amy", "Angela", "Shirley", "Anna", "Brenda", "Pamela", "Emma",
                    "Nicole", "Helen"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
                  "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
                  "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
                  "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark",
                  "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King",
                  "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores"]

    first = random.choice(male_first if gender == "Male" else female_first)
    last = random.choice(last_names)
    return f"{first} {last}"


def _generate_merchant():
    """Generate a random merchant name."""
    merchants = [
        "Amazon", "Walmart", "Target", "Costco", "Best Buy", "Starbucks",
        "McDonald's", "Shell Gas", "Netflix", "Uber", "Apple Store",
        "Home Depot", "Whole Foods", "Zara", "Nike", "Spotify",
        "Grocery Mart", "Electric Co", "Water Utility", "Insurance Corp",
        "PhonePay", "Local Restaurant", "Gas Station", "Pharmacy Plus",
        "BookStore", "Gym Membership", "Car Service", "Airlines Inc"
    ]
    return random.choice(merchants)


def seed_demo_data(n_customers=5000):
    """
    Generate and insert realistic synthetic banking data.

    Args:
        n_customers: Number of customers to generate (default 5000)
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Check if users already exist (indicates database has been initialized/seeded)
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return  # Data already seeded or initialized

    random.seed(42)
    np.random.seed(42)

    # ── 1. Seed Demo Users ──
    for user in DEMO_USERS:
        pw_hash = bcrypt.hashpw(user["password"].encode(), bcrypt.gensalt()).decode()
        try:
            cursor.execute("""
                INSERT INTO users (username, password_hash, full_name, email, role)
                VALUES (?, ?, ?, ?, ?)
            """, (user["username"], pw_hash, user["full_name"], user["email"], user["role"]))
        except sqlite3.IntegrityError:
            pass  # User already exists

    # ── 2. Generate Customers ──
    customers = []
    base_date = datetime.date(2018, 1, 1)
    for i in range(1, n_customers + 1):
        cid = f"CUST{i:05d}"
        gender = random.choice(["Male", "Female"])
        name = _generate_name(gender)
        age = int(np.random.normal(42, 12))
        age = max(18, min(75, age))
        occupation = random.choice(OCCUPATIONS)

        # Income correlated with occupation and age
        base_income = {
            "Salaried": 55000, "Self-Employed": 65000, "Business Owner": 90000,
            "Professional": 80000, "Government": 50000, "Student": 15000,
            "Retired": 35000, "Freelancer": 45000
        }
        income = max(10000, int(np.random.normal(base_income[occupation], base_income[occupation] * 0.3)))
        income = round(income, -2)  # Round to nearest 100

        region = random.choice(REGIONS)
        branch = random.choice(BRANCHES)
        balance = max(0, round(np.random.lognormal(mean=10, sigma=1.2), 2))
        balance = min(balance, 500000)
        credit_score = int(np.clip(np.random.normal(680, 80), 300, 850))
        days_since = random.randint(0, 2200)
        customer_since = (base_date + datetime.timedelta(days=days_since)).isoformat()
        email = f"{name.lower().replace(' ', '.')}_{i}@email.com"
        phone = f"+1-{random.randint(200,999)}-{random.randint(100,999)}-{random.randint(1000,9999)}"
        is_active = 1 if random.random() > 0.08 else 0

        # Risk level based on credit score
        if credit_score >= 750:
            risk_level = "Low"
        elif credit_score >= 650:
            risk_level = "Medium"
        else:
            risk_level = "High"

        customers.append((
            cid, name, gender, age, occupation, income, region, branch,
            balance, credit_score, customer_since, email, phone, is_active,
            risk_level, 0, 0, "Regular"
        ))

    cursor.executemany("""
        INSERT INTO customers (customer_id, name, gender, age, occupation, income,
            region, branch, balance, credit_score, customer_since, email, phone,
            is_active, risk_level, churn_score, clv_score, segment)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, customers)

    # ── 3. Generate Accounts ──
    accounts = []
    acct_counter = 1
    for i in range(1, n_customers + 1):
        cid = f"CUST{i:05d}"
        n_accounts = random.choices([1, 2, 3], weights=[50, 35, 15])[0]
        for _ in range(n_accounts):
            acct_num = f"ACC{acct_counter:07d}"
            acct_type = random.choice(ACCOUNT_TYPES)
            acct_balance = max(0, round(np.random.lognormal(mean=9, sigma=1.5), 2))
            acct_balance = min(acct_balance, 300000)
            status = random.choices(["Active", "Inactive", "Closed"], weights=[80, 12, 8])[0]
            opened = (base_date + datetime.timedelta(days=random.randint(0, 2200))).isoformat()
            accounts.append((acct_num, cid, acct_type, acct_balance, status, opened))
            acct_counter += 1

    cursor.executemany("""
        INSERT INTO accounts (account_number, customer_id, account_type, balance, status, opened_date)
        VALUES (?, ?, ?, ?, ?, ?)
    """, accounts)

    # ── 4. Generate Transactions ──
    transactions = []
    txn_counter = 1
    start_date = datetime.date(2024, 1, 1)
    end_date = datetime.date(2025, 6, 30)
    date_range = (end_date - start_date).days

    # Select a subset of customers to have transactions (most of them)
    active_customer_ids = [f"CUST{i:05d}" for i in range(1, n_customers + 1)]
    n_transactions = min(50000, n_customers * 10)

    for _ in range(n_transactions):
        txn_id = f"TXN{txn_counter:07d}"
        cid = random.choice(active_customer_ids)
        txn_type = random.choices(
            TRANSACTION_TYPES,
            weights=[30, 25, 20, 20, 5]
        )[0]

        # Amount varies by type
        if txn_type == "Deposit":
            amount = round(abs(np.random.lognormal(mean=7.5, sigma=1.0)), 2)
        elif txn_type == "Withdrawal":
            amount = round(abs(np.random.lognormal(mean=6.5, sigma=1.2)), 2)
        elif txn_type == "Transfer":
            amount = round(abs(np.random.lognormal(mean=7.0, sigma=1.3)), 2)
        elif txn_type == "Payment":
            amount = round(abs(np.random.lognormal(mean=5.5, sigma=1.0)), 2)
        else:  # Refund
            amount = round(abs(np.random.lognormal(mean=5.0, sigma=0.8)), 2)

        amount = min(amount, 50000)
        txn_date = (start_date + datetime.timedelta(days=random.randint(0, date_range))).isoformat()
        channel = random.choices(
            TRANSACTION_CHANNELS,
            weights=[15, 20, 30, 25, 10]
        )[0]
        merchant = _generate_merchant() if txn_type in ["Payment", "Withdrawal"] else ""

        # Small percentage flagged as fraud
        is_fraud = 1 if (amount > 10000 and random.random() < 0.03) else 0

        transactions.append((
            txn_id, cid, "", amount, txn_date, txn_type,
            channel, merchant, "", is_fraud
        ))
        txn_counter += 1

    cursor.executemany("""
        INSERT INTO transactions (transaction_id, customer_id, account_number, amount,
            date, type, channel, merchant, description, is_fraud)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, transactions)

    # ── 5. Generate Loans ──
    loans = []
    loan_counter = 1
    # About 60% of customers have at least one loan
    loan_customers = random.sample(active_customer_ids, k=int(n_customers * 0.6))

    for cid in loan_customers:
        n_loans = random.choices([1, 2], weights=[70, 30])[0]
        for _ in range(n_loans):
            loan_id = f"LOAN{loan_counter:06d}"
            loan_type = random.choice(LOAN_TYPES)

            # Loan amount varies by type
            loan_amounts = {
                "Home Loan": (200000, 80000),
                "Personal Loan": (20000, 10000),
                "Auto Loan": (30000, 12000),
                "Business Loan": (100000, 50000),
                "Education Loan": (40000, 15000),
            }
            mean_amt, std_amt = loan_amounts[loan_type]
            loan_amount = max(5000, round(np.random.normal(mean_amt, std_amt), -2))

            interest_rate = round(random.uniform(3.5, 15.5), 2)
            tenure = random.choice([12, 24, 36, 48, 60, 84, 120, 180, 240, 360])
            monthly_rate = interest_rate / 12 / 100
            if monthly_rate > 0:
                emi = round(loan_amount * monthly_rate * (1 + monthly_rate)**tenure / ((1 + monthly_rate)**tenure - 1), 2)
            else:
                emi = round(loan_amount / tenure, 2)

            status = random.choices(
                ["Active", "Closed", "Defaulted", "Pending"],
                weights=[50, 30, 10, 10]
            )[0]
            applied = (start_date + datetime.timedelta(days=random.randint(0, date_range))).isoformat()
            approved = (datetime.date.fromisoformat(applied) + datetime.timedelta(days=random.randint(1, 15))).isoformat() if status != "Pending" else None

            loans.append((loan_id, cid, loan_type, loan_amount, interest_rate,
                         tenure, emi, status, applied, approved))
            loan_counter += 1

    cursor.executemany("""
        INSERT INTO loans (loan_id, customer_id, loan_type, loan_amount, interest_rate,
            tenure_months, emi, status, applied_date, approved_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, loans)

    # ── 6. Generate Cards ──
    cards = []
    card_counter = 1
    # About 50% of customers have cards
    card_customers = random.sample(active_customer_ids, k=int(n_customers * 0.5))

    for cid in card_customers:
        n_cards = random.choices([1, 2], weights=[65, 35])[0]
        for _ in range(n_cards):
            card_num = f"CARD{card_counter:08d}"
            card_type = random.choice(CARD_TYPES)

            if card_type == "Credit":
                card_limit = round(random.choice([5000, 10000, 15000, 25000, 50000, 100000]), 2)
                outstanding = round(random.uniform(0, card_limit * 0.8), 2)
            elif card_type == "Debit":
                card_limit = 0
                outstanding = 0
            else:  # Prepaid
                card_limit = round(random.choice([500, 1000, 2000, 5000]), 2)
                outstanding = round(random.uniform(0, card_limit), 2)

            status = random.choices(["Active", "Blocked", "Expired"], weights=[80, 10, 10])[0]
            issued = (start_date + datetime.timedelta(days=random.randint(0, date_range))).isoformat()
            expiry = (datetime.date.fromisoformat(issued) + datetime.timedelta(days=365*3)).isoformat()

            cards.append((card_num, cid, card_type, card_limit, outstanding,
                         status, issued, expiry))
            card_counter += 1

    cursor.executemany("""
        INSERT INTO cards (card_number, customer_id, card_type, card_limit,
            outstanding_amount, status, issued_date, expiry_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, cards)

    # ── 7. Log initial audit entry ──
    cursor.execute("""
        INSERT INTO audit_logs (username, action, details)
        VALUES ('system', 'DATABASE_SEED', 'Initial synthetic data generated successfully')
    """)

    conn.commit()
    conn.close()

    # ── 8. Export sample dataset CSV ──
    _export_sample_csv()

    # ── 9. Seed Marketplace Data ──
    seed_marketplace_data()


def _export_sample_csv():
    """Export customer data as a CSV for the datasets folder."""
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM customers LIMIT 1000", conn)
    csv_path = os.path.join(os.path.dirname(DATABASE_PATH), "..", "datasets", "bank_customers.csv")
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    df.to_csv(csv_path, index=False)
    conn.close()


# ──────────────────────────────────────────────
# Marketplace Seed Data
# ──────────────────────────────────────────────

def seed_marketplace_data():
    """
    Insert seed data for the marketplace extension.
    Creates vendor user accounts, vendor records, categories, sample products,
    warehouses, inventory, tax rates, and currencies.
    Idempotent — skips if vendors already exist.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Skip if already seeded
    cursor.execute("SELECT COUNT(*) FROM vendors")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    now = datetime.datetime.now().isoformat(timespec="seconds")

    # ── 1. Create vendor user accounts ──
    vendor_users = [
        ("vendor_techworld",    "vendor123", "John Smith",    "john@techworld.com",         "vendor"),
        ("vendor_fashionhub",   "vendor123", "Priya Sharma",  "priya@fashionhub.com",       "vendor"),
        ("vendor_homestyle",    "vendor123", "Rahul Verma",   "rahul@homestyledecor.com",   "vendor"),
        ("vendor_freshgrocers", "vendor123", "Anitha Reddy",  "anitha@freshgrocers.com",    "vendor"),
        ("vendor_sportszone",   "vendor123", "Vikram Singh",  "vikram@sportszone.com",      "vendor"),
    ]

    vendor_user_ids = {}
    for username, password, full_name, email, role in vendor_users:
        pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        try:
            cursor.execute("""
                INSERT INTO users (username, password_hash, full_name, email, role, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (username, pw_hash, full_name, email, role, now))
            vendor_user_ids[username] = cursor.lastrowid
        except sqlite3.IntegrityError:
            # User already exists, fetch their id
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            vendor_user_ids[username] = cursor.fetchone()[0]

    # ── 2. Insert 5 vendors ──
    vendors_data = [
        ("VND00001", vendor_user_ids["vendor_techworld"],    "Tech World",       "John Smith",    "john@techworld.com",       "9876543210", "29ABCDE1234F1Z5", "12 MG Road",        "Bangalore",  "Karnataka",   10.0, "Active"),
        ("VND00002", vendor_user_ids["vendor_fashionhub"],   "Fashion Hub",      "Priya Sharma",  "priya@fashionhub.com",     "9123456780", "07FGHIJ5678K1Z2", "45 Connaught Place","New Delhi",  "Delhi",       12.0, "Active"),
        ("VND00003", vendor_user_ids["vendor_homestyle"],    "HomeStyle Decor",  "Rahul Verma",   "rahul@homestyledecor.com", "9988776655", "27KLMNO9012P1Z8", "78 Andheri West",   "Mumbai",     "Maharashtra",  8.0, "Pending"),
        ("VND00004", vendor_user_ids["vendor_freshgrocers"], "Fresh Grocers",    "Anitha Reddy",  "anitha@freshgrocers.com",  "9012345678", "36QRSTU3456V1Z4", "22 Jubilee Hills",  "Hyderabad",  "Telangana",    9.0, "Active"),
        ("VND00005", vendor_user_ids["vendor_sportszone"],   "SportsZone",       "Vikram Singh",  "vikram@sportszone.com",    "9345678901", "08WXYZA6789B1Z6", "33 Civil Lines",    "Jaipur",     "Rajasthan",   11.0, "Suspended"),
    ]

    cursor.executemany("""
        INSERT INTO vendors (vendor_id, user_id, business_name, owner_name, email, phone,
            gst_number, address, city, state, commission_rate, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
    """, vendors_data)

    # ── 3. Seed categories ──
    categories = [
        ("CAT001", "Electronics",        None,     "Electronic gadgets and devices",    "devices"),
        ("CAT002", "Fashion",            None,     "Clothing and accessories",          "checkroom"),
        ("CAT003", "Home & Decor",       None,     "Home furnishing and decor",         "chair"),
        ("CAT004", "Groceries",          None,     "Fresh food and daily essentials",   "grocery"),
        ("CAT005", "Sports & Fitness",   None,     "Sports equipment and accessories",  "fitness_center"),
        ("CAT006", "Books & Stationery", None,     "Books, stationery, and supplies",   "menu_book"),
        ("CAT007", "Health & Beauty",    None,     "Personal care and beauty products", "spa"),
        ("CAT008", "Toys & Games",       None,     "Toys, games, and entertainment",    "toys"),
        ("CAT009", "Automotive",         None,     "Vehicle parts and accessories",     "directions_car"),
        ("CAT010", "Garden & Outdoors",  None,     "Garden tools and outdoor gear",     "yard"),
        # Sub-categories
        ("CAT011", "Smartphones",        "CAT001", "Mobile phones and accessories",     "smartphone"),
        ("CAT012", "Laptops",            "CAT001", "Laptops and notebooks",             "laptop"),
        ("CAT013", "Men's Clothing",     "CAT002", "Men's fashion wear",                "person"),
        ("CAT014", "Women's Clothing",   "CAT002", "Women's fashion wear",              "person"),
        ("CAT015", "Furniture",          "CAT003", "Home and office furniture",          "weekend"),
    ]

    cursor.executemany("""
        INSERT INTO categories (category_id, name, parent_id, description, icon)
        VALUES (?, ?, ?, ?, ?)
    """, categories)

    # ── 4. Seed sample products ──
    products = [
        ("PRD00001", "VND00001", "CAT011", "Galaxy Pro Max 5G",      "Latest flagship smartphone with 200MP camera", 69999.00, 79999.00, 12.5, "SKU-TW-001", None, "Active"),
        ("PRD00002", "VND00001", "CAT012", "UltraBook Pro 15",       "15-inch ultralight laptop with M3 chip",      124999.00,149999.00, 16.7, "SKU-TW-002", None, "Active"),
        ("PRD00003", "VND00001", "CAT001", "Wireless Earbuds ANC",   "Active noise cancelling wireless earbuds",      4999.00,  6999.00, 28.6, "SKU-TW-003", None, "Active"),
        ("PRD00004", "VND00002", "CAT013", "Premium Cotton Shirt",   "100% cotton formal shirt, slim fit",            1899.00,  2999.00, 36.7, "SKU-FH-001", None, "Active"),
        ("PRD00005", "VND00002", "CAT014", "Designer Silk Saree",    "Handwoven Banarasi silk saree",                 8499.00, 12999.00, 34.6, "SKU-FH-002", None, "Active"),
        ("PRD00006", "VND00002", "CAT002", "Leather Wallet",         "Genuine leather bi-fold wallet",                 999.00,  1499.00, 33.4, "SKU-FH-003", None, "Active"),
        ("PRD00007", "VND00003", "CAT015", "Ergonomic Office Chair", "Adjustable lumbar support mesh chair",          12999.00, 18999.00, 31.6, "SKU-HS-001", None, "Active"),
        ("PRD00008", "VND00003", "CAT003", "Ceramic Dinner Set",     "24-piece premium ceramic dinner set",            3999.00,  5499.00, 27.3, "SKU-HS-002", None, "Active"),
        ("PRD00009", "VND00004", "CAT004", "Organic Honey 500g",     "Pure organic multiflower honey",                  499.00,   699.00, 28.6, "SKU-FG-001", None, "Active"),
        ("PRD00010", "VND00004", "CAT004", "Basmati Rice 5kg",       "Premium aged basmati rice",                       649.00,   799.00, 18.8, "SKU-FG-002", None, "Active"),
        ("PRD00011", "VND00005", "CAT005", "Professional Cricket Bat","English willow grade-1 bat",                    5999.00,  7999.00, 25.0, "SKU-SZ-001", None, "Active"),
        ("PRD00012", "VND00005", "CAT005", "Running Shoes Pro",      "Lightweight marathon running shoes",              3499.00,  4999.00, 30.0, "SKU-SZ-002", None, "Active"),
    ]

    cursor.executemany("""
        INSERT INTO products (product_id, vendor_id, category_id, name, description,
            price, mrp, discount_pct, sku, image_url, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, products)

    # ── 5. Seed warehouses ──
    warehouses = [
        ("WH001", "VND00001", "Tech World Warehouse",       "Electronic City",     "Bangalore", "Karnataka",   "560100"),
        ("WH002", "VND00002", "Fashion Hub Warehouse",       "Karol Bagh",          "New Delhi", "Delhi",       "110005"),
        ("WH003", "VND00003", "HomeStyle Storage",           "Bhiwandi",            "Mumbai",    "Maharashtra", "421302"),
        ("WH004", "VND00004", "Fresh Grocers Cold Storage",  "Miyapur",             "Hyderabad", "Telangana",   "500049"),
        ("WH005", "VND00005", "SportsZone Depot",            "Mansarovar",          "Jaipur",    "Rajasthan",   "302020"),
    ]

    cursor.executemany("""
        INSERT INTO warehouses (warehouse_id, vendor_id, name, address, city, state, pincode)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, warehouses)

    # ── 6. Seed inventory ──
    inventory_items = []
    product_ids = [p[0] for p in products]
    warehouse_map = {
        "VND00001": "WH001", "VND00002": "WH002", "VND00003": "WH003",
        "VND00004": "WH004", "VND00005": "WH005",
    }
    for pid, vid, *_ in products:
        wh = warehouse_map[vid]
        qty = random.randint(20, 500)
        reserved = random.randint(0, min(10, qty))
        reorder = random.choice([10, 20, 25, 50])
        inventory_items.append((pid, wh, qty, reserved, reorder, now))

    cursor.executemany("""
        INSERT INTO inventory (product_id, warehouse_id, quantity, reserved, reorder_level, last_restocked)
        VALUES (?, ?, ?, ?, ?, ?)
    """, inventory_items)

    # ── 7. Seed tax rates ──
    tax_entries = [
        ("GST 5%",  5.0,  "Essential goods"),
        ("GST 12%", 12.0, "Standard goods"),
        ("GST 18%", 18.0, "Standard services & electronics"),
        ("GST 28%", 28.0, "Luxury goods"),
    ]
    cursor.executemany("""
        INSERT INTO tax_rates (name, rate, description) VALUES (?, ?, ?)
    """, tax_entries)

    # ── 8. Seed currencies ──
    currency_entries = [
        ("INR", "Indian Rupee",   "\u20b9", 0.012, 1),
        ("USD", "US Dollar",      "$",      1.0,   1),
        ("EUR", "Euro",           "\u20ac", 1.08,  1),
        ("GBP", "British Pound",  "\u00a3", 1.27,  1),
    ]
    cursor.executemany("""
        INSERT INTO currencies (code, name, symbol, rate_to_usd, is_active) VALUES (?, ?, ?, ?, ?)
    """, currency_entries)

    # ── 9. Log marketplace seed audit entry ──
    cursor.execute("""
        INSERT INTO audit_logs (username, action, details)
        VALUES ('system', 'MARKETPLACE_SEED', 'Marketplace seed data generated: 5 vendors, 12 products, 15 categories')
    """)

    conn.commit()
    conn.close()


def get_table_row_count(table_name: str) -> int:
    """Get the row count for a table."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    conn.close()
    return count


def get_db_size() -> str:
    """Get the database file size as a formatted string."""
    if os.path.exists(DATABASE_PATH):
        size = os.path.getsize(DATABASE_PATH)
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size / (1024 * 1024):.1f} MB"
    return "0 B"
