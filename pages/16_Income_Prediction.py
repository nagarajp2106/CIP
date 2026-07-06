"""
Income Prediction Page — Gradient Boosting Regressor.
"""
import streamlit as st
import pandas as pd
from authentication import check_auth, require_role
from database import get_connection
from utils.prediction import load_model, train_income_model, get_feature_importance
from utils.visualization import kpi_card, prediction_result_card, create_scatter, create_horizontal_bar, create_histogram
from config import OCCUPATIONS

# ── Auth ──
user = check_auth()
if not user:
    st.switch_page("app.py")
require_role("Income Prediction")

st.markdown("# 💵 Income Prediction")
st.markdown("Predict annual income using Gradient Boosting Regression")
st.markdown("---")

conn = get_connection()
customers_df = pd.read_sql("SELECT * FROM customers", conn)
conn.close()

if customers_df.empty:
    st.warning("⚠️ No customer data available.")
    st.stop()

model_data = load_model("income")
if model_data is None:
    with st.spinner("🤖 Training income model..."):
        model_data, metrics = train_income_model(customers_df)

model = model_data["model"]
features = model_data["features"]
metrics = model_data.get("metrics", {})
label_encoder = model_data.get("label_encoder")

if metrics:
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(kpi_card("R² Score", f"{metrics.get('r2_score', 0):.3f}", "📐", color="green"), unsafe_allow_html=True)
    with m2:
        st.markdown(kpi_card("RMSE", f"${metrics.get('rmse', 0):,.0f}", "📊", color="blue"), unsafe_allow_html=True)
    with m3:
        st.markdown(kpi_card("MAE", f"${metrics.get('mae', 0):,.0f}", "📈", color="gold"), unsafe_allow_html=True)

st.markdown("---")

# ── Individual Prediction ──
st.markdown("### 🔮 Predict Income")

with st.form("income_form"):
    fc1, fc2 = st.columns(2)
    with fc1:
        age = st.number_input("Age", value=35, min_value=18, max_value=100)
        balance = st.number_input("Account Balance ($)", value=15000.0, min_value=0.0, step=500.0)
    with fc2:
        credit_score = st.number_input("Credit Score", value=700, min_value=300, max_value=850)
        occupation = st.selectbox("Occupation", OCCUPATIONS)

    submitted = st.form_submit_button("💵 Predict Income", type="primary", use_container_width=True)

if submitted:
    # Encode occupation
    occ_enc = 0
    if label_encoder:
        try:
            occ_enc = label_encoder.transform([occupation])[0]
        except ValueError:
            occ_enc = 0

    input_data = pd.DataFrame([{
        "age": age, "balance": balance, "credit_score": credit_score, "occupation_enc": occ_enc
    }])
    input_features = input_data[[f for f in features if f in input_data.columns]]

    predicted_income = max(0, model.predict(input_features)[0])

    st.markdown(f"""
    <div class="prediction-result animate-in">
        <div class="prediction-label">Predicted Annual Income</div>
        <div class="prediction-value" style="color: #28A745;">${predicted_income:,.2f}</div>
        <div class="prediction-score">Based on profile: {occupation}, Age {age}</div>
    </div>
    """, unsafe_allow_html=True)

    importance_df = get_feature_importance(model, features)
    if not importance_df.empty:
        fig = create_horizontal_bar(importance_df, "importance", "feature", "📊 Income Predictors")
        st.plotly_chart(fig, use_container_width=True)

# ── Actual vs Predicted ──
st.markdown("---")
st.markdown("### 📊 Model Performance")

if st.button("📈 Show Actual vs Predicted", use_container_width=True):
    from sklearn.preprocessing import LabelEncoder
    df = customers_df.dropna(subset=["income"])
    df = df[df["income"] > 0].copy()

    le = LabelEncoder()
    df["occupation_enc"] = le.fit_transform(df["occupation"].fillna("Unknown"))

    X = df[[f for f in features if f in df.columns]].fillna(0)
    y_actual = df["income"]
    y_pred = model.predict(X)
    y_pred = [max(0, v) for v in y_pred]

    scatter_df = pd.DataFrame({"actual": y_actual.values, "predicted": y_pred})
    fig = create_scatter(scatter_df, "actual", "predicted", "📊 Actual vs Predicted Income")
    st.plotly_chart(fig, use_container_width=True)

    error_df = pd.DataFrame({"error": y_actual.values - y_pred})
    fig = create_histogram(error_df, "error", "📉 Prediction Error Distribution", nbins=40)
    st.plotly_chart(fig, use_container_width=True)
