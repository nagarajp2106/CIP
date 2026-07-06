"""
Prediction Utilities — ML model training, loading, and evaluation.
Central module for all 9 AI models.
"""
import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor, IsolationForest
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, mean_squared_error, r2_score
from config import MODEL_PATHS, MODELS_DIR

try:
    from xgboost import XGBClassifier
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False


def load_model(model_name: str):
    """Load a saved model from disk."""
    path = MODEL_PATHS.get(model_name)
    if path and os.path.exists(path):
        return joblib.load(path)
    return None


def save_model(model, model_name: str):
    """Save a model to disk."""
    os.makedirs(MODELS_DIR, exist_ok=True)
    path = MODEL_PATHS.get(model_name)
    if path:
        joblib.dump(model, path)


def get_feature_importance(model, feature_names: list) -> pd.DataFrame:
    """Extract feature importance from a tree-based model."""
    try:
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
            df = pd.DataFrame({
                "feature": feature_names[:len(importances)],
                "importance": importances
            }).sort_values("importance", ascending=False)
            return df
    except Exception:
        pass
    return pd.DataFrame({"feature": feature_names, "importance": [0] * len(feature_names)})


def evaluate_classifier(model, X_test, y_test) -> dict:
    """Evaluate a classifier and return metrics."""
    y_pred = model.predict(X_test)
    metrics = {
        "accuracy": round(accuracy_score(y_test, y_pred), 4),
        "precision": round(precision_score(y_test, y_pred, average='weighted', zero_division=0), 4),
        "recall": round(recall_score(y_test, y_pred, average='weighted', zero_division=0), 4),
        "f1_score": round(f1_score(y_test, y_pred, average='weighted', zero_division=0), 4),
    }
    try:
        if hasattr(model, 'predict_proba'):
            y_proba = model.predict_proba(X_test)
            if y_proba.shape[1] == 2:
                metrics["auc"] = round(roc_auc_score(y_test, y_proba[:, 1]), 4)
    except Exception:
        pass
    return metrics


def evaluate_regressor(model, X_test, y_test) -> dict:
    """Evaluate a regressor and return metrics."""
    y_pred = model.predict(X_test)
    return {
        "r2_score": round(r2_score(y_test, y_pred), 4),
        "rmse": round(np.sqrt(mean_squared_error(y_test, y_pred)), 2),
        "mae": round(np.mean(np.abs(y_test - y_pred)), 2),
    }


# ──────────────────────────────────────────────
# Model-Specific Training Functions
# ──────────────────────────────────────────────

def train_segmentation_model(df: pd.DataFrame) -> tuple:
    """Train customer segmentation model (KMeans k=5)."""
    features = ["income", "balance", "credit_score", "age"]
    available = [f for f in features if f in df.columns]
    if len(available) < 2:
        return None, None, None

    X = df[available].fillna(0).copy()
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = KMeans(n_clusters=5, random_state=42, n_init=10)
    model.fit(X_scaled)

    segment_labels = {0: "Premium", 1: "High Value", 2: "Regular", 3: "Low Value", 4: "Dormant"}

    # Save model and scaler together
    model_data = {"model": model, "scaler": scaler, "features": available, "labels": segment_labels}
    save_model(model_data, "segmentation")

    return model_data, X_scaled, available


def train_churn_model(df: pd.DataFrame, txn_df: pd.DataFrame = None) -> tuple:
    """Train churn prediction model (Random Forest)."""
    # Create churn label: inactive customers are churned
    df = df.copy()
    df["churned"] = (df["is_active"] == 0).astype(int)

    features = ["age", "income", "balance", "credit_score"]
    available = [f for f in features if f in df.columns]

    X = df[available].fillna(0)
    y = df["churned"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    model = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10)
    model.fit(X_train, y_train)

    metrics = evaluate_classifier(model, X_test, y_test)

    model_data = {"model": model, "features": available, "metrics": metrics}
    save_model(model_data, "churn")

    return model_data, metrics


def train_credit_risk_model(df: pd.DataFrame) -> tuple:
    """Train credit risk model (XGBoost or Random Forest)."""
    df = df.copy()

    # Create risk label from credit_score
    def risk_label(score):
        if score >= 750:
            return 0  # Low
        elif score >= 650:
            return 1  # Medium
        else:
            return 2  # High

    df["risk_class"] = df["credit_score"].apply(risk_label)

    features = ["age", "income", "balance"]
    available = [f for f in features if f in df.columns]

    X = df[available].fillna(0)
    y = df["risk_class"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    if HAS_XGBOOST:
        model = XGBClassifier(n_estimators=100, max_depth=6, random_state=42, eval_metric='mlogloss')
    else:
        model = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=8)

    model.fit(X_train, y_train)
    metrics = evaluate_classifier(model, X_test, y_test)

    model_data = {"model": model, "features": available, "metrics": metrics, "risk_labels": {0: "Low", 1: "Medium", 2: "High"}}
    save_model(model_data, "credit_risk")

    return model_data, metrics


def train_loan_approval_model(loans_df: pd.DataFrame, customers_df: pd.DataFrame) -> tuple:
    """Train loan approval model (Random Forest)."""
    # Merge loan with customer data
    df = loans_df.merge(customers_df[["customer_id", "income", "age", "credit_score", "balance"]], on="customer_id", how="left")
    df = df.dropna(subset=["income", "credit_score"])

    # Label: approved (Active/Closed) = 1, Rejected/Defaulted/Pending = 0
    df["approved"] = df["status"].isin(["Active", "Closed"]).astype(int)

    features = ["income", "credit_score", "loan_amount", "interest_rate", "age", "balance"]
    available = [f for f in features if f in df.columns]

    X = df[available].fillna(0)
    y = df["approved"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    model = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10)
    model.fit(X_train, y_train)
    metrics = evaluate_classifier(model, X_test, y_test)

    model_data = {"model": model, "features": available, "metrics": metrics}
    save_model(model_data, "loan_approval")

    return model_data, metrics


def train_clv_model(df: pd.DataFrame) -> tuple:
    """Train Customer Lifetime Value model (Gradient Boosting Regressor)."""
    df = df.copy()
    # CLV target: income * tenure factor * balance factor
    df["customer_since"] = pd.to_datetime(df["customer_since"], errors='coerce')
    df["tenure_days"] = (pd.Timestamp.now() - df["customer_since"]).dt.days.fillna(365)
    df["clv_target"] = (df["income"].fillna(0) * 0.1 + df["balance"].fillna(0) * 0.5) * (df["tenure_days"] / 365)
    df["clv_target"] = df["clv_target"].clip(lower=0)

    features = ["income", "balance", "credit_score", "age"]
    available = [f for f in features if f in df.columns]

    X = df[available].fillna(0)
    y = df["clv_target"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = GradientBoostingRegressor(n_estimators=100, random_state=42, max_depth=5)
    model.fit(X_train, y_train)
    metrics = evaluate_regressor(model, X_test, y_test)

    model_data = {"model": model, "features": available, "metrics": metrics}
    save_model(model_data, "clv")

    return model_data, metrics


def train_fraud_model(txn_df: pd.DataFrame) -> tuple:
    """Train fraud detection model (Isolation Forest)."""
    features = ["amount"]
    X = txn_df[features].fillna(0)

    model = IsolationForest(contamination=0.03, random_state=42, n_estimators=100)
    model.fit(X)

    model_data = {"model": model, "features": features}
    save_model(model_data, "fraud")

    return model_data, {}


def train_income_model(df: pd.DataFrame) -> tuple:
    """Train income prediction model (Gradient Boosting Regressor)."""
    df = df.copy()
    df = df.dropna(subset=["income"])
    df = df[df["income"] > 0]

    # Encode occupation
    le = LabelEncoder()
    df["occupation_enc"] = le.fit_transform(df["occupation"].fillna("Unknown"))

    features = ["age", "balance", "credit_score", "occupation_enc"]
    available = [f for f in features if f in df.columns]

    X = df[available].fillna(0)
    y = df["income"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = GradientBoostingRegressor(n_estimators=100, random_state=42, max_depth=5)
    model.fit(X_train, y_train)
    metrics = evaluate_regressor(model, X_test, y_test)

    model_data = {"model": model, "features": available, "metrics": metrics, "label_encoder": le}
    save_model(model_data, "income")

    return model_data, metrics


def train_deposit_model(df: pd.DataFrame) -> tuple:
    """Train deposit subscription prediction model (Random Forest)."""
    df = df.copy()

    # Create deposit target: customers with high balance and savings account are more likely
    df["deposit_target"] = ((df["balance"] > df["balance"].median()) & (df["is_active"] == 1)).astype(int)

    features = ["age", "income", "balance", "credit_score"]
    available = [f for f in features if f in df.columns]

    X = df[available].fillna(0)
    y = df["deposit_target"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    model = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=8)
    model.fit(X_train, y_train)
    metrics = evaluate_classifier(model, X_test, y_test)

    model_data = {"model": model, "features": available, "metrics": metrics}
    save_model(model_data, "deposit")

    return model_data, metrics


def train_all_models():
    """Train all ML models from database data."""
    from database import get_connection
    conn = get_connection()
    customers_df = pd.read_sql("SELECT * FROM customers", conn)
    transactions_df = pd.read_sql("SELECT * FROM transactions", conn)
    loans_df = pd.read_sql("SELECT * FROM loans", conn)
    conn.close()

    if customers_df.empty:
        print("No data to train on.")
        return

    print("Training segmentation model...")
    train_segmentation_model(customers_df)
    print("Training churn model...")
    train_churn_model(customers_df, transactions_df)
    print("Training credit risk model...")
    train_credit_risk_model(customers_df)
    print("Training loan approval model...")
    train_loan_approval_model(loans_df, customers_df)
    print("Training CLV model...")
    train_clv_model(customers_df)
    print("Training fraud model...")
    train_fraud_model(transactions_df)
    print("Training income model...")
    train_income_model(customers_df)
    print("Training deposit model...")
    train_deposit_model(customers_df)
    print("All models trained successfully!")
