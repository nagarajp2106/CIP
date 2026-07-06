"""
Feature Engineering Utilities — derived features, encoding, and scaling.
"""
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler, MinMaxScaler


# ──────────────────────────────────────────────
# Feature Generators
# ──────────────────────────────────────────────

def create_age_group(df: pd.DataFrame, col: str = "age") -> pd.DataFrame:
    """Add age group categories."""
    if col not in df.columns:
        return df
    df = df.copy()
    bins = [0, 25, 35, 45, 55, 65, 100]
    labels = ["18-25", "26-35", "36-45", "46-55", "56-65", "65+"]
    df["age_group"] = pd.cut(df[col], bins=bins, labels=labels, right=True)
    return df


def create_income_category(df: pd.DataFrame, col: str = "income") -> pd.DataFrame:
    """Add income category based on quartiles."""
    if col not in df.columns:
        return df
    df = df.copy()
    q25 = df[col].quantile(0.25)
    q50 = df[col].quantile(0.50)
    q75 = df[col].quantile(0.75)

    def categorize(val):
        if val <= q25:
            return "Low"
        elif val <= q50:
            return "Medium"
        elif val <= q75:
            return "High"
        else:
            return "Very High"

    df["income_category"] = df[col].apply(categorize)
    return df


def create_balance_category(df: pd.DataFrame, col: str = "balance") -> pd.DataFrame:
    """Add balance category."""
    if col not in df.columns:
        return df
    df = df.copy()
    conditions = [
        df[col] < 5000,
        (df[col] >= 5000) & (df[col] < 25000),
        (df[col] >= 25000) & (df[col] < 100000),
        df[col] >= 100000,
    ]
    categories = ["Low", "Medium", "High", "Premium"]
    df["balance_category"] = np.select(conditions, categories, default="Unknown")
    return df


def calculate_loan_ratio(df: pd.DataFrame, loan_col: str = "loan_amount",
                         income_col: str = "income") -> pd.DataFrame:
    """Calculate loan-to-income ratio."""
    if loan_col not in df.columns or income_col not in df.columns:
        return df
    df = df.copy()
    df["loan_ratio"] = np.where(df[income_col] > 0, df[loan_col] / df[income_col], 0)
    df["loan_ratio"] = df["loan_ratio"].round(4)
    return df


def calculate_credit_utilization(df: pd.DataFrame, outstanding_col: str = "outstanding_amount",
                                  limit_col: str = "card_limit") -> pd.DataFrame:
    """Calculate credit utilization percentage."""
    if outstanding_col not in df.columns or limit_col not in df.columns:
        return df
    df = df.copy()
    df["credit_utilization"] = np.where(
        df[limit_col] > 0, (df[outstanding_col] / df[limit_col]) * 100, 0
    )
    df["credit_utilization"] = df["credit_utilization"].round(2)
    return df


def calculate_customer_tenure(df: pd.DataFrame, since_col: str = "customer_since") -> pd.DataFrame:
    """Calculate customer tenure in months."""
    if since_col not in df.columns:
        return df
    df = df.copy()
    try:
        df[since_col] = pd.to_datetime(df[since_col], errors='coerce')
        now = pd.Timestamp.now()
        df["tenure_months"] = ((now - df[since_col]).dt.days / 30.44).round(0).astype(int)
        df["tenure_months"] = df["tenure_months"].clip(lower=0)
    except Exception:
        df["tenure_months"] = 0
    return df


def calculate_avg_monthly_transactions(df: pd.DataFrame, customer_id_col: str = "customer_id",
                                        transactions_df: pd.DataFrame = None) -> pd.DataFrame:
    """Calculate average monthly transaction count per customer."""
    if transactions_df is None or transactions_df.empty:
        df = df.copy()
        df["avg_monthly_transactions"] = 0
        return df

    txn_counts = transactions_df.groupby(customer_id_col).size().reset_index(name="total_transactions")
    # Assume 12 months of data
    txn_counts["avg_monthly_transactions"] = (txn_counts["total_transactions"] / 12).round(1)

    df = df.copy()
    df = df.merge(txn_counts[[customer_id_col, "avg_monthly_transactions"]],
                  on=customer_id_col, how="left")
    df["avg_monthly_transactions"] = df["avg_monthly_transactions"].fillna(0)
    return df


def calculate_customer_value_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate a composite customer value score (0-100).
    Based on balance, income, credit score, and tenure.
    """
    df = df.copy()
    score = pd.Series(0, index=df.index, dtype=float)

    # Balance component (0-30 points)
    if "balance" in df.columns:
        bal_norm = df["balance"].clip(upper=500000) / 500000
        score += bal_norm * 30

    # Income component (0-25 points)
    if "income" in df.columns:
        inc_norm = df["income"].clip(upper=200000) / 200000
        score += inc_norm * 25

    # Credit score component (0-25 points)
    if "credit_score" in df.columns:
        cs_norm = (df["credit_score"].clip(lower=300, upper=850) - 300) / 550
        score += cs_norm * 25

    # Tenure component (0-20 points)
    if "tenure_months" in df.columns:
        ten_norm = df["tenure_months"].clip(upper=120) / 120
        score += ten_norm * 20

    df["customer_value_score"] = score.round(1)
    return df


def apply_all_features(df: pd.DataFrame, transactions_df: pd.DataFrame = None) -> pd.DataFrame:
    """Apply all feature engineering in sequence."""
    df = create_age_group(df)
    df = create_income_category(df)
    df = create_balance_category(df)
    df = calculate_customer_tenure(df)
    df = calculate_avg_monthly_transactions(df, transactions_df=transactions_df)
    df = calculate_customer_value_score(df)
    return df


# ──────────────────────────────────────────────
# Encoding
# ──────────────────────────────────────────────

def encode_features(df: pd.DataFrame, method: str = "label", columns: list = None) -> tuple[pd.DataFrame, dict]:
    """
    Encode categorical features.

    Args:
        df: Input DataFrame
        method: "label" or "onehot"
        columns: Columns to encode (default: all object columns)

    Returns:
        Tuple of (encoded DataFrame, encoders dict)
    """
    df = df.copy()
    if columns is None:
        columns = df.select_dtypes(include=['object', 'category']).columns.tolist()

    encoders = {}

    if method == "label":
        for col in columns:
            if col in df.columns:
                le = LabelEncoder()
                df[col] = le.fit_transform(df[col].astype(str))
                encoders[col] = le
    elif method == "onehot":
        df = pd.get_dummies(df, columns=columns, drop_first=True)

    return df, encoders


# ──────────────────────────────────────────────
# Scaling
# ──────────────────────────────────────────────

def scale_features(df: pd.DataFrame, method: str = "standard", columns: list = None) -> tuple[pd.DataFrame, object]:
    """
    Scale numeric features.

    Args:
        df: Input DataFrame
        method: "standard" (StandardScaler) or "minmax" (MinMaxScaler)
        columns: Columns to scale (default: all numeric)

    Returns:
        Tuple of (scaled DataFrame, scaler object)
    """
    df = df.copy()
    if columns is None:
        columns = df.select_dtypes(include=[np.number]).columns.tolist()

    valid_cols = [c for c in columns if c in df.columns]
    if not valid_cols:
        return df, None

    if method == "standard":
        scaler = StandardScaler()
    else:
        scaler = MinMaxScaler()

    df[valid_cols] = scaler.fit_transform(df[valid_cols])
    return df, scaler
