"""
Reports Module — Generate and export professional Excel and PDF reports.
"""
import streamlit as st
import pandas as pd
import io
import os
from datetime import datetime, date, timedelta
from authentication import check_auth, require_role
from database import get_connection
from utils.visualization import kpi_card
from utils.auth import log_activity
from config import REPORTS_DIR, REGIONS, BRANCHES
from utils.icons import render_html_icon
from utils.reports import (
    generate_excel_report, generate_pdf_report,
    get_report_data, get_kpi_data,
)

# ── Auth ──
user = check_auth()
if not user:
    st.switch_page("app.py")
require_role("Reports")

st.markdown(f"""<h1 style="display: flex; align-items: center; gap: 10px; margin-top: 0;
    color: var(--primary); font-weight: 700; font-size: 2.2rem; line-height: 1.2;">
    {render_html_icon('description', size='36px', color='var(--primary)')}
    <span>Reports</span>
</h1>""", unsafe_allow_html=True)
st.markdown("Generate and export professional banking reports")
st.markdown("---")

# ──────────────────────────────────────────────
# Report Type Selection
# ──────────────────────────────────────────────
REPORT_TYPES = {
    "Customer Report": {"table": "customers", "description": "Comprehensive customer data report"},
    "Loan Report": {"table": "loans", "description": "Loan portfolio analysis report"},
    "Transaction Report": {"table": "transactions", "description": "Transaction activity report"},
    "Customer Segmentation Report": {"table": "customers", "description": "Customer segmentation analysis"},
    "Churn Report": {"table": "customers", "description": "Customer churn analysis report"},
    "Executive Dashboard Summary": {"table": None, "description": "High-level executive summary"},
}

selected_report = st.selectbox("Select Report Type", list(REPORT_TYPES.keys()))
report_config = REPORT_TYPES[selected_report]
st.info(f"**{selected_report}**: {report_config['description']}")

# ──────────────────────────────────────────────
# Export Options Panel
# ──────────────────────────────────────────────
st.markdown(f"### {render_html_icon('tune', size='22px')} Export Options", unsafe_allow_html=True)

opt_col1, opt_col2 = st.columns(2)

with opt_col1:
    export_format = st.selectbox("Export Format", ["Excel (.xlsx)", "PDF (.pdf)"])
    max_rows = st.number_input("Max Rows", value=1000, min_value=100, max_value=10000, step=100)

with opt_col2:
    if "Excel" in export_format:
        st.markdown("**Include Sheets:**")
        include_summary = st.checkbox("Summary Sheet", value=True, key="inc_summary")
        include_data = st.checkbox("Data Sheet", value=True, key="inc_data")
        include_charts = st.checkbox("Charts Sheet", value=True, key="inc_charts")
    else:
        include_summary = True
        include_data = True
        include_charts = False

# ── Filters ──
st.markdown(f"#### {render_html_icon('filter_list', size='20px')} Filters", unsafe_allow_html=True)

filter_col1, filter_col2 = st.columns(2)

with filter_col1:
    date_from = st.date_input("Date From", value=date(2018, 1, 1), key="filter_date_from")
    region_filter = st.multiselect("Region", options=REGIONS, default=[], key="filter_region")

with filter_col2:
    date_to = st.date_input("Date To", value=date.today(), key="filter_date_to")
    branch_filter = st.multiselect("Branch", options=BRANCHES, default=[], key="filter_branch")

# Build filters dict
active_filters = {}
if region_filter:
    active_filters["region"] = region_filter
if branch_filter:
    active_filters["branch"] = branch_filter
if date_from:
    active_filters["date_from"] = str(date_from)
if date_to:
    active_filters["date_to"] = str(date_to)

# ──────────────────────────────────────────────
# Generate Report
# ──────────────────────────────────────────────
st.markdown("---")

if st.button("Generate Report", type="primary", use_container_width=True):
    progress = st.progress(0, text="Initializing report...")

    conn = get_connection()

    # ── Fetch Data ──
    progress.progress(10, text="Fetching data...")

    if selected_report == "Executive Dashboard Summary":
        # Build executive summary as a simple table
        customers = pd.read_sql("SELECT COUNT(*) as c FROM customers", conn).iloc[0]["c"]
        accounts = pd.read_sql("SELECT COUNT(*) as c FROM accounts", conn).iloc[0]["c"]
        loans = pd.read_sql("SELECT COUNT(*) as c FROM loans", conn).iloc[0]["c"]
        txns = pd.read_sql("SELECT COUNT(*) as c FROM transactions", conn).iloc[0]["c"]
        total_deposits = pd.read_sql(
            "SELECT COALESCE(SUM(amount), 0) as s FROM transactions WHERE type='Deposit'", conn
        ).iloc[0]["s"]
        total_loans_amt = pd.read_sql(
            "SELECT COALESCE(SUM(loan_amount), 0) as s FROM loans", conn
        ).iloc[0]["s"]
        avg_balance = pd.read_sql(
            "SELECT COALESCE(AVG(balance), 0) as a FROM customers", conn
        ).iloc[0]["a"]

        df = pd.DataFrame([
            {"Metric": "Total Customers", "Value": f"{customers:,}"},
            {"Metric": "Total Accounts", "Value": f"{accounts:,}"},
            {"Metric": "Total Loans", "Value": f"{loans:,}"},
            {"Metric": "Total Transactions", "Value": f"{txns:,}"},
            {"Metric": "Total Deposits", "Value": f"${total_deposits:,.2f}"},
            {"Metric": "Total Loan Amount", "Value": f"${total_loans_amt:,.2f}"},
            {"Metric": "Average Balance", "Value": f"${avg_balance:,.2f}"},
        ])
    else:
        df = get_report_data(selected_report, conn, filters=active_filters)
        if len(df) > max_rows:
            df = df.head(max_rows)

    progress.progress(30, text="Data fetched successfully.")

    # ── Preview ──
    st.markdown(f"### {render_html_icon('preview', size='22px')} Report Preview", unsafe_allow_html=True)
    st.markdown(f"**Records:** {len(df):,} | **Columns:** {len(df.columns)}")
    st.dataframe(df.head(50), use_container_width=True)

    # ── Export ──
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{selected_report.replace(' ', '_')}_{timestamp}"

    if "Excel" in export_format:
        progress.progress(40, text="Building Summary sheet...")

        # Get KPIs
        kpi_data = get_kpi_data(conn, report_type=selected_report)

        progress.progress(55, text="Formatting Data sheet...")

        # Build filter display dict
        filter_display = {}
        if region_filter:
            filter_display["Region"] = ", ".join(region_filter)
        if branch_filter:
            filter_display["Branch"] = ", ".join(branch_filter)
        if date_from:
            filter_display["Date From"] = str(date_from)
        if date_to:
            filter_display["Date To"] = str(date_to)

        progress.progress(70, text="Generating Charts...")

        buffer = generate_excel_report(
            report_title=selected_report,
            data=df,
            user_name=user["full_name"],
            filters=filter_display,
            kpi_data=kpi_data,
            report_type=selected_report,
            include_summary=include_summary,
            include_data=include_data,
            include_charts=include_charts,
        )

        file_size = buffer.getbuffer().nbytes
        progress.progress(100, text="Report ready!")

        # Size formatting
        if file_size > 1024 * 1024:
            size_str = f"{file_size / (1024 * 1024):.1f} MB"
        else:
            size_str = f"{file_size / 1024:.1f} KB"

        st.success(f"**{filename}.xlsx** generated successfully — {size_str}")

        st.download_button(
            f"{render_html_icon('download', size='18px')} Download Excel Report",
            buffer,
            f"{filename}.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    else:  # PDF
        progress.progress(50, text="Generating PDF...")

        try:
            from reportlab.lib.pagesizes import letter, landscape
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.units import inch

            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
            styles = getSampleStyleSheet()
            elements = []

            # Title
            elements.append(Paragraph(f"<b>{selected_report}</b>", styles["Title"]))
            elements.append(Paragraph(
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | By: {user['full_name']}",
                styles["Normal"]
            ))
            elements.append(Spacer(1, 0.25 * inch))

            # Table data (limit columns for PDF readability)
            display_cols = df.columns[:8].tolist()
            table_data = [display_cols]
            for _, row in df.head(100).iterrows():
                table_data.append([str(row[col])[:30] for col in display_cols])

            if table_data:
                t = Table(table_data)
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1B2A4A')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#D4AF37')),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 8),
                    ('FONTSIZE', (0, 1), (-1, -1), 7),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1),
                     [colors.white, colors.HexColor('#F8F9FA')]),
                ]))
                elements.append(t)

            doc.build(elements)
            buffer.seek(0)

            file_size = buffer.getbuffer().nbytes
            progress.progress(100, text="Report ready!")

            if file_size > 1024 * 1024:
                size_str = f"{file_size / (1024 * 1024):.1f} MB"
            else:
                size_str = f"{file_size / 1024:.1f} KB"

            st.success(f"**{filename}.pdf** generated successfully — {size_str}")

            st.download_button(
                f"{render_html_icon('download', size='18px')} Download PDF Report",
                buffer,
                f"{filename}.pdf",
                "application/pdf",
                use_container_width=True,
            )
        except ImportError:
            st.error("ReportLab not installed. Please install it: `pip install reportlab`",
                     icon=":material/cancel:")

    conn.close()

    # Log activity
    log_activity(user["user_id"], user["username"], "REPORT_GENERATED",
                 f"Generated {selected_report} ({export_format})")