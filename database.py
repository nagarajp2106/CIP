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
    TRANSACTION_TYPES, TRANSACTION_CHANNELS
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


def _export_sample_csv():
    """Export customer data as a CSV for the datasets folder."""
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM customers LIMIT 1000", conn)
    csv_path = os.path.join(os.path.dirname(DATABASE_PATH), "..", "datasets", "bank_customers.csv")
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    df.to_csv(csv_path, index=False)
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
