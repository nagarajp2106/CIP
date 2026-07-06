"""
Customer Segmentation Page — KMeans clustering with PCA visualization.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from sklearn.decomposition import PCA
from authentication import check_auth, require_role
from database import get_connection
from utils.prediction import load_model, train_segmentation_model
from utils.visualization import kpi_card, create_bar_chart, create_radar_chart, create_pie_chart, apply_layout

# ── Auth ──
user = check_auth()
if not user:
    st.switch_page("app.py")
require_role("Customer Segmentation")

st.markdown("# 🎯 Customer Segmentation")
st.markdown("AI-powered customer clustering using KMeans algorithm")
st.markdown("---")

conn = get_connection()
customers_df = pd.read_sql("SELECT * FROM customers", conn)
conn.close()

if customers_df.empty:
    st.warning("⚠️ No customer data available.")
    st.stop()

# Load or train model
model_data = load_model("segmentation")
if model_data is None:
    with st.spinner("🤖 Training segmentation model..."):
        model_data, X_scaled, features = train_segmentation_model(customers_df)

if model_data is None:
    st.error("❌ Failed to train segmentation model. Check data quality.")
    st.stop()

model = model_data["model"]
scaler = model_data["scaler"]
features = model_data["features"]
segment_labels = model_data["labels"]

# Apply segmentation
X = customers_df[features].fillna(0)
X_scaled = scaler.transform(X)
customers_df["cluster"] = model.predict(X_scaled)
customers_df["segment"] = customers_df["cluster"].map(segment_labels)

# ── KPI Cards ──
segment_counts = customers_df["segment"].value_counts()
k_cols = st.columns(5)
colors = ["purple", "blue", "gold", "orange", "red"]
for i, (seg, count) in enumerate(segment_counts.items()):
    with k_cols[i % 5]:
        st.markdown(kpi_card(seg, f"{count:,}", "🏷️", color=colors[i % 5]), unsafe_allow_html=True)

st.markdown("---")

# ── Visualizations ──
c1, c2 = st.columns(2)

with c1:
    # PCA 2D Projection
    pca = PCA(n_components=2)
    pca_result = pca.fit_transform(X_scaled)
    pca_df = pd.DataFrame(pca_result, columns=["PC1", "PC2"])
    pca_df["Segment"] = customers_df["segment"].values

    fig = px.scatter(pca_df, x="PC1", y="PC2", color="Segment",
                     opacity=0.6, title="🔬 PCA Cluster Projection")
    fig = apply_layout(fig, "🔬 PCA Cluster Projection", 450)
    st.plotly_chart(fig, use_container_width=True)

with c2:
    # Segment distribution
    seg_dist = customers_df["segment"].value_counts().reset_index()
    seg_dist.columns = ["segment", "count"]
    fig = create_pie_chart(seg_dist, "segment", "count", "📊 Customer Distribution by Segment", hole=0.4)
    st.plotly_chart(fig, use_container_width=True)

# Segment Profiles
st.markdown("---")
st.markdown("### 📋 Segment Profiles")
profile = customers_df.groupby("segment")[features].mean().round(2)
st.dataframe(profile, use_container_width=True)

# Radar chart for segment comparison
st.markdown("### 🎯 Segment Comparison")
seg_select = st.selectbox("Select Segment", list(segment_labels.values()))
seg_data = customers_df[customers_df["segment"] == seg_select]

if not seg_data.empty:
    # Normalize values for radar chart
    avg_vals = seg_data[features].mean()
    overall_max = customers_df[features].max()
    normalized = (avg_vals / overall_max * 100).tolist()
    fig = create_radar_chart(features, normalized, f"🎯 {seg_select} Profile")
    st.plotly_chart(fig, use_container_width=True)

# Retrain button
if user["role"] in ["admin", "data_analyst"]:
    st.markdown("---")
    if st.button("🔄 Retrain Model", type="primary"):
        with st.spinner("Retraining..."):
            model_data, _, _ = train_segmentation_model(customers_df)
            st.success("✅ Model retrained successfully!")
            st.rerun()
