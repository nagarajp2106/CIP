"""
Data Upload Page — CSV upload, validation, preview, and database insertion.
"""
import streamlit as st
from utils.icons import render_html_icon
import pandas as pd
from authentication import check_auth, require_role
from database import get_connection
from utils.preprocessing import validate_upload, clean_data, get_data_quality_report, classify_and_filter
from utils.auth import log_activity

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
st.markdown("Upload, validate, and store banking datasets")
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
<li><strong>Data Cleanliness:</strong> Empty or missing values in key columns might cause rows to be skipped.</li>
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
    # ── FILE LOADED: Validation, Preview & Commit ──
    try:
        df = pd.read_csv(uploaded_file)
        
        # Run validations
        report = validate_upload(df, target_table)
        quality = get_data_quality_report(df)
        
        rows_detected = len(df)
        missing_count = sum(df.isna().sum())
        duplicate_count = quality.get("duplicates", 0)
        schema_valid = report.get("valid", False)
        
        # Display Status Chips
        st.markdown('<div style="margin-top: 1.5rem; margin-bottom: 1rem;"></div>', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f'<div class="status-pill success" style="display:flex; align-items:center; gap:6px; justify-content:center; width:100%; text-align:center;">{render_html_icon("check_circle", size="18px")} {rows_detected:,} rows</div>', unsafe_allow_html=True)
        with c2:
            if missing_count > 0:
                st.markdown(f'<div class="status-pill warning" style="display:flex; align-items:center; gap:6px; justify-content:center; width:100%; text-align:center;">{render_html_icon("warning", size="18px")} {missing_count:,} missing</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="status-pill success" style="display:flex; align-items:center; gap:6px; justify-content:center; width:100%; text-align:center;">{render_html_icon("check_circle", size="18px")} No missing</div>', unsafe_allow_html=True)
        with c3:
            if duplicate_count > 0:
                st.markdown(f'<div class="status-pill danger" style="display:flex; align-items:center; gap:6px; justify-content:center; width:100%; text-align:center;">{render_html_icon("cancel", size="18px")} {duplicate_count:,} duplicates</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="status-pill success" style="display:flex; align-items:center; gap:6px; justify-content:center; width:100%; text-align:center;">{render_html_icon("check_circle", size="18px")} No duplicates</div>', unsafe_allow_html=True)
        with c4:
            if schema_valid:
                st.markdown(f'<div class="status-pill success" style="display:flex; align-items:center; gap:6px; justify-content:center; width:100%; text-align:center;">{render_html_icon("check_circle", size="18px")} Schema matches</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="status-pill danger" style="display:flex; align-items:center; gap:6px; justify-content:center; width:100%; text-align:center;">{render_html_icon("cancel", size="18px")} Schema mismatch</div>', unsafe_allow_html=True)
                
        # Data Preview
        st.markdown("#### Data Preview (First 5 Rows)")
        st.dataframe(df.head(5), use_container_width=True)
        st.caption(f"Showing 5 of {rows_detected:,} rows · {len(df.columns)} columns")
        
        # Validation Logs (if errors/warnings present)
        if report.get("errors") or report.get("warnings"):
            with st.container(border=True):
                if report.get("errors"):
                    st.markdown(f"<h5 style='margin-top:0; color:var(--danger);'>{render_html_icon('cancel', size='18px', color='var(--danger)')} Validation Errors</h5>", unsafe_allow_html=True)
                    for err in report["errors"]:
                        st.markdown(f"- {err}")
                if report.get("warnings"):
                    st.markdown(f"<h5 style='margin-top:0; color:var(--warning);'>{render_html_icon('warning', size='18px', color='var(--warning)')} Warnings</h5>", unsafe_allow_html=True)
                    for warn in report["warnings"]:
                        st.markdown(f"- {warn}")
            
        # ── Confirm & Action block ──
        st.markdown("### Upload to Database")
        auto_clean = st.checkbox("Auto-clean data before upload (handles missing values and standardizes data format)", value=True)
        
        act_col1, act_col2 = st.columns(2)
        with act_col1:
            confirm_btn = st.button("Confirm Upload", type="primary", disabled=not schema_valid, use_container_width=True)
        with act_col2:
            cancel_btn = st.button("Cancel", use_container_width=True)
            
        if cancel_btn:
            st.session_state["uploader_key"] += 1
            st.rerun()
            
        if confirm_btn:
            upload_df = df.copy()
            
            # Standardize columns
            upload_df.columns = [c.lower().replace(" ", "_") for c in upload_df.columns]
            
            # ── Step 1: Classify and filter rows with missing PKs/FKs ──
            upload_df, excluded_df, filter_report = classify_and_filter(upload_df, target_table)
            
            excluded_count = filter_report["excluded_rows"]
            if excluded_count > 0:
                st.info(
                    f"Excluded {excluded_count} row(s) with missing primary key or required ID fields.",
                    icon=":material/filter_alt:"
                )
            
            # ── Step 2: Auto-clean (type-aware — skips ID/date columns) ──
            if auto_clean and len(upload_df) > 0:
                upload_df, clean_report = clean_data(upload_df, target_table)
                for action in clean_report["actions"]:
                    st.info(f"Clean action: {action}")
                    
            # ── Step 3: Insert into database with skip-reason tracking ──
            total_rows = len(upload_df)
            
            if total_rows == 0:
                st.error(
                    f"Upload failed — all {len(df)} rows were excluded due to missing IDs. "
                    f"No records were inserted into **{target_table}**.",
                    icon=":material/cancel:"
                )
                # Show exclusion reasons
                if filter_report["exclusion_reasons"]:
                    with st.expander(f"View {excluded_count} Excluded Rows", expanded=False):
                        for row_idx, reason in filter_report["exclusion_reasons"][:50]:
                            st.markdown(f"- **Row {row_idx + 1}**: {reason}")
                        if len(filter_report["exclusion_reasons"]) > 50:
                            st.caption(f"… and {len(filter_report['exclusion_reasons']) - 50} more.")
            else:
                progress_bar = st.progress(0.0, text="Uploading records...")
                batch_size = max(1, total_rows // 20)
                
                conn = get_connection()
                inserted = 0
                skipped = 0
                skip_reasons = []  # list of (row_number, reason_string)
                
                for i, (idx, row) in enumerate(upload_df.iterrows()):
                    try:
                        row_dict = row.to_dict()
                        cols = ", ".join(row_dict.keys())
                        placeholders = ", ".join(["?"] * len(row_dict))
                        conn.execute(
                            f"INSERT INTO {target_table} ({cols}) VALUES ({placeholders})",
                            list(row_dict.values())
                        )
                        inserted += 1
                    except Exception as e:
                        skipped += 1
                        err_msg = str(e)
                        # Make common SQLite errors more readable
                        if "UNIQUE constraint failed" in err_msg:
                            field = err_msg.split("UNIQUE constraint failed: ")[-1].strip()
                            skip_reasons.append((idx + 1, f"Duplicate {field}"))
                        elif "NOT NULL constraint failed" in err_msg:
                            field = err_msg.split("NOT NULL constraint failed: ")[-1].strip()
                            skip_reasons.append((idx + 1, f"Missing required field: {field}"))
                        else:
                            skip_reasons.append((idx + 1, err_msg))
                        
                    # Update progress bar
                    if (i + 1) % batch_size == 0 or (i + 1) == total_rows:
                        progress_pct = float(i + 1) / total_rows
                        progress_bar.progress(progress_pct, text=f"Processing: {i+1}/{total_rows} rows...")
                
                conn.commit()
                conn.close()
                progress_bar.empty()
                
                # ── Step 4: Result banners based on actual counts ──
                total_original = len(df)
                
                if inserted == total_original and skipped == 0 and excluded_count == 0:
                    # Perfect upload — green success
                    st.toast(f"Successfully uploaded {inserted} records to {target_table.title()}!", icon="✅")
                    st.success(
                        f"Upload complete! {inserted} records added to **{target_table}**.",
                        icon=":material/check_circle:"
                    )
                    log_activity(
                        user["user_id"], user["username"],
                        "DATA_UPLOAD",
                        f"Uploaded {inserted} records to {target_table} from {uploaded_file.name}"
                    )
                elif inserted == 0:
                    # Total failure — red error
                    st.error(
                        f"Upload failed — 0 of {total_original} records were inserted into **{target_table}**. See reasons below.",
                        icon=":material/cancel:"
                    )
                    log_activity(
                        user["user_id"], user["username"],
                        "DATA_UPLOAD",
                        f"Upload FAILED: 0 of {total_original} records inserted to {target_table} from {uploaded_file.name}"
                    )
                else:
                    # Partial success — amber warning
                    total_not_inserted = skipped + excluded_count
                    st.warning(
                        f"Upload partially completed — {inserted} of {total_original} records added to **{target_table}**, "
                        f"{total_not_inserted} skipped.",
                        icon=":material/warning:"
                    )
                    log_activity(
                        user["user_id"], user["username"],
                        "DATA_UPLOAD",
                        f"Partial upload: {inserted} of {total_original} records to {target_table} from {uploaded_file.name} ({total_not_inserted} skipped)"
                    )
                
                # Upload Summary metrics
                with st.container(border=True):
                    st.markdown("#### Upload Summary")
                    s1, s2, s3, s4 = st.columns(4)
                    s1.metric("Total Rows", total_original)
                    s2.metric("Inserted", inserted)
                    s3.metric("Skipped (Insert)", skipped)
                    s4.metric("Excluded (Invalid ID)", excluded_count)
                
                # Expandable skip reasons
                all_reasons = filter_report["exclusion_reasons"] + skip_reasons
                if all_reasons:
                    with st.expander(f"View {len(all_reasons)} Skipped/Excluded Row Details", expanded=False):
                        if filter_report["exclusion_reasons"]:
                            st.markdown("**Excluded before insert (missing ID):**")
                            for row_idx, reason in filter_report["exclusion_reasons"][:30]:
                                st.markdown(f"- **Row {row_idx + 1}**: {reason}")
                            if len(filter_report["exclusion_reasons"]) > 30:
                                st.caption(f"… and {len(filter_report['exclusion_reasons']) - 30} more exclusions.")
                        if skip_reasons:
                            st.markdown("**Skipped during insert:**")
                            for row_num, reason in skip_reasons[:30]:
                                st.markdown(f"- **Row {row_num}**: {reason}")
                            if len(skip_reasons) > 30:
                                st.caption(f"… and {len(skip_reasons) - 30} more skips.")
            
    except Exception as e:
        st.error(f"Error processing CSV: {str(e)}", icon=":material/cancel:")