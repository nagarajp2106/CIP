"""
Churn Prediction Page — Random Forest classifier for customer retention.
"""
import streamlit as st
from utils.icons import render_html_icon, get_symbol_name
import pandas as pd
import numpy as np
from authentication import check_auth, require_role
from database import get_connection
from utils.prediction import load_model, train_churn_model, get_feature_importance
from utils.visualization import kpi_card, prediction_result_card, progress_bar_html, create_horizontal_bar

# ── Auth ──
user = check_auth()
if not user:
    st.switch_page("app.py")
require_role("Churn Prediction")

st.markdown(f"# {render_html_icon('change_circle', size='30px')} Customer Churn Prediction", unsafe_allow_html=True)
st.markdown("Predict which customers are likely to leave using Random Forest")
st.markdown("---")

conn = get_connection()
customers_df = pd.read_sql("SELECT * FROM customers", conn)
conn.close()

if customers_df.empty:
    st.warning("No customer data available.", icon=":material/warning:")
    st.stop()

# Load or train model
model_data = load_model("churn")
if model_data is None:
    with st.spinner("Training churn model..."):
        model_data, metrics = train_churn_model(customers_df)

if model_data is None:
    st.error("Failed to train churn model.", icon=":material/cancel:")
    st.stop()

model = model_data["model"]
features = model_data["features"]
metrics = model_data.get("metrics", {})

# Show model metrics
if metrics:
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(kpi_card("Accuracy", f"{metrics.get('accuracy', 0):.1%}", "track_changes", color="green"), unsafe_allow_html=True)
    with m2:
        st.markdown(kpi_card("Precision", f"{metrics.get('precision', 0):.1%}", "search", color="blue"), unsafe_allow_html=True)
    with m3:
        st.markdown(kpi_card("Recall", f"{metrics.get('recall', 0):.1%}", "", color="gold"), unsafe_allow_html=True)
    with m4:
        st.markdown(kpi_card("F1 Score", f"{metrics.get('f1_score', 0):.1%}", "bolt", color="teal"), unsafe_allow_html=True)

st.markdown("---")

tab1, tab2 = st.tabs([":material/change_circle: Individual Prediction", ":material/dataset: Batch Prediction"])

with tab1:
    st.markdown("### Predict Churn for a Customer")

    # Customer selector
    cust_options = customers_df["customer_id"].tolist()
    selected_id = st.selectbox("Select Customer", cust_options,
                                format_func=lambda x: f"{x} — {customers_df[customers_df['customer_id']==x]['name'].values[0]}")

    cust = customers_df[customers_df["customer_id"] == selected_id].iloc[0]

    # Manual input option
    st.markdown("#### Or Enter Custom Values")
    ic1, ic2 = st.columns(2)
    with ic1:
        age = st.number_input("Age", value=int(cust.get("age", 40)), min_value=18, max_value=100)
        income = st.number_input("Income", value=float(cust.get("income", 50000)))
    with ic2:
        balance = st.number_input("Balance", value=float(cust.get("balance", 10000)))
        credit_score = st.number_input("Credit Score", value=int(cust.get("credit_score", 700)), min_value=300, max_value=850)

    if st.button("Predict Churn", icon=":material/change_circle:", type="primary", use_container_width=True):
        input_data = pd.DataFrame([{
            "age": age, "income": income, "balance": balance, "credit_score": credit_score
        }])
        # Only use available features
        input_features = input_data[[f for f in features if f in input_data.columns]]

        prediction = model.predict(input_features)[0]
        probability = model.predict_proba(input_features)[0]

        churn_prob = probability[1] if len(probability) > 1 else probability[0]
        stay_prob = probability[0] if len(probability) > 1 else 1 - probability[0]

        # Result card
        if prediction == 0:
            st.markdown(prediction_result_card("Churn Prediction", "STAY", stay_prob, "prediction-approved"), unsafe_allow_html=True)
        else:
            st.markdown(prediction_result_card("Churn Prediction", "LIKELY TO LEAVE", churn_prob, "prediction-rejected"), unsafe_allow_html=True)

        # Probability bars
        r1, r2 = st.columns(2)
        with r1:
            st.markdown(progress_bar_html(stay_prob * 100, label="Stay Probability", color="#28A745"), unsafe_allow_html=True)
        with r2:
            st.markdown(progress_bar_html(churn_prob * 100, label="Churn Probability", color="#DC3545"), unsafe_allow_html=True)

        # Feature importance
        importance_df = get_feature_importance(model, features)
        if not importance_df.empty:
            st.markdown(f"#### {render_html_icon('analytics', size='20px')} Key Factors", unsafe_allow_html=True)
            fig = create_horizontal_bar(importance_df.head(10), "importance", "feature", "Feature Importance")
            st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.markdown("### Batch Churn Prediction")
    st.markdown("Run churn prediction on all customers")

    if st.button("Run Batch Prediction", icon=":material/bolt:", type="primary", use_container_width=True):
        with st.spinner("Predicting churn for all customers..."):
            X = customers_df[features].fillna(0)
            predictions = model.predict(X)
            probabilities = model.predict_proba(X)

            result_df = customers_df[["customer_id", "name", "income", "balance", "credit_score"]].copy()
            result_df["churn_prediction"] = ["Churn" if p == 1 else "Stay" for p in predictions]
            result_df["churn_probability"] = [round(prob[1] * 100, 1) if len(prob) > 1 else 0 for prob in probabilities]

            # Sort by churn probability
            result_df = result_df.sort_values("churn_probability", ascending=False)

            # Summary
            churn_count = (predictions == 1).sum()
            stay_count = (predictions == 0).sum()

            s1, s2, s3 = st.columns(3)
            with s1:
                st.markdown(kpi_card("At Risk", f"{churn_count:,}", "", color="red"), unsafe_allow_html=True)
            with s2:
                st.markdown(kpi_card("Stable", f"{stay_count:,}", "", color="green"), unsafe_allow_html=True)
            with s3:
                churn_pct = round(churn_count / max(len(predictions), 1) * 100, 1)
                st.markdown(kpi_card("Churn Rate", f"{churn_pct}%", "", color="gold"), unsafe_allow_html=True)

            st.markdown("#### High-Risk Customers")
            high_risk = result_df[result_df["churn_prediction"] == "Churn"].head(20)
            st.dataframe(high_risk, use_container_width=True)

            # Download
            csv = result_df.to_csv(index=False)
            st.download_button("Download Results", csv, "churn_predictions.csv", "text/csv", icon=":material/download:")