"""
Data Preprocessing Page — Cleaning, feature engineering, encoding, and scaling.
"""
import streamlit as st
import pandas as pd
from authentication import check_auth, require_role
from database import get_connection
from utils.preprocessing import clean_data, get_data_quality_report
from utils.feature_engineering import (
    apply_all_features, encode_features, scale_features,
    create_age_group, create_income_category, create_balance_category,
    calculate_customer_tenure, calculate_customer_value_score
)

# ── Auth ──
user = check_auth()
if not user:
    st.switch_page("app.py")
require_role("Data Preprocessing")

st.markdown("# 🔧 Data Preprocessing")
st.markdown("Clean, transform, and engineer features from banking data")
st.markdown("---")

# Load data
conn = get_connection()
customers_df = pd.read_sql("SELECT * FROM customers", conn)
transactions_df = pd.read_sql("SELECT * FROM transactions", conn)
conn.close()

if customers_df.empty:
    st.warning("⚠️ No customer data available. Please upload data first.")
    st.stop()

tab1, tab2, tab3, tab4 = st.tabs(["🧹 Auto Clean", "⚙️ Feature Engineering", "🔤 Encoding", "📏 Scaling"])

# ── Tab 1: Auto Cleaning ──
with tab1:
    st.markdown("### Automatic Data Cleaning")
    st.markdown("Handles missing values, duplicates, invalid balances, and data types.")

    st.markdown("#### Current Data Quality")
    quality = get_data_quality_report(customers_df)

    q1, q2, q3, q4 = st.columns(4)
    with q1:
        st.metric("Rows", quality["shape"]["rows"])
    with q2:
        st.metric("Columns", quality["shape"]["columns"])
    with q3:
        st.metric("Duplicates", quality["duplicates"])
    with q4:
        total_missing = sum(v["count"] for v in quality["missing"].values())
        st.metric("Missing Values", total_missing)

    if st.button("🧹 Run Auto-Clean", type="primary", use_container_width=True):
        with st.spinner("Cleaning data..."):
            cleaned_df, report = clean_data(customers_df)

            st.markdown("#### Cleaning Report")
            if report["actions"]:
                for action in report["actions"]:
                    st.info(f"✅ {action}")
            else:
                st.success("✨ Data is already clean — no actions needed!")

            c1, c2 = st.columns(2)
            with c1:
                st.metric("Rows Before", report["original_rows"])
            with c2:
                st.metric("Rows After", report["cleaned_rows"])

            st.markdown("#### Cleaned Data Preview")
            st.dataframe(cleaned_df.head(50), use_container_width=True)

            # Store in session
            st.session_state["preprocessed_df"] = cleaned_df

# ── Tab 2: Feature Engineering ──
with tab2:
    st.markdown("### Feature Engineering")
    st.markdown("Generate derived features from existing data.")

    source_df = st.session_state.get("preprocessed_df", customers_df)

    features = st.multiselect(
        "Select Features to Generate",
        ["Age Group", "Income Category", "Balance Category", "Customer Tenure",
         "Customer Value Score", "All Features"],
        default=["All Features"]
    )

    if st.button("⚙️ Generate Features", type="primary", use_container_width=True):
        with st.spinner("Engineering features..."):
            result_df = source_df.copy()

            if "All Features" in features:
                result_df = apply_all_features(result_df, transactions_df)
            else:
                if "Age Group" in features:
                    result_df = create_age_group(result_df)
                if "Income Category" in features:
                    result_df = create_income_category(result_df)
                if "Balance Category" in features:
                    result_df = create_balance_category(result_df)
                if "Customer Tenure" in features:
                    result_df = calculate_customer_tenure(result_df)
                if "Customer Value Score" in features:
                    result_df = calculate_customer_tenure(result_df)
                    result_df = calculate_customer_value_score(result_df)

            new_cols = [c for c in result_df.columns if c not in source_df.columns]
            st.success(f"✅ Generated {len(new_cols)} new features: {', '.join(new_cols)}")

            st.markdown("#### Preview with New Features")
            st.dataframe(result_df.head(50), use_container_width=True)

            st.session_state["preprocessed_df"] = result_df

# ── Tab 3: Encoding ──
with tab3:
    st.markdown("### Categorical Encoding")

    source_df = st.session_state.get("preprocessed_df", customers_df)
    cat_cols = source_df.select_dtypes(include=['object', 'category']).columns.tolist()

    if not cat_cols:
        st.info("No categorical columns found.")
    else:
        method = st.radio("Encoding Method", ["Label Encoding", "One-Hot Encoding"])
        selected_cols = st.multiselect("Select Columns to Encode", cat_cols, default=cat_cols[:3])

        if selected_cols and st.button("🔤 Apply Encoding", type="primary"):
            with st.spinner("Encoding..."):
                enc_method = "label" if method == "Label Encoding" else "onehot"
                encoded_df, encoders = encode_features(source_df, enc_method, selected_cols)

                st.success(f"✅ {method} applied to {len(selected_cols)} columns")
                st.dataframe(encoded_df.head(50), use_container_width=True)
                st.session_state["preprocessed_df"] = encoded_df

# ── Tab 4: Scaling ──
with tab4:
    st.markdown("### Feature Scaling")

    source_df = st.session_state.get("preprocessed_df", customers_df)
    num_cols = source_df.select_dtypes(include=['float64', 'int64']).columns.tolist()

    if not num_cols:
        st.info("No numeric columns found.")
    else:
        method = st.radio("Scaling Method", ["StandardScaler", "MinMaxScaler"])
        selected_cols = st.multiselect("Select Columns to Scale", num_cols, default=num_cols[:4])

        if selected_cols and st.button("📏 Apply Scaling", type="primary"):
            with st.spinner("Scaling..."):
                sc_method = "standard" if method == "StandardScaler" else "minmax"
                scaled_df, scaler = scale_features(source_df, sc_method, selected_cols)

                st.success(f"✅ {method} applied to {len(selected_cols)} columns")

                before_after = pd.DataFrame({
                    "Column": selected_cols,
                    "Original Mean": [source_df[c].mean() for c in selected_cols],
                    "Original Std": [source_df[c].std() for c in selected_cols],
                    "Scaled Mean": [scaled_df[c].mean() for c in selected_cols],
                    "Scaled Std": [scaled_df[c].std() for c in selected_cols],
                })
                st.dataframe(before_after, use_container_width=True)
                st.session_state["preprocessed_df"] = scaled_df
