"""
Data Preprocessing Page — Upload validation & insert, auto-cleaning,
feature engineering, encoding, and scaling.
"""
import streamlit as st
from utils.icons import render_html_icon
import pandas as pd
from authentication import check_auth, require_role
from database import get_connection
from utils.preprocessing import (
    clean_data, get_data_quality_report, validate_upload,
    classify_and_filter, check_foreign_keys
)
from utils.feature_engineering import (
    apply_all_features, encode_features, scale_features,
    create_age_group, create_income_category, create_balance_category,
    calculate_customer_tenure, calculate_customer_value_score
)
from utils.auth import log_activity

# ── Auth ──
user = check_auth()
if not user:
    st.switch_page("app.py")
require_role("Data Preprocessing")

st.markdown(f"# {render_html_icon('build', size='30px')} Data Preprocessing", unsafe_allow_html=True)
st.markdown("Clean, validate, and engineer features from banking data")
st.markdown("---")

# Load existing DB data for the feature engineering / encoding / scaling tabs
conn = get_connection()
customers_df = pd.read_sql("SELECT * FROM customers", conn)
transactions_df = pd.read_sql("SELECT * FROM transactions", conn)
conn.close()

# ── Determine which tabs to show ──
has_pending = "upload_pending" in st.session_state

if has_pending:
    tab_labels = [
        ":material/upload_file: Upload Validation",
        ":material/cleaning_services: Auto Clean",
        ":material/settings: Feature Engineering",
        ":material/font_download: Encoding",
        ":material/straighten: Scaling",
    ]
    tab_upload, tab1, tab2, tab3, tab4 = st.tabs(tab_labels)
else:
    tab_labels = [
        ":material/cleaning_services: Auto Clean",
        ":material/settings: Feature Engineering",
        ":material/font_download: Encoding",
        ":material/straighten: Scaling",
    ]
    tab1, tab2, tab3, tab4 = st.tabs(tab_labels)
    tab_upload = None

# ═══════════════════════════════════════════════
# Tab: Upload Validation (only when pending upload exists)
# ═══════════════════════════════════════════════
if tab_upload is not None:
    with tab_upload:
        pending = st.session_state["upload_pending"]
        raw_df = pending["df"]
        target_table = pending["table_name"]
        file_name = pending["file_name"]

        st.markdown(f"### Validating upload: `{file_name}` → **{target_table.title()}**")

        # Standardize column names
        work_df = raw_df.copy()
        work_df.columns = [c.lower().replace(" ", "_") for c in work_df.columns]

        # ── 1. Basic stats ──
        report = validate_upload(raw_df, target_table)
        quality = get_data_quality_report(work_df)

        rows_detected = len(work_df)
        missing_count = int(work_df.isna().sum().sum())
        duplicate_count = quality.get("duplicates", 0)

        st.markdown('<div style="margin-top: 1rem; margin-bottom: 1rem;"></div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f'<div class="status-pill success" style="display:flex; align-items:center; gap:6px; justify-content:center; width:100%; text-align:center;">{render_html_icon("check_circle", size="18px")} {rows_detected:,} rows</div>', unsafe_allow_html=True)
        with c2:
            pill_cls = "warning" if missing_count > 0 else "success"
            pill_icon = "warning" if missing_count > 0 else "check_circle"
            pill_text = f"{missing_count:,} missing" if missing_count > 0 else "No missing"
            st.markdown(f'<div class="status-pill {pill_cls}" style="display:flex; align-items:center; gap:6px; justify-content:center; width:100%; text-align:center;">{render_html_icon(pill_icon, size="18px")} {pill_text}</div>', unsafe_allow_html=True)
        with c3:
            pill_cls = "danger" if duplicate_count > 0 else "success"
            pill_icon = "cancel" if duplicate_count > 0 else "check_circle"
            pill_text = f"{duplicate_count:,} duplicates" if duplicate_count > 0 else "No duplicates"
            st.markdown(f'<div class="status-pill {pill_cls}" style="display:flex; align-items:center; gap:6px; justify-content:center; width:100%; text-align:center;">{render_html_icon(pill_icon, size="18px")} {pill_text}</div>', unsafe_allow_html=True)

        # Data preview
        st.markdown("#### Data Preview (First 5 Rows)")
        st.dataframe(raw_df.head(5), use_container_width=True)
        st.caption(f"Showing 5 of {rows_detected:,} rows · {len(raw_df.columns)} columns")

        # ── 2. Schema warnings ──
        if report.get("warnings"):
            with st.container(border=True):
                st.markdown(f"<h5 style='margin-top:0; color:var(--warning);'>{render_html_icon('warning', size='18px', color='var(--warning)')} Data Quality Warnings</h5>", unsafe_allow_html=True)
                for warn in report["warnings"]:
                    st.markdown(f"- {warn}")

        # ── 3. Foreign Key validation ──
        conn = get_connection()
        fk_report = check_foreign_keys(work_df, target_table, conn)
        conn.close()

        fk_invalid_indices = set()
        if fk_report["has_issues"]:
            with st.container(border=True):
                st.markdown(f"<h5 style='margin-top:0; color:var(--danger);'>{render_html_icon('link_off', size='18px', color='var(--danger)')} Foreign Key Issues</h5>", unsafe_allow_html=True)
                for issue in fk_report["issues"]:
                    st.markdown(
                        f"- **{issue['missing_count']}** of {issue['total_rows']} rows reference "
                        f"`{issue['column']}` values not found in the **{issue['parent_table']}** table."
                    )
                    sample = ", ".join(f"`{v}`" for v in issue["sample_values"][:8])
                    remaining = len(issue["sample_values"]) - 8
                    if remaining > 0:
                        sample += f", … +{remaining} more"
                    st.caption(f"Sample missing values: {sample}")
                    fk_invalid_indices.update(issue["invalid_indices"])

        # ── 4. User action choice ──
        st.markdown("### Preprocessing & Upload Options")

        auto_clean = st.checkbox(
            "Auto-clean data before upload (handles missing values, standardises data format)",
            value=True
        )

        fk_action = "exclude"
        if fk_report["has_issues"]:
            fk_action = st.radio(
                "How should rows with invalid foreign keys be handled?",
                ["exclude", "cancel"],
                format_func=lambda x: {
                    "exclude": f"Exclude {len(fk_invalid_indices)} rows with invalid foreign keys (proceed with remaining)",
                    "cancel": "Cancel upload — fix the source file first",
                }[x],
                index=0,
            )

        act_col1, act_col2 = st.columns(2)
        with act_col1:
            confirm_btn = st.button(
                "Confirm Upload",
                type="primary",
                disabled=(fk_action == "cancel"),
                use_container_width=True,
            )
        with act_col2:
            cancel_btn = st.button("Cancel Upload", use_container_width=True)

        if cancel_btn:
            if "upload_pending" in st.session_state:
                del st.session_state["upload_pending"]
            st.info("Upload cancelled. Return to **Data Upload** to start again.", icon=":material/info:")
            st.stop()

        if confirm_btn:
            upload_df = work_df.copy()

            # ── Step 1: Exclude FK-invalid rows ──
            fk_excluded_count = 0
            if fk_invalid_indices:
                fk_excluded_count = len(fk_invalid_indices)
                upload_df = upload_df.drop(index=list(fk_invalid_indices), errors="ignore")
                st.info(
                    f"Excluded {fk_excluded_count} row(s) with invalid foreign key references.",
                    icon=":material/link_off:"
                )

            # ── Step 2: Classify and filter rows with missing PKs/ID refs ──
            upload_df, excluded_df, filter_report = classify_and_filter(upload_df, target_table)
            pk_excluded_count = filter_report["excluded_rows"]
            if pk_excluded_count > 0:
                st.info(
                    f"Excluded {pk_excluded_count} row(s) with missing primary key or required ID fields.",
                    icon=":material/filter_alt:"
                )

            # ── Step 3: Auto-clean (type-aware) ──
            if auto_clean and len(upload_df) > 0:
                upload_df, clean_report = clean_data(upload_df, target_table)
                for action in clean_report["actions"]:
                    st.info(f"Clean action: {action}")

            # ── Step 4: Insert into database ──
            total_rows = len(upload_df)
            total_original = len(raw_df)

            if total_rows == 0:
                total_excluded = fk_excluded_count + pk_excluded_count
                st.error(
                    f"Upload failed — all {total_original} rows were excluded. "
                    f"No records were inserted into **{target_table}**.",
                    icon=":material/cancel:"
                )
                # Show exclusion breakdown
                if filter_report["exclusion_reasons"]:
                    with st.expander(f"View {pk_excluded_count} rows excluded (missing IDs)", expanded=False):
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
                skip_reasons = []

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
                        if "UNIQUE constraint failed" in err_msg:
                            field = err_msg.split("UNIQUE constraint failed: ")[-1].strip()
                            skip_reasons.append((idx + 1, f"Duplicate {field}"))
                        elif "NOT NULL constraint failed" in err_msg:
                            field = err_msg.split("NOT NULL constraint failed: ")[-1].strip()
                            skip_reasons.append((idx + 1, f"Missing required field: {field}"))
                        elif "FOREIGN KEY constraint failed" in err_msg:
                            skip_reasons.append((idx + 1, f"Foreign key constraint failed (referenced ID not in parent table)"))
                        else:
                            skip_reasons.append((idx + 1, err_msg))

                    if (i + 1) % batch_size == 0 or (i + 1) == total_rows:
                        progress_pct = float(i + 1) / total_rows
                        progress_bar.progress(progress_pct, text=f"Processing: {i+1}/{total_rows} rows...")

                conn.commit()
                conn.close()
                progress_bar.empty()

                # ── Step 5: Result banners ──
                total_excluded = fk_excluded_count + pk_excluded_count

                if inserted == total_original and skipped == 0 and total_excluded == 0:
                    st.toast(f"Successfully uploaded {inserted} records to {target_table.title()}!", icon="✅")
                    st.success(
                        f"Upload complete! {inserted} records added to **{target_table}**.",
                        icon=":material/check_circle:"
                    )
                    log_activity(
                        user["user_id"], user["username"],
                        "DATA_UPLOAD",
                        f"Uploaded {inserted} records to {target_table} from {file_name}"
                    )
                elif inserted == 0:
                    st.error(
                        f"Upload failed — 0 of {total_original} records were inserted into **{target_table}**. See reasons below.",
                        icon=":material/cancel:"
                    )
                    log_activity(
                        user["user_id"], user["username"],
                        "DATA_UPLOAD",
                        f"Upload FAILED: 0 of {total_original} records inserted to {target_table} from {file_name}"
                    )
                else:
                    total_not_inserted = skipped + total_excluded
                    st.warning(
                        f"Upload partially completed — {inserted} of {total_original} records added to **{target_table}**, "
                        f"{total_not_inserted} skipped.",
                        icon=":material/warning:"
                    )
                    log_activity(
                        user["user_id"], user["username"],
                        "DATA_UPLOAD",
                        f"Partial upload: {inserted} of {total_original} records to {target_table} from {file_name} ({total_not_inserted} skipped)"
                    )

                # Upload Summary
                with st.container(border=True):
                    st.markdown("#### Upload Summary")
                    s1, s2, s3, s4, s5 = st.columns(5)
                    s1.metric("Total Rows", total_original)
                    s2.metric("Inserted", inserted)
                    s3.metric("Skipped (Insert)", skipped)
                    s4.metric("Excluded (Invalid ID)", pk_excluded_count)
                    s5.metric("Excluded (Invalid FK)", fk_excluded_count)

                # Expandable skip reasons
                all_reasons = filter_report["exclusion_reasons"] + skip_reasons
                if fk_excluded_count > 0:
                    all_reasons.insert(0, (0, f"{fk_excluded_count} rows excluded — foreign key references not found in parent table"))
                if all_reasons:
                    with st.expander(f"View {len(all_reasons)} Skipped/Excluded Row Details", expanded=False):
                        if fk_excluded_count > 0:
                            st.markdown(f"**Excluded before insert (invalid foreign keys): {fk_excluded_count} rows**")
                            for issue in fk_report["issues"]:
                                sample = ", ".join(f"`{v}`" for v in issue["sample_values"][:5])
                                st.markdown(f"- `{issue['column']}` → {issue['missing_count']} rows (e.g. {sample})")
                        if filter_report["exclusion_reasons"]:
                            st.markdown(f"**Excluded before insert (missing IDs): {pk_excluded_count} rows**")
                            for row_idx, reason in filter_report["exclusion_reasons"][:30]:
                                st.markdown(f"- **Row {row_idx + 1}**: {reason}")
                            if len(filter_report["exclusion_reasons"]) > 30:
                                st.caption(f"… and {len(filter_report['exclusion_reasons']) - 30} more.")
                        if skip_reasons:
                            st.markdown(f"**Skipped during insert: {skipped} rows**")
                            for row_num, reason in skip_reasons[:30]:
                                st.markdown(f"- **Row {row_num}**: {reason}")
                            if len(skip_reasons) > 30:
                                st.caption(f"… and {len(skip_reasons) - 30} more.")

            # Clear the pending upload after processing
            if "upload_pending" in st.session_state:
                del st.session_state["upload_pending"]


# ═══════════════════════════════════════════════
# Tab 1: Auto Cleaning (existing — works on DB data)
# ═══════════════════════════════════════════════
with tab1:
    st.markdown("### Automatic Data Cleaning")
    st.markdown("Handles missing values, duplicates, invalid balances, and data types.")

    if customers_df.empty:
        st.warning("No customer data available. Please upload data first.", icon=":material/warning:")
    else:
        st.markdown("#### Current Data Quality")
        quality = get_data_quality_report(customers_df)

        q1, q2, q3, q4 = st.columns(4)
        with q1:
            st.metric("Rows", quality["shape"]["rows"])
        with q2:
            st.metric("Columns", quality["shape"]["columns"])
        with q3:
            st.metric("Duplicates", quality["duplicates"])
        with q4:
            total_missing = sum(v["count"] for v in quality["missing"].values())
            st.metric("Missing Values", total_missing)

        if st.button("Run Auto-Clean", type="primary", use_container_width=True):
            with st.spinner("Cleaning data..."):
                cleaned_df, report = clean_data(customers_df)

                st.markdown("#### Cleaning Report")
                if report["actions"]:
                    for action in report["actions"]:
                        st.info(f"{action}")
                else:
                    st.success("Data is already clean — no actions needed!")

                c1, c2 = st.columns(2)
                with c1:
                    st.metric("Rows Before", report["original_rows"])
                with c2:
                    st.metric("Rows After", report["cleaned_rows"])

                st.markdown("#### Cleaned Data Preview")
                st.dataframe(cleaned_df.head(50), use_container_width=True)

                # Store in session
                st.session_state["preprocessed_df"] = cleaned_df

# ═══════════════════════════════════════════════
# Tab 2: Feature Engineering (existing — unchanged)
# ═══════════════════════════════════════════════
with tab2:
    st.markdown("### Feature Engineering")
    st.markdown("Generate derived features from existing data.")

    if customers_df.empty:
        st.warning("No customer data available. Please upload data first.", icon=":material/warning:")
    else:
        source_df = st.session_state.get("preprocessed_df", customers_df)

        features = st.multiselect(
            "Select Features to Generate",
            ["Age Group", "Income Category", "Balance Category", "Customer Tenure",
             "Customer Value Score", "All Features"],
            default=["All Features"]
        )

        if st.button("Generate Features", icon=":material/settings:", type="primary", use_container_width=True):
            with st.spinner("Engineering features..."):
                result_df = source_df.copy()

                if "All Features" in features:
                    result_df = apply_all_features(result_df, transactions_df)
                else:
                    if "Age Group" in features:
                        result_df = create_age_group(result_df)
                    if "Income Category" in features:
                        result_df = create_income_category(result_df)
                    if "Balance Category" in features:
                        result_df = create_balance_category(result_df)
                    if "Customer Tenure" in features:
                        result_df = calculate_customer_tenure(result_df)
                    if "Customer Value Score" in features:
                        result_df = calculate_customer_tenure(result_df)
                        result_df = calculate_customer_value_score(result_df)

                new_cols = [c for c in result_df.columns if c not in source_df.columns]
                st.success(f"Generated {len(new_cols)} new features: {', '.join(new_cols)}")

                st.markdown("#### Preview with New Features")
                st.dataframe(result_df.head(50), use_container_width=True)

                st.session_state["preprocessed_df"] = result_df

# ═══════════════════════════════════════════════
# Tab 3: Encoding (existing — unchanged)
# ═══════════════════════════════════════════════
with tab3:
    st.markdown("### Categorical Encoding")

    if customers_df.empty:
        st.warning("No customer data available. Please upload data first.", icon=":material/warning:")
    else:
        source_df = st.session_state.get("preprocessed_df", customers_df)
        cat_cols = source_df.select_dtypes(include=['object', 'category']).columns.tolist()

        if not cat_cols:
            st.info("No categorical columns found.")
        else:
            method = st.radio("Encoding Method", ["Label Encoding", "One-Hot Encoding"])
            selected_cols = st.multiselect("Select Columns to Encode", cat_cols, default=cat_cols[:3])

            if selected_cols and st.button("Apply Encoding", icon=":material/font_download:", type="primary"):
                with st.spinner("Encoding..."):
                    enc_method = "label" if method == "Label Encoding" else "onehot"
                    encoded_df, encoders = encode_features(source_df, enc_method, selected_cols)

                    st.success(f"{method} applied to {len(selected_cols)} columns")
                    st.dataframe(encoded_df.head(50), use_container_width=True)
                    st.session_state["preprocessed_df"] = encoded_df

# ═══════════════════════════════════════════════
# Tab 4: Scaling (existing — unchanged)
# ═══════════════════════════════════════════════
with tab4:
    st.markdown("### Feature Scaling")

    if customers_df.empty:
        st.warning("No customer data available. Please upload data first.", icon=":material/warning:")
    else:
        source_df = st.session_state.get("preprocessed_df", customers_df)
        num_cols = source_df.select_dtypes(include=['float64', 'int64']).columns.tolist()

        if not num_cols:
            st.info("No numeric columns found.")
        else:
            method = st.radio("Scaling Method", ["StandardScaler", "MinMaxScaler"])
            selected_cols = st.multiselect("Select Columns to Scale", num_cols, default=num_cols[:4])

            if selected_cols and st.button("Apply Scaling", icon=":material/straighten:", type="primary"):
                with st.spinner("Scaling..."):
                    sc_method = "standard" if method == "StandardScaler" else "minmax"
                    scaled_df, scaler = scale_features(source_df, sc_method, selected_cols)

                    st.success(f"{method} applied to {len(selected_cols)} columns")

                    before_after = pd.DataFrame({
                        "Column": selected_cols,
                        "Original Mean": [source_df[c].mean() for c in selected_cols],
                        "Original Std": [source_df[c].std() for c in selected_cols],
                        "Scaled Mean": [scaled_df[c].mean() for c in selected_cols],
                        "Scaled Std": [scaled_df[c].std() for c in selected_cols],
                    })
                    st.dataframe(before_after, use_container_width=True)
                    st.session_state["preprocessed_df"] = scaled_df