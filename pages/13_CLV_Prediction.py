"""
Customer Lifetime Value Prediction Page — Gradient Boosting Regressor.
"""
import streamlit as st
import pandas as pd
from authentication import check_auth, require_role
from database import get_connection
from utils.prediction import load_model, train_clv_model, get_feature_importance
from utils.visualization import kpi_card, prediction_result_card, create_histogram, create_horizontal_bar

# ── Auth ──
user = check_auth()
if not user:
    st.switch_page("app.py")
require_role("CLV Prediction")

st.markdown("# 💎 Customer Lifetime Value Prediction")
st.markdown("Estimate the lifetime value of each customer using regression")
st.markdown("---")

conn = get_connection()
customers_df = pd.read_sql("SELECT * FROM customers", conn)
conn.close()

if customers_df.empty:
    st.warning("⚠️ No customer data available.")
    st.stop()

model_data = load_model("clv")
if model_data is None:
    with st.spinner("🤖 Training CLV model..."):
        model_data, metrics = train_clv_model(customers_df)

model = model_data["model"]
features = model_data["features"]
metrics = model_data.get("metrics", {})

if metrics:
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(kpi_card("R² Score", f"{metrics.get('r2_score', 0):.3f}", "📐", color="green"), unsafe_allow_html=True)
    with m2:
        st.markdown(kpi_card("RMSE", f"${metrics.get('rmse', 0):,.0f}", "📊", color="blue"), unsafe_allow_html=True)
    with m3:
        st.markdown(kpi_card("MAE", f"${metrics.get('mae', 0):,.0f}", "📈", color="gold"), unsafe_allow_html=True)

st.markdown("---")

tab1, tab2 = st.tabs(["🔮 Individual Prediction", "📊 Portfolio CLV"])

with tab1:
    st.markdown("### Predict CLV for a Customer")
    selected_id = st.selectbox("Select Customer", customers_df["customer_id"].tolist(),
        format_func=lambda x: f"{x} — {customers_df[customers_df['customer_id']==x]['name'].values[0]}")

    cust = customers_df[customers_df["customer_id"] == selected_id].iloc[0]

    ic1, ic2 = st.columns(2)
    with ic1:
        income = st.number_input("Income", value=float(cust.get("income", 50000)), key="clv_income")
        balance = st.number_input("Balance", value=float(cust.get("balance", 10000)), key="clv_balance")
    with ic2:
        credit_score = st.number_input("Credit Score", value=int(cust.get("credit_score", 700)), key="clv_cs")
        age = st.number_input("Age", value=int(cust.get("age", 40)), key="clv_age")

    if st.button("💎 Predict CLV", type="primary", use_container_width=True):
        input_data = pd.DataFrame([{"income": income, "balance": balance, "credit_score": credit_score, "age": age}])
        input_features = input_data[[f for f in features if f in input_data.columns]]

        clv = model.predict(input_features)[0]
        clv = max(0, clv)

        # Category
        if clv > 100000:
            category = "🏆 Platinum"
        elif clv > 50000:
            category = "🥇 Gold"
        elif clv > 20000:
            category = "🥈 Silver"
        else:
            category = "🥉 Bronze"

        st.markdown(f"""
        <div class="prediction-result animate-in">
            <div class="prediction-label">Estimated Customer Lifetime Value</div>
            <div class="prediction-value" style="color: #D4AF37;">${clv:,.2f}</div>
            <div class="prediction-score" style="font-size: 1.3rem;">{category}</div>
        </div>
        """, unsafe_allow_html=True)

        importance_df = get_feature_importance(model, features)
        if not importance_df.empty:
            fig = create_horizontal_bar(importance_df, "importance", "feature", "📊 CLV Drivers")
            st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.markdown("### Portfolio CLV Analysis")

    if st.button("🚀 Calculate CLV for All Customers", type="primary", use_container_width=True):
        with st.spinner("Calculating..."):
            X = customers_df[features].fillna(0)
            clv_predictions = model.predict(X)
            clv_predictions = [max(0, v) for v in clv_predictions]

            result_df = customers_df[["customer_id", "name", "income", "balance"]].copy()
            result_df["estimated_clv"] = clv_predictions
            result_df["category"] = pd.cut(result_df["estimated_clv"],
                bins=[-1, 20000, 50000, 100000, float('inf')],
                labels=["Bronze", "Silver", "Gold", "Platinum"])
            result_df = result_df.sort_values("estimated_clv", ascending=False)

            # Summary
            s1, s2, s3 = st.columns(3)
            with s1:
                st.markdown(kpi_card("Avg CLV", f"${result_df['estimated_clv'].mean():,.0f}", "💰", color="gold"), unsafe_allow_html=True)
            with s2:
                st.markdown(kpi_card("Total CLV", f"${result_df['estimated_clv'].sum():,.0f}", "💎", color="purple"), unsafe_allow_html=True)
            with s3:
                st.markdown(kpi_card("Median CLV", f"${result_df['estimated_clv'].median():,.0f}", "📊", color="blue"), unsafe_allow_html=True)

            fig = create_histogram(result_df, "estimated_clv", "💎 CLV Distribution", nbins=50)
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("#### 🏆 Top 20 Highest CLV Customers")
            st.dataframe(result_df.head(20), use_container_width=True)

            csv = result_df.to_csv(index=False)
            st.download_button("📥 Download CLV Report", csv, "clv_predictions.csv", "text/csv")
