"""
Deposit Subscription Prediction Page — Random Forest Classifier.
"""
import streamlit as st
from utils.icons import render_html_icon, get_symbol_name
import pandas as pd
import plotly.express as px
from authentication import check_auth, require_role
from database import get_connection
from utils.prediction import load_model, train_deposit_model, get_feature_importance
from utils.visualization import kpi_card, prediction_result_card, progress_bar_html, create_horizontal_bar, create_pie_chart, apply_layout

# ── Auth ──
user = check_auth()
if not user:
    st.switch_page("app.py")
require_role("Deposit Prediction")

st.markdown(f"""<h1 style="display: flex; align-items: center; gap: 10px; margin-top: 0; color: var(--primary); font-weight: 700; font-size: 2.2rem; line-height: 1.2;">
{render_html_icon('savings', size='36px', color='var(--primary)')}
<span>Deposit Subscription Prediction</span>
</h1>""", unsafe_allow_html=True)
st.markdown("Predict whether a customer will subscribe to a term deposit")
st.markdown("---")

conn = get_connection()
customers_df = pd.read_sql("SELECT * FROM customers", conn)
conn.close()

if customers_df.empty:
    st.warning("No customer data available.", icon=":material/warning:")
    st.stop()

model_data = load_model("deposit")
if model_data is None:
    with st.spinner("Training deposit model..."):
        model_data, metrics = train_deposit_model(customers_df)

model = model_data["model"]
features = model_data["features"]
metrics = model_data.get("metrics", {})

# Model Performance Cards (Standardized)
if metrics:
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(kpi_card("Accuracy", f"{metrics.get('accuracy', 0):.1%}", "track_changes", color="blue"), unsafe_allow_html=True)
    with m2:
        st.markdown(kpi_card("Precision", f"{metrics.get('precision', 0):.1%}", "insights", color="blue"), unsafe_allow_html=True)
    with m3:
        st.markdown(kpi_card("Recall", f"{metrics.get('recall', 0):.1%}", "history", color="blue"), unsafe_allow_html=True)
    with m4:
        st.markdown(kpi_card("F1 Score", f"{metrics.get('f1_score', 0):.1%}", "analytics", color="blue"), unsafe_allow_html=True)

st.markdown("---")

tab1, tab2 = st.tabs([":material/change_circle: Individual Prediction", ":material/campaign: Campaign Targeting"])

with tab1:
    st.markdown("### Predict Deposit Subscription")

    selected_id = st.selectbox(
        "Select Customer", 
        customers_df["customer_id"].tolist(),
        format_func=lambda x: f"{x} — {customers_df[customers_df['customer_id']==x]['name'].values[0]}"
    )

    cust = customers_df[customers_df["customer_id"] == selected_id].iloc[0]

    ic1, ic2 = st.columns(2)
    with ic1:
        age = st.number_input("Age", min_value=18, max_value=120, value=int(cust.get("age", 40)), step=1, key="dp_age")
        income = st.number_input("Income ($)", min_value=0.0, value=float(cust.get("income", 50000)), step=1000.0, key="dp_income")
    with ic2:
        balance = st.number_input("Balance ($)", min_value=-10000.0, value=float(cust.get("balance", 10000)), step=500.0, key="dp_balance")
        credit_score = st.number_input("Credit Score", min_value=300, max_value=850, value=int(cust.get("credit_score", 700)), step=1, key="dp_cs")

    if st.button("Predict Subscription", icon=":material/savings:", type="primary", use_container_width=True):
        input_data = pd.DataFrame([{"age": age, "income": income, "balance": balance, "credit_score": credit_score}])
        input_features = input_data[[f for f in features if f in input_data.columns]]

        prediction = model.predict(input_features)[0]
        probability = model.predict_proba(input_features)[0]

        yes_prob = probability[1] if len(probability) > 1 else probability[0]

        # Determine the badge styling and icon color
        if prediction == 1:
            badge_html = f"""<div class="prediction-badge approved">
{render_html_icon("check_circle", size="20px", color="var(--success)")}
<span>YES — Likely to Subscribe</span>
</div>"""
            prob_color = "var(--success)" if yes_prob >= 0.70 else "var(--warning)"
        else:
            badge_html = f"""<div class="prediction-badge rejected">
{render_html_icon("cancel", size="20px", color="var(--danger)")}
<span>NO — Unlikely to Subscribe</span>
</div>"""
            prob_color = "var(--danger)" if yes_prob < 0.30 else "var(--warning)"

        # Render the unified prediction card
        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
        st.markdown(f"""<div class="prediction-result-card animate-in">
<div class="prediction-result-header">
<span class="prediction-result-title">Prediction Result</span>
<span class="prediction-result-confidence">Confidence: {yes_prob:.1%}</span>
</div>
<div class="prediction-result-badge-row">
{badge_html}
</div>
<div style="height: 6px;"></div>
{progress_bar_html(yes_prob * 100, label="Subscription Probability", color=prob_color)}
</div>""", unsafe_allow_html=True)

        # Spacing
        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

        importance_df = get_feature_importance(model, features)
        if not importance_df.empty:
            # Map features to human-readable names
            feature_map = {
                "balance": "Balance",
                "income": "Income",
                "credit_score": "Credit Score",
                "age": "Age"
            }
            importance_df["feature"] = importance_df["feature"].map(lambda x: feature_map.get(x, x.title()))
            
            fig = px.bar(
                importance_df, 
                x="importance", 
                y="feature", 
                orientation="h",
                color_discrete_sequence=["#2E86AB"],
                text="importance"
            )
            fig.update_traces(
                texttemplate='%{text:.2f}', 
                textposition='outside',
                marker=dict(cornerradius=4)
            )
            fig.update_layout(
                xaxis_title="Feature Importance",
                yaxis_title="",
                yaxis=dict(categoryorder="total ascending"),
                bargap=0.35
            )
            fig = apply_layout(fig, "Key Factors", height=320)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with tab2:
    st.markdown("### Campaign Targeting — Find Likely Subscribers")

    if st.button("Identify Target Customers", icon=":material/campaign:", type="primary", use_container_width=True):
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

            # Aligned Target Summary Cards (Likely=Green, Unlikely=Blue, Conv Rate=Blue)
            s1, s2, s3 = st.columns(3)
            with s1:
                st.markdown(kpi_card("Likely Subscribers", f"{yes_count:,}", "check_circle", color="green"), unsafe_allow_html=True)
            with s2:
                st.markdown(kpi_card("Unlikely", f"{no_count:,}", "cancel", color="blue"), unsafe_allow_html=True)
            with s3:
                conv_rate = round(yes_count / max(len(predictions), 1) * 100, 1)
                st.markdown(kpi_card("Conversion Rate", f"{conv_rate}%", "trending_up", color="blue"), unsafe_allow_html=True)

            # Subscription Donut Chart with strict green/red mapping
            dist = result_df["will_subscribe"].value_counts().reset_index()
            dist.columns = ["response", "count"]
            color_map = {"Yes": "#2E7D32", "No": "#C62828"} # Green and Red
            fig = create_pie_chart(dist, "response", "count", "Subscription Prediction Distribution", hole=0.4, color_discrete_map=color_map)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

            # Custom HTML targets table
            st.markdown(f"#### {render_html_icon('campaign', size='20px')} Top Campaign Targets", unsafe_allow_html=True)
            
            targets_df = result_df[result_df["will_subscribe"] == "Yes"].head(30)
            
            def render_targets_table(df: pd.DataFrame) -> str:
                html = """<table style="width: 100%; border-collapse: collapse; margin-top: 1rem; border-radius: 8px; overflow: hidden; font-size: 0.9rem;">
<thead>
<tr style="background-color: var(--primary); color: white; text-align: left; font-weight: 600;">
<th style="padding: 12px;">Customer ID</th>
<th style="padding: 12px;">Name</th>
<th style="padding: 12px;">Age</th>
<th style="padding: 12px;">Income</th>
<th style="padding: 12px;">Balance</th>
<th style="padding: 12px;">Will Subscribe</th>
<th style="padding: 12px;">Probability</th>
</tr>
</thead>
<tbody>"""
                for idx, row in df.reset_index(drop=True).iterrows():
                    # Zebra striping
                    row_bg = "var(--card-bg)" if idx % 2 == 0 else "var(--bg-light)"
                    
                    # Will Subscribe badge
                    badge_html = '<span class="status-pill success" style="padding: 2px 8px; font-size: 0.78rem;">Yes</span>'
                    
                    # Probability progress bar style
                    prob = row["probability"]
                    bar_color = "var(--success)" if prob >= 75 else "var(--secondary)" if prob >= 50 else "var(--warning)"
                    progress_html = f"""<div style="display: flex; align-items: center; gap: 8px; width: 100%;">
<div style="flex-grow: 1; background: #E2E8F0; border-radius: 4px; height: 6px; overflow: hidden;">
<div style="background: {bar_color}; width: {prob}%; height: 100%;"></div>
</div>
<span style="font-weight: 600; width: 45px; text-align: right;">{prob:.1f}%</span>
</div>"""
                    
                    html += f"""<tr style="background-color: {row_bg}; border-bottom: 1px solid var(--border-color); color: var(--text-main);">
<td style="padding: 12px; font-weight: 600;">{row['customer_id']}</td>
<td style="padding: 12px;">{row['name']}</td>
<td style="padding: 12px;">{row['age']}</td>
<td style="padding: 12px;">${row['income']:,.0f}</td>
<td style="padding: 12px;">${row['balance']:,.0f}</td>
<td style="padding: 12px;">{badge_html}</td>
<td style="padding: 12px; min-width: 140px;">{progress_html}</td>
</tr>"""
                html += "</tbody></table>"
                return html

            st.markdown(render_targets_table(targets_df), unsafe_allow_html=True)
            
            st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

            csv = result_df.to_csv(index=False)
            st.download_button("Download Target List", csv, "deposit_targets.csv", "text/csv", icon=":material/download:", use_container_width=True)