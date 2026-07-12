"""
AI Business Insights Page — Auto-generated data-driven insights.
"""
import streamlit as st
from utils.icons import render_html_icon, get_symbol_name
import pandas as pd
import numpy as np
from authentication import check_auth, require_role
from database import get_connection
from utils.visualization import kpi_card

# ── Auth ──
user = check_auth()
if not user:
    st.switch_page("app.py")
require_role("AI Business Insights")

# Page Header & Actions Layout
col_head, col_btn = st.columns([4, 1])
with col_head:
    st.markdown(f"""<h1 style="display: flex; align-items: center; gap: 10px; margin: 0; color: var(--primary); font-weight: 700; font-size: 2.2rem; line-height: 1.2;">
    {render_html_icon('smart_toy', size='36px', color='var(--primary)')}
    <span>AI Business Insights</span>
    </h1>""", unsafe_allow_html=True)
    st.markdown("Automatically generated data-driven insights for strategic decision making")
with col_btn:
    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
    refresh_clicked = st.button("Refresh Insights", icon=":material/autorenew:", type="primary", use_container_width=True)
    if refresh_clicked:
        st.session_state.pop("insights_cache", None)
        st.rerun()

st.markdown("---")

conn = get_connection()
customers_df = pd.read_sql("SELECT * FROM customers", conn)
transactions_df = pd.read_sql("SELECT * FROM transactions", conn)
loans_df = pd.read_sql("SELECT * FROM loans", conn)
accounts_df = pd.read_sql("SELECT * FROM accounts", conn)
conn.close()

if customers_df.empty:
    st.warning("No data available for insight generation.", icon=":material/warning:")
    st.stop()


def generate_insights() -> list[dict]:
    """Generate AI-driven business insights from data analysis."""
    insights = []

    # ── Customer Insights ──
    # Churn analysis
    active_pct = customers_df["is_active"].mean() * 100
    churn_pct = 100 - active_pct
    insights.append({
        "icon": "", "category": "Customer",
        "text": f"Customer churn rate is **{churn_pct:.1f}%**. {'This is within acceptable limits.' if churn_pct < 10 else 'Immediate retention strategies are recommended.'}",
        "severity": "info" if churn_pct < 10 else "warning"
    })

    # High-income segment
    high_income = customers_df[customers_df["income"] > customers_df["income"].quantile(0.75)]
    high_income_churn = (1 - high_income["is_active"].mean()) * 100
    insights.append({
        "icon": "", "category": "Customer",
        "text": f"High-income customers (top 25%) have a **{high_income_churn:.1f}%** churn rate. {'They show strong loyalty.' if high_income_churn < 5 else 'Consider premium retention programs.'}",
        "severity": "success" if high_income_churn < 5 else "warning"
    })

    # Age group analysis
    age_deposit = customers_df.groupby(pd.cut(customers_df["age"], bins=[0, 30, 45, 60, 100], labels=["18-30", "31-45", "46-60", "60+"]))["balance"].mean()
    top_age_group = age_deposit.idxmax()
    insights.append({
        "icon": "", "category": "Customer",
        "text": f"Customers aged **{top_age_group}** hold the highest average balance of **${age_deposit.max():,.0f}**. Target this segment for premium products.",
        "severity": "info"
    })

    # ── Revenue Insights ──
    if not transactions_df.empty:
        transactions_df["date"] = pd.to_datetime(transactions_df["date"], errors="coerce")
        monthly_revenue = transactions_df.groupby(transactions_df["date"].dt.to_period("M"))["amount"].sum()
        if len(monthly_revenue) >= 2:
            recent = monthly_revenue.iloc[-1]
            previous = monthly_revenue.iloc[-2]
            growth = ((recent - previous) / max(previous, 1)) * 100
            insights.append({
                "icon": "", "category": "Revenue",
                "text": f"Monthly transaction volume {'increased' if growth > 0 else 'decreased'} by **{abs(growth):.1f}%**. {'Strong growth trajectory.' if growth > 5 else 'Revenue growth needs attention.' if growth < -5 else 'Stable performance.'}",
                "severity": "success" if growth > 5 else "warning" if growth < -5 else "info"
            })

        # Deposit vs withdrawal ratio
        deposits = transactions_df[transactions_df["type"] == "Deposit"]["amount"].sum()
        withdrawals = transactions_df[transactions_df["type"] == "Withdrawal"]["amount"].sum()
        ratio = deposits / max(withdrawals, 1)
        insights.append({
            "icon": "", "category": "Revenue",
            "text": f"Deposit-to-withdrawal ratio is **{ratio:.2f}x**. {'Healthy liquidity position.' if ratio > 1.2 else 'Monitor liquidity carefully.'}",
            "severity": "success" if ratio > 1.2 else "warning"
        })

    # ── Risk Insights ──

    # High-risk customers
    high_risk = customers_df[customers_df["risk_level"] == "High"]
    insights.append({
        "icon": "", "category": "Risk",
        "text": f"**{len(high_risk):,}** customers ({len(high_risk)/max(len(customers_df),1)*100:.1f}%) are classified as **High Risk**. Additional verification and monitoring recommended.",
        "severity": "warning" if len(high_risk) > len(customers_df) * 0.15 else "info"
    })

    # ── Loan Insights ──
    if not loans_df.empty:
        approved = loans_df[loans_df["status"].isin(["Active", "Closed"])]
        approval_rate = len(approved) / max(len(loans_df), 1) * 100
        insights.append({
            "icon": "", "category": "Operations",
            "text": f"Loan approval rate is **{approval_rate:.1f}%**. {'Strong lending performance.' if approval_rate > 70 else 'Review underwriting criteria.'}",
            "severity": "success" if approval_rate > 70 else "info"
        })

        # Loan type analysis
        top_loan = loans_df.groupby("loan_type")["loan_amount"].sum().idxmax()
        top_loan_amt = loans_df.groupby("loan_type")["loan_amount"].sum().max()
        insights.append({
            "icon": "", "category": "Operations",
            "text": f"**{top_loan}** is the most popular loan product with total disbursement of **${top_loan_amt:,.0f}**.",
            "severity": "info"
        })

        # Default analysis
        default_rate = len(loans_df[loans_df["status"] == "Defaulted"]) / max(len(loans_df), 1) * 100
        insights.append({
            "icon": "warning", "category": "Risk",
            "text": f"Loan default rate is **{default_rate:.1f}%**. {'Well controlled.' if default_rate < 5 else 'Requires immediate risk mitigation strategies.'}",
            "severity": "success" if default_rate < 5 else "warning"
        })

    # ── Operations Insights ──
    # Regional performance
    region_balance = customers_df.groupby("region")["balance"].mean()
    top_region = region_balance.idxmax()
    insights.append({
        "icon": "", "category": "Operations",
        "text": f"**{top_region}** region has the highest average customer balance of **${region_balance.max():,.0f}**. Consider expanding services in this area.",
        "severity": "info"
    })

    # Credit card insights
    if not accounts_df.empty:
        savings_pct = len(accounts_df[accounts_df["account_type"] == "Savings"]) / max(len(accounts_df), 1) * 100
        insights.append({
            "icon": "", "category": "Operations",
            "text": f"**{savings_pct:.1f}%** of accounts are Savings accounts. {'Cross-sell current accounts and FDs.' if savings_pct > 40 else 'Good product diversification.'}",
            "severity": "info"
        })

    # Customer tenure
    customers_df["customer_since"] = pd.to_datetime(customers_df["customer_since"], errors="coerce")
    avg_tenure = (pd.Timestamp.now() - customers_df["customer_since"]).dt.days.mean() / 365
    insights.append({
        "icon": "schedule", "category": "Customer",
        "text": f"Average customer tenure is **{avg_tenure:.1f} years**. {'Strong customer loyalty.' if avg_tenure > 3 else 'Focus on early engagement programs.'}",
        "severity": "success" if avg_tenure > 3 else "info"
    })

    # Credit score distribution
    avg_cs = customers_df["credit_score"].mean()
    insights.append({
        "icon": "", "category": "Customer",
        "text": f"Average credit score across all customers is **{avg_cs:.0f}**. {'Healthy portfolio.' if avg_cs > 680 else 'Consider credit improvement initiatives.'}",
        "severity": "success" if avg_cs > 680 else "info"
    })

    return insights


def format_bold_text(text: str) -> str:
    """Replace Markdown **bold** syntax with HTML <strong>bold</strong> syntax."""
    parts = text.split("**")
    formatted = []
    for i, part in enumerate(parts):
        if i % 2 == 1:
            formatted.append(f"<strong>{part}</strong>")
        else:
            formatted.append(part)
    return "".join(formatted)


# ── Generate and Display ──
if "insights_cache" not in st.session_state:
    with st.spinner("Analyzing data and generating insights..."):
        st.session_state["insights_cache"] = generate_insights()

insights = st.session_state["insights_cache"]

# Summary
s1, s2, s3, s4 = st.columns(4)
categories = {}
for ins in insights:
    categories[ins["category"]] = categories.get(ins["category"], 0) + 1

with s1:
    st.markdown(kpi_card("Total Insights", f"{len(insights)}", "smart_toy", color="blue"), unsafe_allow_html=True)
with s2:
    st.markdown(kpi_card("Categories", f"{len(categories)}", "category", color="gold"), unsafe_allow_html=True)
with s3:
    warnings = sum(1 for i in insights if i["severity"] == "warning")
    st.markdown(kpi_card("Warnings", f"{warnings}", "warning", color="orange"), unsafe_allow_html=True)
with s4:
    successes = sum(1 for i in insights if i["severity"] == "success")
    st.markdown(kpi_card("Positive", f"{successes}", "check_circle", color="green"), unsafe_allow_html=True)

st.markdown("---")

# Category filter
f1, f2 = st.columns([1, 2])
with f1:
    category_filter = st.selectbox("Filter by Category", ["All"] + list(categories.keys()))

st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

# Display insights
severity_colors = {
    "success": "var(--success)", 
    "warning": "var(--warning)", 
    "info": "var(--secondary)"
}
severity_bgs = {
    "success": "var(--success-bg)", 
    "warning": "var(--warning-bg)", 
    "info": "var(--info-bg)"
}
category_colors = {
    "Customer": "var(--secondary)", 
    "Revenue": "var(--success)", 
    "Risk": "var(--danger)", 
    "Operations": "#6F42C1"
}

for insight in insights:
    if category_filter != "All" and insight["category"] != category_filter:
        continue

    border_color = severity_colors.get(insight["severity"], "var(--text-muted)")
    bg_color = severity_bgs.get(insight["severity"], "var(--bg-light)")
    cat_color = category_colors.get(insight["category"], "var(--text-muted)")

    # Resolve icon
    icon_name = insight.get("icon")
    if not icon_name:
        if insight["category"] == "Risk":
            icon_name = "warning"
        elif insight["category"] == "Revenue":
            icon_name = "payments"
        elif insight["category"] == "Operations":
            icon_name = "settings"
        else:
            icon_name = "person"

    # Format bold text syntax
    formatted_text = format_bold_text(insight["text"])

    st.markdown(f"""
    <div class="insight-row-card" style="border-left-color: {border_color}; background-color: {bg_color};">
        <div style="display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
            {render_html_icon(icon_name, size="20px", color=border_color)}
        </div>
        <div style="flex-shrink: 0; min-width: 90px; text-align: center;">
            <span style="display: inline-block; width: 90px; padding: 3px 8px; border-radius: 12px; background: {cat_color}; color: white; font-size: 0.75rem; font-weight: 600;">{insight['category']}</span>
        </div>
        <div style="flex-grow: 1; color: var(--text-main); font-size: 0.92rem; line-height: 1.4;">
            {formatted_text}
        </div>
    </div>
    """, unsafe_allow_html=True)

# Add spacer at bottom to prevent layout clipping
st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)