"""
Data Preprocessing Utilities — cleaning, validation, and anomaly detection.
"""
import pandas as pd
import numpy as np


# ──────────────────────────────────────────────
# Column Classification Registry
# ──────────────────────────────────────────────
# Derived from the actual SQLite schema in database.py.
# Each column is classified so clean_data() can apply the
# correct imputation strategy and classify_and_filter() can
# exclude rows with missing primary-key / required-ID values.
#
# Categories:
#   primary_key — table's own unique identifier, NEVER impute
#   id_ref      — foreign-key reference to another table, NEVER impute
#   numeric     — median-fill
#   categorical — mode-fill
#   date        — leave as-is (do not impute)
#   flag        — integer 0/1 flag, fill with 0

TABLE_COLUMN_METADATA = {
    "customers": {
        "customer_id":    "primary_key",
        "name":           "categorical",
        "gender":         "categorical",
        "age":            "numeric",
        "occupation":     "categorical",
        "income":         "numeric",
        "region":         "categorical",
        "branch":         "categorical",
        "balance":        "numeric",
        "credit_score":   "numeric",
        "customer_since": "date",
        "email":          "categorical",
        "phone":          "categorical",
        "is_active":      "flag",
        "risk_level":     "categorical",
        "churn_score":    "numeric",
        "clv_score":      "numeric",
        "segment":        "categorical",
    },
    "accounts": {
        "account_number": "primary_key",
        "customer_id":    "id_ref",
        "account_type":   "categorical",
        "balance":        "numeric",
        "status":         "categorical",
        "opened_date":    "date",
    },
    "transactions": {
        "transaction_id": "primary_key",
        "customer_id":    "id_ref",
        "account_number": "id_ref",
        "amount":         "numeric",
        "date":           "date",
        "type":           "categorical",
        "channel":        "categorical",
        "merchant":       "categorical",
        "description":    "categorical",
        "is_fraud":       "flag",
    },
    "loans": {
        "loan_id":        "primary_key",
        "customer_id":    "id_ref",
        "loan_type":      "categorical",
        "loan_amount":    "numeric",
        "interest_rate":  "numeric",
        "tenure_months":  "numeric",
        "emi":            "numeric",
        "status":         "categorical",
        "applied_date":   "date",
        "approved_date":  "date",
    },
    "cards": {
        "card_number":       "primary_key",
        "customer_id":       "id_ref",
        "card_type":         "categorical",
        "card_limit":        "numeric",
        "outstanding_amount": "numeric",
        "status":            "categorical",
        "issued_date":       "date",
        "expiry_date":       "date",
    },
    # ── Marketplace Tables ──
    "vendors": {
        "vendor_id":        "primary_key",
        "user_id":          "id_ref",
        "business_name":    "categorical",
        "owner_name":       "categorical",
        "email":            "categorical",
        "phone":            "categorical",
        "gst_number":       "categorical",
        "address":          "categorical",
        "city":             "categorical",
        "state":            "categorical",
        "commission_rate":  "numeric",
        "status":           "categorical",
        "created_at":       "date",
        "updated_at":       "date",
    },
    "categories": {
        "category_id":  "primary_key",
        "name":         "categorical",
        "parent_id":    "id_ref",
        "description":  "categorical",
        "icon":         "categorical",
        "is_active":    "flag",
        "created_at":   "date",
    },
    "products": {
        "product_id":   "primary_key",
        "vendor_id":    "id_ref",
        "category_id":  "id_ref",
        "name":         "categorical",
        "description":  "categorical",
        "price":        "numeric",
        "mrp":          "numeric",
        "discount_pct": "numeric",
        "sku":          "categorical",
        "image_url":    "categorical",
        "status":       "categorical",
        "rating_avg":   "numeric",
        "rating_count": "numeric",
        "created_at":   "date",
        "updated_at":   "date",
    },
    "warehouses": {
        "warehouse_id": "primary_key",
        "vendor_id":    "id_ref",
        "name":         "categorical",
        "address":      "categorical",
        "city":         "categorical",
        "state":        "categorical",
        "pincode":      "categorical",
        "is_active":    "flag",
        "created_at":   "date",
    },
    "inventory": {
        "id":             "primary_key",
        "product_id":     "id_ref",
        "warehouse_id":   "id_ref",
        "quantity":       "numeric",
        "reserved":       "numeric",
        "reorder_level":  "numeric",
        "last_restocked": "date",
    },
    "orders": {
        "order_id":         "primary_key",
        "customer_id":      "id_ref",
        "total_amount":     "numeric",
        "tax_amount":       "numeric",
        "shipping_amount":  "numeric",
        "discount_amount":  "numeric",
        "net_amount":       "numeric",
        "status":           "categorical",
        "shipping_address": "categorical",
        "shipping_city":    "categorical",
        "shipping_state":   "categorical",
        "shipping_pincode": "categorical",
        "notes":            "categorical",
        "placed_at":        "date",
        "updated_at":       "date",
    },
    "order_items": {
        "id":          "primary_key",
        "order_id":    "id_ref",
        "product_id":  "id_ref",
        "vendor_id":   "id_ref",
        "quantity":    "numeric",
        "unit_price":  "numeric",
        "total_price": "numeric",
        "status":      "categorical",
    },
    "cart": {
        "id":          "primary_key",
        "customer_id": "id_ref",
        "product_id":  "id_ref",
        "quantity":    "numeric",
        "added_at":    "date",
    },
    "wishlist": {
        "id":          "primary_key",
        "customer_id": "id_ref",
        "product_id":  "id_ref",
        "added_at":    "date",
    },
    "reviews": {
        "review_id":   "primary_key",
        "product_id":  "id_ref",
        "customer_id": "id_ref",
        "rating":      "numeric",
        "title":       "categorical",
        "comment":     "categorical",
        "is_approved": "flag",
        "created_at":  "date",
    },
    "payments": {
        "payment_id":      "primary_key",
        "order_id":        "id_ref",
        "amount":          "numeric",
        "method":          "categorical",
        "status":          "categorical",
        "transaction_ref": "categorical",
        "paid_at":         "date",
        "created_at":      "date",
    },
    "shipments": {
        "shipment_id":        "primary_key",
        "order_id":           "id_ref",
        "carrier":            "categorical",
        "tracking_number":    "categorical",
        "status":             "categorical",
        "estimated_delivery": "date",
        "shipped_at":         "date",
        "delivered_at":       "date",
        "created_at":         "date",
    },
    "refunds": {
        "refund_id":   "primary_key",
        "order_id":    "id_ref",
        "payment_id":  "id_ref",
        "amount":      "numeric",
        "reason":      "categorical",
        "status":      "categorical",
        "approved_at": "date",
        "created_at":  "date",
    },
    "notifications": {
        "id":         "primary_key",
        "user_id":    "id_ref",
        "title":      "categorical",
        "message":    "categorical",
        "type":       "categorical",
        "is_read":    "flag",
        "created_at": "date",
    },
    "commission_ledger": {
        "id":                "primary_key",
        "vendor_id":         "id_ref",
        "order_id":          "id_ref",
        "order_amount":      "numeric",
        "commission_rate":   "numeric",
        "commission_amount": "numeric",
        "status":            "categorical",
        "created_at":        "date",
    },
    "tax_rates": {
        "id":          "primary_key",
        "name":        "categorical",
        "rate":        "numeric",
        "description": "categorical",
        "is_active":   "flag",
    },
    "currencies": {
        "code":        "primary_key",
        "name":        "categorical",
        "symbol":      "categorical",
        "rate_to_usd": "numeric",
        "is_active":   "flag",
    },
}


def _get_column_type(table_name: str, col_name: str) -> str:
    """Look up a column's classification. Falls back to heuristic."""
    meta = TABLE_COLUMN_METADATA.get(table_name, {})
    if col_name in meta:
        return meta[col_name]
    # Heuristic fallback for columns not in the registry
    lower = col_name.lower()
    if lower.endswith("_id") or lower.endswith("_number"):
        return "id_ref"
    if "date" in lower or "since" in lower:
        return "date"
    return "categorical"


def _coerce_flag_column(series: pd.Series) -> pd.Series:
    """
    Coerce a boolean/flag column to integer 0/1.

    Handles numeric values as-is, plus common text representations:
      1 / True / Yes / Active  → 1
      0 / False / No / Inactive → 0
    Unrecognised text values are set to NaN (so the caller can default
    or emit a warning).
    """
    TRUE_VALS  = {"1", "true", "yes", "active", "1.0"}
    FALSE_VALS = {"0", "false", "no", "inactive", "0.0"}

    def _map(val):
        if pd.isna(val):
            return np.nan
        s = str(val).strip().lower()
        if s in TRUE_VALS:
            return 1
        if s in FALSE_VALS:
            return 0
        # Try numeric parse as last resort
        try:
            n = float(s)
            return 1 if n != 0 else 0
        except ValueError:
            return np.nan  # genuinely unmappable — will default to 0

    return series.map(_map)



# ──────────────────────────────────────────────
# Pre-Clean Classification & Filtering
# ──────────────────────────────────────────────

def classify_and_filter(df: pd.DataFrame, table_name: str) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """
    Pre-screen rows BEFORE auto-clean. Rows with missing primary-key
    or required foreign-key values are separated into an 'invalid' set
    so they are never mode-filled with a duplicate value.

    Args:
        df: DataFrame with columns already lowercased/standardized.
        table_name: Target table name (e.g. 'accounts').

    Returns:
        (valid_df, invalid_df, classification_report)
        classification_report contains 'excluded_rows' count and
        'exclusion_reasons' list of (row_index, reason) tuples.
    """
    meta = TABLE_COLUMN_METADATA.get(table_name, {})
    # Columns that must not be missing — PKs and required FK refs
    critical_cols = [col for col, ctype in meta.items()
                     if ctype in ("primary_key", "id_ref")]

    report = {
        "excluded_rows": 0,
        "exclusion_reasons": [],  # list of (original_index, reason_string)
    }

    if not critical_cols:
        return df.copy(), pd.DataFrame(columns=df.columns), report

    # Identify rows where ANY critical column is null / empty-string / whitespace
    invalid_mask = pd.Series(False, index=df.index)
    for col in critical_cols:
        if col not in df.columns:
            continue
        is_missing = df[col].isna()
        # Also catch empty strings that slipped through as non-null
        if df[col].dtype == object:
            is_missing = is_missing | df[col].astype(str).str.strip().isin(["", "nan", "None"])
        for idx in df.index[is_missing & ~invalid_mask]:
            col_type = meta.get(col, "id_ref")
            label = "primary key" if col_type == "primary_key" else "required ID"
            report["exclusion_reasons"].append(
                (int(idx), f"Missing {label}: '{col}'")
            )
        invalid_mask = invalid_mask | is_missing

    valid_df = df[~invalid_mask].copy()
    invalid_df = df[invalid_mask].copy()
    report["excluded_rows"] = len(invalid_df)

    return valid_df, invalid_df, report


# ──────────────────────────────────────────────
# Smart Data Cleaning
# ──────────────────────────────────────────────

def clean_data(df: pd.DataFrame, table_name: str = None) -> tuple[pd.DataFrame, dict]:
    """
    Perform automatic data cleaning on a DataFrame.
    When table_name is provided, uses column-type-aware imputation
    (skips PK/ID/date columns). Without it, falls back to legacy behavior.

    Returns:
        Tuple of (cleaned DataFrame, cleaning report dict)
    """
    report = {
        "original_rows": len(df),
        "original_cols": len(df.columns),
        "actions": [],
    }

    # 1. Remove exact duplicate rows
    n_dupes = df.duplicated().sum()
    if n_dupes > 0:
        df = df.drop_duplicates()
        report["actions"].append(f"Removed {n_dupes} duplicate rows")

    # 2. Handle missing values — type-aware when table_name is given
    missing = df.isnull().sum()
    for col in df.columns:
        if missing[col] == 0:
            continue

        col_type = _get_column_type(table_name, col) if table_name else None

        # SKIP imputation for primary keys, ID refs, and dates
        if col_type in ("primary_key", "id_ref"):
            report["actions"].append(
                f"Skipped {missing[col]} missing values in '{col}' (unique ID column — not imputed)"
            )
            continue
        if col_type == "date":
            report["actions"].append(
                f"Skipped {missing[col]} missing values in '{col}' (date column — not imputed)"
            )
            continue

        # Numeric columns → median-fill
        if col_type == "numeric" or (col_type is None and df[col].dtype in ['float64', 'int64']):
            numeric_series = pd.to_numeric(df[col], errors='coerce')
            median_val = numeric_series.median()
            if pd.notna(median_val):
                df[col] = numeric_series.fillna(median_val)
                report["actions"].append(
                    f"Filled {missing[col]} missing values in '{col}' with median ({median_val:.2f})"
                )
            else:
                df[col] = numeric_series.fillna(0)
                report["actions"].append(
                    f"Filled {missing[col]} missing values in '{col}' with 0 (no valid median)"
                )
            continue

        # Flag columns → coerce text to 0/1, then fill missing with 0
        if col_type == "flag":
            df[col] = _coerce_flag_column(df[col])
            df[col] = df[col].fillna(0).astype(int)
            report["actions"].append(
                f"Filled {missing[col]} missing values in '{col}' with 0 (flag column)"
            )
            continue

        # Categorical columns → mode-fill (default for object types)
        mode_val = df[col].mode()
        if len(mode_val) > 0:
            df[col] = df[col].fillna(mode_val[0])
            report["actions"].append(
                f"Filled {missing[col]} missing values in '{col}' with mode ({mode_val[0]})"
            )
        else:
            df[col] = df[col].fillna("Unknown")
            report["actions"].append(
                f"Filled {missing[col]} missing values in '{col}' with 'Unknown'"
            )

    # 3. Fix negative values in balance/amount columns
    money_cols = [c for c in df.columns if any(kw in c.lower() for kw in ['balance', 'amount', 'income', 'salary'])]
    for col in money_cols:
        if df[col].dtype in ['float64', 'int64']:
            neg_count = (df[col] < 0).sum()
            if neg_count > 0:
                df[col] = df[col].abs()
                report["actions"].append(f"Corrected {neg_count} negative values in '{col}'")

    # 4. Standardize string columns
    str_cols = df.select_dtypes(include=['object']).columns
    for col in str_cols:
        df[col] = df[col].astype(str).str.strip()

    report["cleaned_rows"] = len(df)
    report["cleaned_cols"] = len(df.columns)
    return df, report


def validate_upload(df: pd.DataFrame, table_name: str) -> dict:
    """
    Validate uploaded data against expected schema.

    Args:
        df: Uploaded DataFrame
        table_name: Target table name

    Returns:
        Validation report dict with 'valid' bool and 'errors'/'warnings' lists
    """
    report = {"valid": True, "errors": [], "warnings": [], "info": []}

    # Expected schemas
    # NOTE: For customers, risk_level/churn_score/clv_score/segment are
    # system-computed columns with schema defaults.  They are NOT listed
    # as required or recommended so a CSV that omits them still passes
    # validation; SQLite defaults will fill them on insert.
    schemas = {
        "customers": {
            "required": ["customer_id", "name"],
            "recommended": ["gender", "age", "occupation", "income", "region", "branch", "balance", "credit_score"],
            "optional_derived": ["risk_level", "churn_score", "clv_score", "segment"],
            "types": {"age": "numeric", "income": "numeric", "balance": "numeric", "credit_score": "numeric"}
        },
        "accounts": {
            "required": ["account_number", "customer_id", "account_type"],
            "recommended": ["balance", "status"],
            "types": {"balance": "numeric"}
        },
        "transactions": {
            "required": ["transaction_id", "customer_id", "amount", "date", "type"],
            "recommended": ["channel", "merchant"],
            "types": {"amount": "numeric"}
        },
        "loans": {
            "required": ["loan_id", "customer_id", "loan_type", "loan_amount"],
            "recommended": ["interest_rate", "status", "tenure_months"],
            "types": {"loan_amount": "numeric", "interest_rate": "numeric"}
        },
        "cards": {
            "required": ["card_number", "customer_id", "card_type"],
            "recommended": ["card_limit", "outstanding_amount"],
            "types": {"card_limit": "numeric", "outstanding_amount": "numeric"}
        },
    }

    schema = schemas.get(table_name)
    if not schema:
        report["errors"].append(f"Unknown table: {table_name}")
        report["valid"] = False
        return report

    # Check required columns
    df_cols = [c.lower().replace(" ", "_") for c in df.columns]
    for req in schema["required"]:
        if req not in df_cols:
            report["errors"].append(f"Missing required column: '{req}'")
            report["valid"] = False

    # Check recommended columns
    for rec in schema.get("recommended", []):
        if rec not in df_cols:
            report["warnings"].append(f"Missing recommended column: '{rec}'")

    # Check for duplicates in ID columns
    if schema["required"]:
        id_col = schema["required"][0]
        if id_col in df_cols:
            idx = df_cols.index(id_col)
            actual_col = df.columns[idx]
            n_dupes = df[actual_col].duplicated().sum()
            if n_dupes > 0:
                report["warnings"].append(f"{n_dupes} duplicate values in '{id_col}'")

    # Check data types
    for col, expected_type in schema.get("types", {}).items():
        if col in df_cols:
            idx = df_cols.index(col)
            actual_col = df.columns[idx]
            if expected_type == "numeric":
                non_numeric = pd.to_numeric(df[actual_col], errors='coerce').isna().sum()
                if non_numeric > 0:
                    report["warnings"].append(f"{non_numeric} non-numeric values in '{col}'")

    # Check for empty DataFrame
    if len(df) == 0:
        report["errors"].append("Uploaded file is empty")
        report["valid"] = False

    # Info
    report["info"].append(f"Total rows: {len(df)}")
    report["info"].append(f"Total columns: {len(df.columns)}")
    report["info"].append(f"Missing values: {df.isnull().sum().sum()}")

    return report


def detect_anomalies(df: pd.DataFrame, columns: list = None, threshold: float = 3.0) -> pd.DataFrame:
    """
    Detect statistical outliers using z-score method.

    Args:
        df: Input DataFrame
        columns: Numeric columns to check (default: all numeric)
        threshold: Z-score threshold for outlier detection

    Returns:
        DataFrame with outlier flags
    """
    if columns is None:
        columns = df.select_dtypes(include=[np.number]).columns.tolist()

    result = df.copy()
    result['is_outlier'] = False

    for col in columns:
        if col in result.columns and result[col].dtype in ['float64', 'int64']:
            mean = result[col].mean()
            std = result[col].std()
            if std > 0:
                z_scores = np.abs((result[col] - mean) / std)
                result.loc[z_scores > threshold, 'is_outlier'] = True

    return result


def get_data_quality_report(df: pd.DataFrame) -> dict:
    """Generate a comprehensive data quality report."""
    report = {
        "shape": {"rows": len(df), "columns": len(df.columns)},
        "missing": {},
        "duplicates": int(df.duplicated().sum()),
        "dtypes": {},
        "numeric_summary": {},
    }

    # Missing values per column
    for col in df.columns:
        missing = int(df[col].isnull().sum())
        pct = missing / len(df) * 100 if len(df) > 0 else 0
        report["missing"][col] = {"count": missing, "percentage": round(pct, 2)}

    # Data types
    for col in df.columns:
        report["dtypes"][col] = str(df[col].dtype)

    # Numeric summary
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        report["numeric_summary"][col] = {
            "mean": round(float(df[col].mean()), 2),
            "median": round(float(df[col].median()), 2),
            "std": round(float(df[col].std()), 2),
            "min": round(float(df[col].min()), 2),
            "max": round(float(df[col].max()), 2),
        }

    return report


# ──────────────────────────────────────────────
# Foreign Key Validation
# ──────────────────────────────────────────────
# Maps child table FK columns to their parent table + parent column.
# Derived from the FOREIGN KEY constraints in database.py.

FK_MAP = {
    "accounts":     [{"column": "customer_id", "parent_table": "customers", "parent_column": "customer_id"}],
    "transactions": [
        {"column": "customer_id",    "parent_table": "customers", "parent_column": "customer_id"},
        {"column": "account_number", "parent_table": "accounts",  "parent_column": "account_number"},
    ],
    "loans":        [{"column": "customer_id", "parent_table": "customers", "parent_column": "customer_id"}],
    "cards":        [{"column": "customer_id", "parent_table": "customers", "parent_column": "customer_id"}],
    "customers":    [],  # No FK — this is the root table
}


def check_foreign_keys(df: pd.DataFrame, table_name: str, db_connection) -> dict:
    """
    Check every foreign key column in df against its parent table in the database.

    Args:
        df: DataFrame with columns already lowercased/standardized.
        table_name: Target table name (e.g. 'accounts').
        db_connection: Active SQLite connection.

    Returns:
        dict with 'has_issues' bool and 'issues' list of dicts:
        [{"column": "customer_id", "missing_count": 847,
          "total_rows": 1000, "sample_values": ["CUST98001", ...],
          "invalid_indices": [0, 1, 2, ...]}]
    """
    report = {"has_issues": False, "issues": []}

    fk_refs = FK_MAP.get(table_name, [])
    if not fk_refs:
        return report

    for ref in fk_refs:
        fk_col = ref["column"]
        parent_table = ref["parent_table"]
        parent_col = ref["parent_column"]

        if fk_col not in df.columns:
            continue

        # Get all valid parent IDs from the database
        try:
            parent_df = pd.read_sql(
                f"SELECT DISTINCT {parent_col} FROM {parent_table}", db_connection
            )
            valid_ids = set(parent_df[parent_col].dropna().astype(str).tolist())
        except Exception:
            valid_ids = set()

        # Find rows whose FK value doesn't exist in the parent table
        df_fk_values = df[fk_col].astype(str).str.strip()
        invalid_mask = ~df_fk_values.isin(valid_ids) & df[fk_col].notna()
        invalid_indices = df.index[invalid_mask].tolist()
        missing_count = len(invalid_indices)

        if missing_count > 0:
            # Collect up to 10 sample values for display
            sample_vals = df_fk_values[invalid_mask].unique()[:10].tolist()
            report["has_issues"] = True
            report["issues"].append({
                "column": fk_col,
                "parent_table": parent_table,
                "parent_column": parent_col,
                "missing_count": missing_count,
                "total_rows": len(df),
                "sample_values": sample_vals,
                "invalid_indices": invalid_indices,
            })

    return report
