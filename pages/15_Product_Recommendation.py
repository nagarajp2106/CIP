"""
Product Recommendation Page — Rule-based + similarity scoring.
"""
import streamlit as st
import pandas as pd
import numpy as np
from authentication import check_auth, require_role
from database import get_connection
from utils.visualization import kpi_card, progress_bar_html
from config import PRODUCT_LIST
from utils.icons import render_html_icon, get_symbol_name

# ── Auth ──
user = check_auth()
if not user:
    st.switch_page("app.py")
require_role("Product Recommendation")

st.markdown(f"# {render_html_icon('recommend', size='30px')} Product Recommendation", unsafe_allow_html=True)
st.markdown("AI-powered product recommendations based on customer profiles")
st.markdown("---")

conn = get_connection()
customers_df = pd.read_sql("SELECT * FROM customers", conn)
accounts_df = pd.read_sql("SELECT customer_id, account_type FROM accounts", conn)
loans_df = pd.read_sql("SELECT customer_id, loan_type FROM loans", conn)
cards_df = pd.read_sql("SELECT customer_id, card_type FROM cards", conn)
conn.close()

if customers_df.empty:
    st.warning("No customer data available.", icon=":material/warning:")
    st.stop()


def generate_recommendations(customer: pd.Series) -> list[dict]:
    """Generate product recommendations based on customer profile."""
    recommendations = []
    age = customer.get("age", 35)
    income = customer.get("income", 40000)
    balance = customer.get("balance", 5000)
    credit_score = customer.get("credit_score", 650)
    cid = customer.get("customer_id", "")

    # Get existing products
    existing_accounts = accounts_df[accounts_df["customer_id"] == cid]["account_type"].tolist()
    existing_loans = loans_df[loans_df["customer_id"] == cid]["loan_type"].tolist()
    has_credit_card = len(cards_df[(cards_df["customer_id"] == cid) & (cards_df["card_type"] == "Credit")]) > 0

    # Savings Account
    if "Savings" not in existing_accounts:
        score = min(85 + (balance / 10000) * 5, 98)
        recommendations.append({
            "product": "Savings Account", "score": round(score, 1), "icon": "savings",
            "reason": "Every customer benefits from a high-yield savings account."
        })

    # Current Account
    if "Current" not in existing_accounts and income > 50000:
        score = min(60 + (income / 100000) * 25, 95)
        recommendations.append({
            "product": "Current Account", "score": round(score, 1), "icon": "credit_card",
            "reason": f"High income (${income:,.0f}) makes a current account beneficial for business transactions."
        })

    # Credit Card
    if not has_credit_card and credit_score >= 650:
        score = min(50 + (credit_score - 650) * 0.2 + (income / 100000) * 15, 95)
        recommendations.append({
            "product": "Credit Card", "score": round(score, 1), "icon": "credit_card",
            "reason": f"Credit score of {credit_score} qualifies for premium credit card products."
        })

    # Home Loan
    if "Home Loan" not in existing_loans and age >= 25 and income >= 40000 and credit_score >= 650:
        score = min(40 + (income / 150000) * 30 + (credit_score - 650) * 0.1, 90)
        recommendations.append({
            "product": "Home Loan", "score": round(score, 1), "icon": "home",
            "reason": f"Age {age} with stable income is ideal for home ownership financing."
        })

    # Personal Loan
    if "Personal Loan" not in existing_loans and credit_score >= 600:
        score = min(45 + (credit_score - 600) * 0.15, 85)
        recommendations.append({
            "product": "Personal Loan", "score": round(score, 1), "icon": "account_balance",
            "reason": "Flexible personal loan for various financial needs."
        })

    # Fixed Deposit
    if "Fixed Deposit" not in existing_accounts and balance > 10000:
        score = min(55 + (balance / 100000) * 30, 95)
        recommendations.append({
            "product": "Fixed Deposit", "score": round(score, 1), "icon": "savings",
            "reason": f"High balance (${balance:,.0f}) would earn better returns in a fixed deposit."
        })

    # Insurance
    if age >= 30:
        score = min(50 + (age - 30) * 0.8 + (income / 100000) * 10, 90)
        recommendations.append({
            "product": "Insurance", "score": round(score, 1), "icon": "shield",
            "reason": "Life and health insurance for financial security."
        })

    # Investment Plan
    if income > 60000 and age >= 25:
        score = min(40 + (income / 200000) * 35 + (balance / 100000) * 15, 92)
        recommendations.append({
            "product": "Investment Plan", "score": round(score, 1), "icon": "trending_up",
            "reason": f"Income of ${income:,.0f} with balance of ${balance:,.0f} is suitable for wealth building."
        })

    # Sort by score
    recommendations.sort(key=lambda x: x["score"], reverse=True)
    return recommendations


# ── Customer Selection ──
selected_id = st.selectbox("Select Customer", customers_df["customer_id"].tolist(),
    format_func=lambda x: f"{x} — {customers_df[customers_df['customer_id']==x]['name'].values[0]}")

cust = customers_df[customers_df["customer_id"] == selected_id].iloc[0]

# Customer profile summary
p1, p2, p3, p4 = st.columns(4)
with p1:
    st.markdown(kpi_card("Income", f"${cust['income']:,.0f}", "", color="green"), unsafe_allow_html=True)
with p2:
    st.markdown(kpi_card("Balance", f"${cust['balance']:,.2f}", "", color="blue"), unsafe_allow_html=True)
with p3:
    st.markdown(kpi_card("Credit Score", f"{cust['credit_score']}", "", color="gold"), unsafe_allow_html=True)
with p4:
    st.markdown(kpi_card("Age", f"{cust['age']}", "", color="teal"), unsafe_allow_html=True)

st.markdown("---")

# Generate recommendations
recommendations = generate_recommendations(cust)

if recommendations:
    st.markdown(f"### {render_html_icon('track_changes', size='22px')} Top {len(recommendations)} Recommended Products", unsafe_allow_html=True)

    for rec in recommendations:
        color = "#28A745" if rec["score"] >= 80 else "#FFC107" if rec["score"] >= 60 else "#6C757D"
        st.markdown(f"""
        <div class="insight-card" style="border-left-color: {color};">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="margin-right: 0.75rem; vertical-align: middle;">{render_html_icon(rec['icon'], size='24px', color='var(--primary)')}</span>
                    <strong style="font-size: 1.1rem; color: #1B2A4A;">{rec['product']}</strong>
                </div>
                <span style="font-size: 1.2rem; font-weight: 700; color: {color};">{rec['score']}%</span>
            </div>
            <p style="margin: 0.5rem 0 0 2.5rem; color: #6C757D; font-size: 0.9rem;">{rec['reason']}</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(progress_bar_html(rec["score"], label="Match Score", color=color), unsafe_allow_html=True)
else:
    st.success("Customer already has all recommended products!", icon=":material/check_circle:")

# ── Batch Recommendations ──
st.markdown("---")
st.markdown(f"### {render_html_icon('group', size='22px')} Batch Recommendations", unsafe_allow_html=True)
if st.button("Generate for All Customers", icon=":material/autorenew:", type="primary"):
    with st.spinner("Generating recommendations..."):
        results = []
        for _, cust_row in customers_df.iterrows():
            recs = generate_recommendations(cust_row)
            if recs:
                top_rec = recs[0]
                results.append({
                    "customer_id": cust_row["customer_id"],
                    "name": cust_row["name"],
                    "top_product": top_rec["product"],
                    "match_score": top_rec["score"],
                    "reason": top_rec["reason"]
                })

        result_df = pd.DataFrame(results).sort_values("match_score", ascending=False)
        st.dataframe(result_df.head(50), use_container_width=True)

        csv = result_df.to_csv(index=False)
        st.download_button("Download Recommendations", csv, "product_recommendations.csv", "text/csv", icon=":material/download:")