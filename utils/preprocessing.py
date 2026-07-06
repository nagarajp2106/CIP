"""
Data Preprocessing Utilities — cleaning, validation, and anomaly detection.
"""
import pandas as pd
import numpy as np


def clean_data(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Perform automatic data cleaning on a DataFrame.

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

    # 2. Handle missing values
    missing = df.isnull().sum()
    for col in df.columns:
        if missing[col] > 0:
            if df[col].dtype in ['float64', 'int64']:
                median_val = df[col].median()
                df[col] = df[col].fillna(median_val)
                report["actions"].append(f"Filled {missing[col]} missing values in '{col}' with median ({median_val:.2f})")
            else:
                mode_val = df[col].mode()
                if len(mode_val) > 0:
                    df[col] = df[col].fillna(mode_val[0])
                    report["actions"].append(f"Filled {missing[col]} missing values in '{col}' with mode ({mode_val[0]})")
                else:
                    df[col] = df[col].fillna("Unknown")
                    report["actions"].append(f"Filled {missing[col]} missing values in '{col}' with 'Unknown'")

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
    schemas = {
        "customers": {
            "required": ["customer_id", "name"],
            "recommended": ["gender", "age", "occupation", "income", "region", "branch", "balance", "credit_score"],
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
