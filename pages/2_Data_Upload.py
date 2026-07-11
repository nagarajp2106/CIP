"""
Data Upload Page — CSV upload, validation, preview, and database insertion.
"""
import streamlit as st
from utils.icons import render_html_icon
import pandas as pd
from authentication import check_auth, require_role
from database import get_connection
from utils.preprocessing import validate_upload, clean_data, get_data_quality_report
from utils.auth import log_activity

# ── Auth ──
user = check_auth()
if not user:
    st.switch_page("app.py")
require_role("Data Upload")

st.markdown(f"# {render_html_icon('upload_file', size='30px')} Data Upload", unsafe_allow_html=True)
st.markdown("Upload, validate, and store banking datasets")
st.markdown("---")

# ── Table Selection ──
target_table = st.selectbox(
    "Select Target Table",
    ["customers", "accounts", "transactions", "loans", "cards"],
    format_func=lambda x: x.title()
)

# ── File Upload ──
uploaded_file = st.file_uploader(
    "Upload CSV File",
    type=["csv"],
    help="Upload a CSV file with data matching the selected table schema."
)

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        st.success(f"File loaded: **{uploaded_file.name}** ({len(df)} rows, {len(df.columns)} columns)")

        # ── Tabs ──
        tab1, tab2, tab3, tab4 = st.tabs([":material/preview: Preview", ":material/check_circle: Validation", ":material/search: Quality Report", ":material/upload: Upload"])

        with tab1:
            st.markdown("### Data Preview (First 100 Rows)")
            st.dataframe(df.head(100), use_container_width=True, height=400)

            with st.expander(":material/analytics: Column Info"):
                col_info = pd.DataFrame({
                    "Column": df.columns,
                    "Type": df.dtypes.values,
                    "Non-Null": df.notna().sum().values,
                    "Null": df.isna().sum().values,
                    "Null %": (df.isna().sum() / len(df) * 100).round(2).values,
                    "Unique": df.nunique().values
                })
                st.dataframe(col_info, use_container_width=True)

        with tab2:
            st.markdown("### Validation Report")
            report = validate_upload(df, target_table)

            if report["valid"]:
                st.success("**Validation Passed** — Data is ready for upload", icon=":material/check_circle:")
            else:
                st.error("**Validation Failed** — Fix errors before uploading", icon=":material/cancel:")

            if report["errors"]:
                st.markdown(f"#### {render_html_icon('cancel', size='20px', color='var(--danger)')} Errors", unsafe_allow_html=True)
                for err in report["errors"]:
                    st.markdown(f"- {render_html_icon('error', size='16px', color='var(--danger)')} {err}", unsafe_allow_html=True)

            if report["warnings"]:
                st.markdown(f"#### {render_html_icon('warning', size='20px', color='var(--warning)')} Warnings", unsafe_allow_html=True)
                for warn in report["warnings"]:
                    st.markdown(f"- {render_html_icon('warning', size='16px', color='var(--warning)')} {warn}", unsafe_allow_html=True)

            if report["info"]:
                st.markdown("#### ℹ️ Info")
                for info in report["info"]:
                    st.markdown(f"- {render_html_icon('info', size='16px', color='var(--info)')} {info}", unsafe_allow_html=True)

        with tab3:
            st.markdown("### Data Quality Report")
            quality = get_data_quality_report(df)

            q1, q2, q3 = st.columns(3)
            with q1:
                st.metric("Rows", quality["shape"]["rows"])
            with q2:
                st.metric("Columns", quality["shape"]["columns"])
            with q3:
                st.metric("Duplicates", quality["duplicates"])

            if quality["numeric_summary"]:
                st.markdown("#### Numeric Columns Summary")
                summary_df = pd.DataFrame(quality["numeric_summary"]).T
                st.dataframe(summary_df, use_container_width=True)

            st.markdown("#### Missing Values")
            missing_df = pd.DataFrame(quality["missing"]).T
            missing_df = missing_df[missing_df["count"] > 0]
            if not missing_df.empty:
                st.dataframe(missing_df, use_container_width=True)
            else:
                st.success("No missing values found!")

        with tab4:
            st.markdown("### Upload to Database")
            report = validate_upload(df, target_table)

            if not report["valid"]:
                st.warning("Please fix validation errors before uploading.", icon=":material/warning:")
            else:
                auto_clean = st.checkbox("Auto-clean data before upload", value=True)

                col_map_expander = st.expander(":material/build: Column Mapping (optional)")
                with col_map_expander:
                    st.info("Columns will be matched by name (case-insensitive). Rename columns here if needed.")

                if st.button("Upload to Database", icon=":material/upload:", type="primary", use_container_width=True):
                    with st.spinner("Processing..."):
                        upload_df = df.copy()

                        # Standardize column names
                        upload_df.columns = [c.lower().replace(" ", "_") for c in upload_df.columns]

                        # Auto-clean if enabled
                        if auto_clean:
                            upload_df, clean_report = clean_data(upload_df)
                            for action in clean_report["actions"]:
                                st.info(f"{action}")

                        # Insert into database
                        conn = get_connection()
                        inserted = 0
                        skipped = 0

                        for _, row in upload_df.iterrows():
                            try:
                                row_dict = row.to_dict()
                                cols = ", ".join(row_dict.keys())
                                placeholders = ", ".join(["?"] * len(row_dict))
                                conn.execute(
                                    f"INSERT OR IGNORE INTO {target_table} ({cols}) VALUES ({placeholders})",
                                    list(row_dict.values())
                                )
                                inserted += 1
                            except Exception:
                                skipped += 1

                        conn.commit()
                        conn.close()

                        # Summary
                        st.markdown(f"### {render_html_icon('analytics', size='22px')} Upload Summary", unsafe_allow_html=True)
                        s1, s2, s3 = st.columns(3)
                        with s1:
                            st.metric("Total Rows", len(upload_df))
                        with s2:
                            st.metric("Inserted", inserted)
                        with s3:
                            st.metric("Skipped", skipped)

                        st.success(f"Upload complete! {inserted} records added to **{target_table}**.")

                        # Log activity
                        log_activity(
                            user["user_id"], user["username"],
                            "DATA_UPLOAD",
                            f"Uploaded {inserted} records to {target_table} from {uploaded_file.name}"
                        )

    except Exception as e:
        st.error(f"Error reading file: {str(e)}", icon=":material/cancel:")