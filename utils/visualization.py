"""
Visualization Utilities — Reusable Plotly chart builders with banking theme.
"""
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from config import CHART_COLORS, COLORS


# ──────────────────────────────────────────────
# Common Layout Config
# ──────────────────────────────────────────────
PLOTLY_LAYOUT = dict(
    font=dict(family="Inter, Segoe UI, -apple-system, sans-serif", size=12, color="#1B2A4A"),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="#F8FAFC",
    margin=dict(l=45, r=45, t=55, b=45),
    colorway=CHART_COLORS,
    hoverlabel=dict(bgcolor="#FFFFFF", font_size=13, font_family="Inter", bordercolor="#E2E8F0"),
    legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
)


def apply_layout(fig, title="", height=400):
    """Apply consistent banking theme layout to a Plotly figure."""
    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(text=f"<b>{title}</b>" if title else "", font=dict(size=15, color="#1B2A4A"), x=0.02, y=0.95, xanchor="left"),
        height=height,
    )
    fig.update_xaxes(showgrid=False, linecolor="#E2E8F0", title_font=dict(size=11, color="#64748B"), tickfont=dict(size=10, color="#64748B"))
    fig.update_yaxes(showgrid=True, gridcolor="#F1F5F9", linecolor="rgba(0,0,0,0)", title_font=dict(size=11, color="#64748B"), tickfont=dict(size=10, color="#64748B"))
    return fig


from utils.icons import render_html_icon

def kpi_card(title: str, value, icon: str = "", delta=None, delta_label="", color="blue") -> str:
    """
    Generate HTML for a styled KPI metric card.

    Args:
        title: Card title/label
        value: Display value (will be converted to string)
        icon: Emoji icon or Material Symbol name (optional)
        delta: Optional delta value (shows green/red indicator)
        delta_label: Label for delta
        color: Card accent color (blue, gold, green, red, teal, purple, orange)
    """
    delta_html = ""
    if delta is not None:
        delta_class = "positive" if delta >= 0 else "negative"
        delta_symbol = "↑" if delta >= 0 else "↓"
        delta_html = f'<div class="kpi-delta {delta_class}">{delta_symbol} {abs(delta):.1f}% {delta_label}</div>'
    else:
        # Invisible spacer of the same height to preserve vertical alignment across cards
        delta_html = '<div class="kpi-delta" style="visibility: hidden; background: transparent;">&nbsp;</div>'

    icon_html = ""
    if icon:
        icon_html = f'<div class="kpi-icon">{render_html_icon(icon, size="2.5rem")}</div>'

    return f"""
    <div class="kpi-card {color} animate-in">
        {icon_html}
        <div class="kpi-value">{value}</div>
        <div class="kpi-label">{title}</div>
        {delta_html}
    </div>
    """


# ──────────────────────────────────────────────
# Chart Builders
# ──────────────────────────────────────────────

def create_line_chart(df, x, y, title="", color=None, height=400):
    """Create a styled line chart."""
    fig = px.line(df, x=x, y=y, color=color, markers=True)
    fig.update_traces(line=dict(width=2.5))
    return apply_layout(fig, title, height)


def create_area_chart(df, x, y, title="", color=None, height=400):
    """Create a styled area chart."""
    fig = px.area(df, x=x, y=y, color=color)
    fig.update_traces(line=dict(width=2))
    return apply_layout(fig, title, height)


def create_bar_chart(df, x, y, title="", color=None, barmode="group", orientation="v", height=400):
    """Create a styled bar chart."""
    fig = px.bar(df, x=x, y=y, color=color, barmode=barmode, orientation=orientation)
    fig.update_traces(marker=dict(cornerradius=4))
    return apply_layout(fig, title, height)


def create_horizontal_bar(df, x, y, title="", color=None, height=400):
    """Create a styled horizontal bar chart."""
    fig = px.bar(df, x=x, y=y, color=color, orientation="h")
    fig.update_traces(marker=dict(cornerradius=4))
    fig.update_layout(yaxis=dict(categoryorder="total ascending"))
    return apply_layout(fig, title, height)


def create_pie_chart(df, names, values, title="", hole=0, height=400):
    """Create a styled pie/donut chart."""
    fig = px.pie(df, names=names, values=values, hole=hole)
    fig.update_traces(
        textposition="inside", textinfo="percent+label",
        marker=dict(line=dict(color="white", width=2))
    )
    return apply_layout(fig, title, height)


def create_donut_chart(df, names, values, title="", height=400):
    """Create a styled donut chart."""
    return create_pie_chart(df, names, values, title, hole=0.45, height=height)


def create_histogram(df, x, title="", nbins=30, color=None, height=400):
    """Create a styled histogram."""
    fig = px.histogram(df, x=x, nbins=nbins, color=color, marginal="box")
    fig.update_traces(marker=dict(cornerradius=4))
    return apply_layout(fig, title, height)


def create_scatter(df, x, y, title="", color=None, size=None, height=400):
    """Create a styled scatter plot."""
    fig = px.scatter(df, x=x, y=y, color=color, size=size, opacity=0.7)
    return apply_layout(fig, title, height)


def create_box_plot(df, x, y, title="", color=None, height=400):
    """Create a styled box plot."""
    fig = px.box(df, x=x, y=y, color=color)
    return apply_layout(fig, title, height)


def create_heatmap(data, x_labels, y_labels, title="", height=400):
    """Create a styled heatmap from a 2D array."""
    fig = go.Figure(data=go.Heatmap(
        z=data, x=x_labels, y=y_labels,
        colorscale=[[0, "#F0F4F8"], [0.5, "#2E86AB"], [1, "#1B2A4A"]],
        hoverongaps=False
    ))
    return apply_layout(fig, title, height)


def create_correlation_matrix(df, title="Correlation Matrix", height=500):
    """Create a correlation matrix heatmap."""
    numeric_df = df.select_dtypes(include=[np.number])
    corr = numeric_df.corr()
    fig = go.Figure(data=go.Heatmap(
        z=corr.values,
        x=corr.columns.tolist(),
        y=corr.columns.tolist(),
        colorscale="RdBu_r",
        zmid=0,
        text=np.round(corr.values, 2),
        texttemplate="%{text}",
        textfont=dict(size=10),
        hoverongaps=False
    ))
    return apply_layout(fig, title, height)


def create_gauge(value, title="", min_val=0, max_val=100, height=300):
    """Create a gauge chart for scores/percentages."""
    # Determine color based on value position
    if value < max_val * 0.33:
        bar_color = COLORS["danger"]
    elif value < max_val * 0.66:
        bar_color = COLORS["warning"]
    else:
        bar_color = COLORS["success"]

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        title=dict(text=title, font=dict(size=14)),
        gauge=dict(
            axis=dict(range=[min_val, max_val], tickwidth=1),
            bar=dict(color=bar_color),
            bgcolor="white",
            borderwidth=2,
            bordercolor="#E9ECEF",
            steps=[
                dict(range=[min_val, max_val*0.33], color="#FFEBEE"),
                dict(range=[max_val*0.33, max_val*0.66], color="#FFF8E1"),
                dict(range=[max_val*0.66, max_val], color="#E8F5E9"),
            ],
        )
    ))
    return apply_layout(fig, "", height)


def create_sunburst(df, path, values, title="", height=450):
    """Create a styled sunburst chart."""
    fig = px.sunburst(df, path=path, values=values)
    return apply_layout(fig, title, height)


def create_treemap(df, path, values, title="", height=450):
    """Create a styled treemap."""
    fig = px.treemap(df, path=path, values=values)
    return apply_layout(fig, title, height)


def create_violin(df, x, y, title="", color=None, height=400):
    """Create a styled violin plot."""
    fig = px.violin(df, x=x, y=y, color=color, box=True, points="outliers")
    return apply_layout(fig, title, height)


def create_radar_chart(categories, values, title="", height=400):
    """Create a radar/spider chart for multi-dimensional comparison."""
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]],
        theta=categories + [categories[0]],
        fill="toself",
        fillcolor="rgba(46, 134, 171, 0.2)",
        line=dict(color=COLORS["secondary"], width=2),
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, max(values) * 1.1]),
            bgcolor="#FAFBFC"
        ),
    )
    return apply_layout(fig, title, height)


# ──────────────────────────────────────────────
# Prediction Result HTML
# ──────────────────────────────────────────────

def prediction_result_card(label: str, value: str, score: float, css_class: str = "") -> str:
    """Generate HTML for a prediction result display card."""
    return f"""
    <div class="prediction-result animate-in">
        <div class="prediction-label">{label}</div>
        <div class="prediction-value {css_class}">{value}</div>
        <div class="prediction-score">Confidence: {score:.1%}</div>
    </div>
    """


def progress_bar_html(value: float, max_val: float = 100, color: str = "#2E86AB", label: str = "") -> str:
    """Generate HTML for a styled progress bar."""
    pct = min((value / max_val) * 100, 100) if max_val > 0 else 0
    return f"""
    <div style="margin: 0.3rem 0;">
        <div style="display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 4px;">
            <span style="color: #1B2A4A; font-weight: 500;">{label}</span>
            <span style="color: #6C757D;">{value:.1f}%</span>
        </div>
        <div class="progress-container">
            <div class="progress-bar" style="width: {pct}%; background: {color};">{pct:.0f}%</div>
        </div>
    </div>
    """
