"""
Loan Approval Prediction Page — Random Forest classifier.
"""
import streamlit as st
import pandas as pd
from authentication import check_auth, require_role
from database import get_connection
from utils.prediction import load_model, train_loan_approval_model, get_feature_importance
from utils.visualization import kpi_card, prediction_result_card, progress_bar_html, create_horizontal_bar

# ── Auth ──
user = check_auth()
if not user:
    st.switch_page("app.py")
require_role("Loan Approval")

st.markdown("# 🏦 Loan Approval Prediction")
st.markdown("AI-powered loan approval decision support")
st.markdown("---")

conn = get_connection()
customers_df = pd.read_sql("SELECT * FROM customers", conn)
loans_df = pd.read_sql("SELECT * FROM loans", conn)
conn.close()

if customers_df.empty or loans_df.empty:
    st.warning("⚠️ Insufficient data for loan approval prediction.")
    st.stop()

# Load or train
model_data = load_model("loan_approval")
if model_data is None:
    with st.spinner("🤖 Training loan approval model..."):
        model_data, metrics = train_loan_approval_model(loans_df, customers_df)

model = model_data["model"]
features = model_data["features"]
metrics = model_data.get("metrics", {})

if metrics:
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(kpi_card("Accuracy", f"{metrics.get('accuracy', 0):.1%}", "🎯", color="green"), unsafe_allow_html=True)
    with m2:
        st.markdown(kpi_card("Precision", f"{metrics.get('precision', 0):.1%}", "🔍", color="blue"), unsafe_allow_html=True)
    with m3:
        st.markdown(kpi_card("Recall", f"{metrics.get('recall', 0):.1%}", "📊", color="gold"), unsafe_allow_html=True)
    with m4:
        st.markdown(kpi_card("F1 Score", f"{metrics.get('f1_score', 0):.1%}", "⚡", color="teal"), unsafe_allow_html=True)

st.markdown("---")
st.markdown("### 📝 Loan Application")

with st.form("loan_form"):
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        income = st.number_input("Annual Income ($)", value=60000.0, min_value=0.0, step=1000.0)
        credit_score = st.number_input("Credit Score", value=700, min_value=300, max_value=850)
    with fc2:
        loan_amount = st.number_input("Loan Amount ($)", value=50000.0, min_value=1000.0, step=1000.0)
        interest_rate = st.number_input("Interest Rate (%)", value=8.5, min_value=0.0, max_value=30.0, step=0.5)
    with fc3:
        age = st.number_input("Age", value=35, min_value=18, max_value=100)
        balance = st.number_input("Current Balance ($)", value=15000.0, min_value=0.0, step=500.0)

    submitted = st.form_submit_button("🔮 Predict Approval", type="primary", use_container_width=True)

if submitted:
    input_dict = {"income": income, "credit_score": credit_score, "loan_amount": loan_amount,
                  "interest_rate": interest_rate, "age": age, "balance": balance}
    input_data = pd.DataFrame([input_dict])
    input_features = input_data[[f for f in features if f in input_data.columns]]

    prediction = model.predict(input_features)[0]
    probability = model.predict_proba(input_features)[0]

    approval_prob = probability[1] if len(probability) > 1 else probability[0]

    if prediction == 1:
        st.markdown(prediction_result_card("Loan Decision", "✅ APPROVED", approval_prob, "prediction-approved"), unsafe_allow_html=True)
    else:
        st.markdown(prediction_result_card("Loan Decision", "❌ REJECTED", 1 - approval_prob, "prediction-rejected"), unsafe_allow_html=True)

    st.markdown(progress_bar_html(approval_prob * 100, label="Approval Probability", color="#28A745" if prediction == 1 else "#DC3545"), unsafe_allow_html=True)

    # Key factors
    importance_df = get_feature_importance(model, features)
    if not importance_df.empty:
        st.markdown("#### 📊 Key Decision Factors")
        fig = create_horizontal_bar(importance_df, "importance", "feature", "Feature Importance")
        st.plotly_chart(fig, use_container_width=True)

    # Decision explanation
    st.markdown("#### 📝 Decision Explanation")
    if prediction == 1:
        factors = []
        if credit_score >= 700:
            factors.append("✅ Good credit score")
        if income > loan_amount * 0.3:
            factors.append("✅ Healthy income-to-loan ratio")
        if balance > 5000:
            factors.append("✅ Sufficient account balance")
        for f in factors:
            st.markdown(f)
    else:
        factors = []
        if credit_score < 650:
            factors.append("⚠️ Low credit score — consider improving credit history")
        if income < loan_amount * 0.2:
            factors.append("⚠️ High loan-to-income ratio")
        if balance < 2000:
            factors.append("⚠️ Low account balance")
        for f in factors:
            st.markdown(f)
