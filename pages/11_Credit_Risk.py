"""
Credit Risk Assessment Page — XGBoost classifier for risk scoring.
"""
import streamlit as st
import pandas as pd
from authentication import check_auth, require_role
from database import get_connection
from utils.prediction import load_model, train_credit_risk_model, get_feature_importance
from utils.visualization import kpi_card, prediction_result_card, progress_bar_html, create_horizontal_bar, create_pie_chart

# ── Auth ──
user = check_auth()
if not user:
    st.switch_page("app.py")
require_role("Credit Risk")

st.markdown("# ⚡ Credit Risk Assessment")
st.markdown("AI-powered credit risk scoring using XGBoost")
st.markdown("---")

conn = get_connection()
customers_df = pd.read_sql("SELECT * FROM customers", conn)
conn.close()

if customers_df.empty:
    st.warning("⚠️ No customer data available.")
    st.stop()

# Load or train model
model_data = load_model("credit_risk")
if model_data is None:
    with st.spinner("🤖 Training credit risk model..."):
        model_data, metrics = train_credit_risk_model(customers_df)

model = model_data["model"]
features = model_data["features"]
risk_labels = model_data.get("risk_labels", {0: "Low", 1: "Medium", 2: "High"})
metrics = model_data.get("metrics", {})

# Model metrics
if metrics:
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(kpi_card("Accuracy", f"{metrics.get('accuracy', 0):.1%}", "🎯", color="green"), unsafe_allow_html=True)
    with m2:
        st.markdown(kpi_card("Precision", f"{metrics.get('precision', 0):.1%}", "🔍", color="blue"), unsafe_allow_html=True)
    with m3:
        st.markdown(kpi_card("F1 Score", f"{metrics.get('f1_score', 0):.1%}", "⚡", color="gold"), unsafe_allow_html=True)

st.markdown("---")

tab1, tab2 = st.tabs(["🔮 Risk Assessment", "📊 Portfolio Risk"])

with tab1:
    st.markdown("### Assess Credit Risk")

    selected_id = st.selectbox("Select Customer", customers_df["customer_id"].tolist(),
        format_func=lambda x: f"{x} — {customers_df[customers_df['customer_id']==x]['name'].values[0]}")

    cust = customers_df[customers_df["customer_id"] == selected_id].iloc[0]

    ic1, ic2, ic3 = st.columns(3)
    with ic1:
        age = st.number_input("Age", value=int(cust.get("age", 40)), min_value=18, max_value=100, key="cr_age")
    with ic2:
        income = st.number_input("Income", value=float(cust.get("income", 50000)), key="cr_income")
    with ic3:
        balance = st.number_input("Balance", value=float(cust.get("balance", 10000)), key="cr_balance")

    if st.button("⚡ Assess Risk", type="primary", use_container_width=True):
        input_data = pd.DataFrame([{"age": age, "income": income, "balance": balance}])
        input_features = input_data[[f for f in features if f in input_data.columns]]

        prediction = model.predict(input_features)[0]
        risk_level = risk_labels.get(prediction, "Unknown")

        try:
            probabilities = model.predict_proba(input_features)[0]
        except Exception:
            probabilities = [0.33, 0.33, 0.34]

        # Risk score (0-100)
        risk_score = round(probabilities[2] * 100 if len(probabilities) > 2 else probabilities[-1] * 100, 1) if sum(probabilities) > 0 else 50

        # Display
        risk_css = {"Low": "prediction-low-risk", "Medium": "prediction-medium-risk", "High": "prediction-high-risk"}.get(risk_level, "")
        st.markdown(prediction_result_card("Credit Risk Level", f"{'🟢' if risk_level == 'Low' else '🟡' if risk_level == 'Medium' else '🔴'} {risk_level.upper()} RISK", risk_score / 100, risk_css), unsafe_allow_html=True)

        # Risk score bar
        risk_color = {"Low": "#28A745", "Medium": "#FFC107", "High": "#DC3545"}.get(risk_level, "#6C757D")
        st.markdown(progress_bar_html(risk_score, label="Risk Score", color=risk_color), unsafe_allow_html=True)

        # Recommended action
        actions = {
            "Low": "✅ **Approved** — Customer qualifies for standard products and services.",
            "Medium": "⚠️ **Review Required** — Additional documentation recommended before approval.",
            "High": "🚫 **Decline / Enhanced Due Diligence** — High risk requires management approval.",
        }
        st.info(actions.get(risk_level, "Review required."))

        # Feature importance
        importance_df = get_feature_importance(model, features)
        if not importance_df.empty:
            st.markdown("#### 📊 Risk Factors")
            fig = create_horizontal_bar(importance_df, "importance", "feature", "Feature Importance")
            st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.markdown("### Portfolio Risk Distribution")
    with st.spinner("Analyzing portfolio..."):
        X = customers_df[features].fillna(0)
        predictions = model.predict(X)
        customers_df["risk_prediction"] = [risk_labels.get(p, "Unknown") for p in predictions]

        # Distribution
        risk_dist = customers_df["risk_prediction"].value_counts().reset_index()
        risk_dist.columns = ["risk_level", "count"]
        fig = create_pie_chart(risk_dist, "risk_level", "count", "🎯 Portfolio Risk Distribution", hole=0.4)
        st.plotly_chart(fig, use_container_width=True)

        # High-risk customers
        st.markdown("#### 🔴 High Risk Customers")
        high_risk = customers_df[customers_df["risk_prediction"] == "High"][["customer_id", "name", "income", "balance", "credit_score", "risk_prediction"]].head(20)
        st.dataframe(high_risk, use_container_width=True)
