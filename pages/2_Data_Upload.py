"""
Data Upload Page — CSV file intake and basic structural validation.
Stores the uploaded DataFrame in session state for processing on the
Data Preprocessing page.  Does NOT insert into the database.
"""
import streamlit as st
from utils.icons import render_html_icon
import pandas as pd
from authentication import check_auth, require_role
from database import get_connection
from utils.preprocessing import validate_upload

# ── Auth ──
user = check_auth()
if not user:
    st.switch_page("app.py")
require_role("Data Upload")

# Page Header
st.markdown(f"""<h1 style="display: flex; align-items: center; gap: 10px; margin-top: 0; color: var(--primary); font-weight: 700; font-size: 2.2rem; line-height: 1.2;">
{render_html_icon('upload_file', size='36px', color='var(--primary)')}
<span>Data Upload</span>
</h1>""", unsafe_allow_html=True)
st.markdown("Upload and validate banking datasets before preprocessing")
st.markdown("---")

# Schema helper mapping
EXPECTED_SCHEMAS = {
    "customers": "customer_id, name, gender, age, occupation, income, region, branch, balance, credit_score, customer_since, email, phone, is_active, risk_level, churn_score, clv_score, segment",
    "accounts": "account_number, customer_id, account_type, balance, status, opened_date",
    "transactions": "transaction_id, customer_id, account_number, amount, date, type, channel, merchant, description, is_fraud",
    "loans": "loan_id, customer_id, loan_type, loan_amount, interest_rate, tenure_months, emi, status, applied_date, approved_date",
    "cards": "card_number, customer_id, card_type, card_limit, outstanding_amount, status, issued_date, expiry_date",
}

# ── Table Selection and Upload Form Card ──
st.markdown('<div class="form-card">', unsafe_allow_html=True)

target_table = st.selectbox(
    "Select Target Table",
    ["customers", "accounts", "transactions", "loans", "cards"],
    format_func=lambda x: x.title(),
    key="target_table_selectbox"
)

# Display schema helper caption under the dropdown
st.caption(f"**Expected columns**: {EXPECTED_SCHEMAS[target_table]}")

# Initialize uploader key to allow resetting
if "uploader_key" not in st.session_state:
    st.session_state["uploader_key"] = 0

uploaded_file = st.file_uploader(
    "Upload CSV File",
    type=["csv"],
    key=f"csv_uploader_{st.session_state['uploader_key']}",
    help="Upload a CSV file with data matching the selected table schema."
)

st.markdown('</div>', unsafe_allow_html=True)

# ── Upload View Logic ──
if uploaded_file is None:
    # ── EMPTY STATE: Guidelines & Recent Uploads ──
    st.markdown('<div style="margin-top: 1.5rem;"></div>', unsafe_allow_html=True)
    g_col1, g_col2 = st.columns(2)
    
    with g_col1:
        guidelines_html = f"""<div class="list-card animate-in" style="height: 100%;">
<h4 style="margin:0 0 12px 0; color:var(--primary); font-weight:700; display:flex; align-items:center; gap:8px;">
{render_html_icon("info", size="22px", color="var(--secondary)")} Upload Guidelines
</h4>
<ul style="margin: 0; padding-left: 1.2rem; color: var(--text-muted); font-size: 0.9rem; line-height: 1.6;">
<li><strong>Format:</strong> Only comma-separated values (<code>.csv</code>) files are supported.</li>
<li><strong>Size Limit:</strong> Files must be smaller than 50 MB.</li>
<li><strong>Required Schema:</strong> Column names must match the expected columns listed under the selector dropdown (case-insensitive).</li>
<li><strong>Workflow:</strong> After uploading, you will be directed to <strong>Data Preprocessing</strong> to validate, clean, and insert the data into the database.</li>
</ul>
</div>"""
        st.markdown(guidelines_html, unsafe_allow_html=True)
        
    with g_col2:
        conn = get_connection()
        recent_df = pd.read_sql(
            "SELECT details, timestamp FROM audit_logs WHERE action = 'DATA_UPLOAD' ORDER BY id DESC LIMIT 5", 
            conn
        )
        conn.close()
        
        recent_html = ""
        if not recent_df.empty:
            for _, row in recent_df.iterrows():
                ts = row["timestamp"]
                details = row["details"]
                recent_html += f"""<div style="padding: 0.75rem 0; border-bottom: 1px solid var(--border-color); font-size: 0.88rem;">
<div style="color: var(--primary); font-weight: 600; display: flex; align-items: center; gap: 6px;">
{render_html_icon("check_circle", size="16px", color="var(--success)")} 
<span>{details}</span>
</div>
<div style="color: var(--text-muted); font-size: 0.75rem; margin-top: 2px;">{ts}</div>
</div>"""
        else:
            recent_html = "<p style='color: var(--text-muted); font-size: 0.9rem; margin: 0;'>No recent uploads recorded.</p>"
            
        uploads_card_html = f"""<div class="list-card animate-in" style="height: 100%;">
<h4 style="margin:0 0 12px 0; color:var(--primary); font-weight:700; display:flex; align-items:center; gap:8px;">
{render_html_icon("schedule", size="22px", color="var(--secondary)")} Recent Uploads
</h4>
<div style="display: flex; flex-direction: column; gap: 4px;">
{recent_html}
</div>
</div>"""
        st.markdown(uploads_card_html, unsafe_allow_html=True)

else:
    # ── FILE LOADED: Structural validation only ──
    try:
        df = pd.read_csv(uploaded_file)
        
        # Run basic structural validation (column names, schema match)
        report = validate_upload(df, target_table)
        
        rows_detected = len(df)
        schema_valid = report.get("valid", False)
        
        # Display Status Chips
        st.markdown('<div style="margin-top: 1.5rem; margin-bottom: 1rem;"></div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f'<div class="status-pill success" style="display:flex; align-items:center; gap:6px; justify-content:center; width:100%; text-align:center;">{render_html_icon("check_circle", size="18px")} {rows_detected:,} rows detected</div>', unsafe_allow_html=True)
        with c2:
            if schema_valid:
                st.markdown(f'<div class="status-pill success" style="display:flex; align-items:center; gap:6px; justify-content:center; width:100%; text-align:center;">{render_html_icon("check_circle", size="18px")} Schema matches</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="status-pill danger" style="display:flex; align-items:center; gap:6px; justify-content:center; width:100%; text-align:center;">{render_html_icon("cancel", size="18px")} Schema mismatch</div>', unsafe_allow_html=True)
                
        # Data Preview
        st.markdown("#### Data Preview (First 5 Rows)")
        st.dataframe(df.head(5), use_container_width=True)
        st.caption(f"Showing 5 of {rows_detected:,} rows · {len(df.columns)} columns")
        
        # Validation Logs (if errors present — schema mismatch)
        if report.get("errors"):
            with st.container(border=True):
                st.markdown(f"<h5 style='margin-top:0; color:var(--danger);'>{render_html_icon('cancel', size='18px', color='var(--danger)')} Validation Errors</h5>", unsafe_allow_html=True)
                for err in report["errors"]:
                    st.markdown(f"- {err}")
                st.info("Fix the schema errors above and re-upload the file.", icon=":material/info:")
        
        # Warnings (informational — duplicates, type issues)
        if report.get("warnings"):
            with st.container(border=True):
                st.markdown(f"<h5 style='margin-top:0; color:var(--warning);'>{render_html_icon('warning', size='18px', color='var(--warning)')} Data Quality Warnings</h5>", unsafe_allow_html=True)
                for warn in report["warnings"]:
                    st.markdown(f"- {warn}")
                st.caption("These issues will be addressed during preprocessing.")
            
        # ── Action block ──
        act_col1, act_col2 = st.columns(2)
        with act_col1:
            continue_btn = st.button(
                "Continue to Data Preprocessing",
                type="primary",
                disabled=not schema_valid,
                use_container_width=True
            )
        with act_col2:
            cancel_btn = st.button("Cancel", use_container_width=True)
            
        if cancel_btn:
            # Clear any pending upload and reset
            if "upload_pending" in st.session_state:
                del st.session_state["upload_pending"]
            st.session_state["uploader_key"] += 1
            st.rerun()
            
        if continue_btn:
            # Store raw DataFrame and metadata in session state
            st.session_state["upload_pending"] = {
                "df": df,
                "table_name": target_table,
                "file_name": uploaded_file.name,
                "rows": rows_detected,
                "columns": len(df.columns),
            }
            st.switch_page("pages/3_Data_Preprocessing.py")
            
    except Exception as e:
        st.error(f"Error processing CSV: {str(e)}", icon=":material/cancel:")