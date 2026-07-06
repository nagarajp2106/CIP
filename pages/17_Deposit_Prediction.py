"""
Deposit Subscription Prediction Page — Random Forest Classifier.
"""
import streamlit as st
import pandas as pd
from authentication import check_auth, require_role
from database import get_connection
from utils.prediction import load_model, train_deposit_model, get_feature_importance
from utils.visualization import kpi_card, prediction_result_card, progress_bar_html, create_horizontal_bar, create_pie_chart

# ── Auth ──
user = check_auth()
if not user:
    st.switch_page("app.py")
require_role("Deposit Prediction")

st.markdown("# 🏦 Deposit Subscription Prediction")
st.markdown("Predict whether a customer will subscribe to a term deposit")
st.markdown("---")

conn = get_connection()
customers_df = pd.read_sql("SELECT * FROM customers", conn)
conn.close()

if customers_df.empty:
    st.warning("⚠️ No customer data available.")
    st.stop()

model_data = load_model("deposit")
if model_data is None:
    with st.spinner("🤖 Training deposit model..."):
        model_data, metrics = train_deposit_model(customers_df)

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

tab1, tab2 = st.tabs(["🔮 Individual Prediction", "📊 Campaign Targeting"])

with tab1:
    st.markdown("### Predict Deposit Subscription")

    selected_id = st.selectbox("Select Customer", customers_df["customer_id"].tolist(),
        format_func=lambda x: f"{x} — {customers_df[customers_df['customer_id']==x]['name'].values[0]}")

    cust = customers_df[customers_df["customer_id"] == selected_id].iloc[0]

    ic1, ic2 = st.columns(2)
    with ic1:
        age = st.number_input("Age", value=int(cust.get("age", 40)), key="dp_age")
        income = st.number_input("Income", value=float(cust.get("income", 50000)), key="dp_income")
    with ic2:
        balance = st.number_input("Balance", value=float(cust.get("balance", 10000)), key="dp_balance")
        credit_score = st.number_input("Credit Score", value=int(cust.get("credit_score", 700)), key="dp_cs")

    if st.button("🔮 Predict", type="primary", use_container_width=True):
        input_data = pd.DataFrame([{"age": age, "income": income, "balance": balance, "credit_score": credit_score}])
        input_features = input_data[[f for f in features if f in input_data.columns]]

        prediction = model.predict(input_features)[0]
        probability = model.predict_proba(input_features)[0]

        yes_prob = probability[1] if len(probability) > 1 else probability[0]

        if prediction == 1:
            st.markdown(prediction_result_card("Deposit Subscription", "✅ YES — Likely to Subscribe", yes_prob, "prediction-approved"), unsafe_allow_html=True)
        else:
            st.markdown(prediction_result_card("Deposit Subscription", "❌ NO — Unlikely to Subscribe", 1 - yes_prob, "prediction-rejected"), unsafe_allow_html=True)

        st.markdown(progress_bar_html(yes_prob * 100, label="Subscription Probability", color="#28A745" if prediction == 1 else "#DC3545"), unsafe_allow_html=True)

        importance_df = get_feature_importance(model, features)
        if not importance_df.empty:
            fig = create_horizontal_bar(importance_df, "importance", "feature", "📊 Key Factors")
            st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.markdown("### Campaign Targeting — Find Likely Subscribers")

    if st.button("🚀 Identify Target Customers", type="primary", use_container_width=True):
        with st.spinner("Analyzing all customers..."):
            X = customers_df[features].fillna(0)
            predictions = model.predict(X)
            probabilities = model.predict_proba(X)

            result_df = customers_df[["customer_id", "name", "income", "balance", "age"]].copy()
            result_df["will_subscribe"] = ["Yes" if p == 1 else "No" for p in predictions]
            result_df["probability"] = [round(prob[1] * 100, 1) if len(prob) > 1 else 0 for prob in probabilities]
            result_df = result_df.sort_values("probability", ascending=False)

            yes_count = (predictions == 1).sum()
            no_count = (predictions == 0).sum()

            s1, s2, s3 = st.columns(3)
            with s1:
                st.markdown(kpi_card("Likely Subscribers", f"{yes_count:,}", "✅", color="green"), unsafe_allow_html=True)
            with s2:
                st.markdown(kpi_card("Unlikely", f"{no_count:,}", "❌", color="red"), unsafe_allow_html=True)
            with s3:
                conv_rate = round(yes_count / max(len(predictions), 1) * 100, 1)
                st.markdown(kpi_card("Conversion Rate", f"{conv_rate}%", "📊", color="gold"), unsafe_allow_html=True)

            dist = result_df["will_subscribe"].value_counts().reset_index()
            dist.columns = ["response", "count"]
            fig = create_pie_chart(dist, "response", "count", "📊 Subscription Prediction Distribution", hole=0.4)
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("#### 🎯 Top Campaign Targets")
            st.dataframe(result_df[result_df["will_subscribe"] == "Yes"].head(30), use_container_width=True)

            csv = result_df.to_csv(index=False)
            st.download_button("📥 Download Target List", csv, "deposit_targets.csv", "text/csv")
