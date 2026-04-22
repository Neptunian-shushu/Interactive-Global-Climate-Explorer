from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from sklearn.linear_model import LinearRegression

from .config import DEFAULT_PATHS, DISPLAY_CLASS_ORDER, DISPLAY_CLASS_STYLES, ProjectPaths

CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ---- Global ---- */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    [data-testid="stAppViewContainer"] {
        background: #f8fafc;
    }
    [data-testid="stHeader"] {
        background: rgba(248,250,252,0.95);
        backdrop-filter: blur(8px);
    }

    /* ---- Sidebar ---- */
    section[data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid #e2e8f0;
    }
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stCheckbox label {
        color: #64748b !important;
        font-size: 0.78rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* ---- Hero banner ---- */
    .hero-banner {
        background: linear-gradient(135deg, #0f766e 0%, #1e40af 100%);
        border-radius: 16px;
        padding: 36px 44px 30px;
        margin-bottom: 28px;
        position: relative;
        overflow: hidden;
    }
    .hero-banner::before {
        content: '';
        position: absolute;
        top: -60%;
        right: -15%;
        width: 420px;
        height: 420px;
        background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%);
        border-radius: 50%;
    }
    .hero-banner h1 {
        color: #ffffff;
        font-size: 2.1rem;
        font-weight: 800;
        margin: 0 0 8px 0;
        letter-spacing: -0.025em;
        position: relative;
    }
    .hero-banner p {
        color: rgba(255,255,255,0.82);
        font-size: 0.95rem;
        margin: 0;
        font-weight: 400;
        max-width: 720px;
        line-height: 1.55;
        position: relative;
    }

    /* ---- Metrics ---- */
    div[data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px 18px 14px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.03);
    }
    div[data-testid="stMetric"] label {
        color: #64748b !important;
        font-size: 0.7rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #0f172a !important;
        font-size: 1.4rem !important;
        font-weight: 700 !important;
    }

    /* ---- Region header card ---- */
    .region-header-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 24px 28px 20px;
        margin-bottom: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.03);
    }
    .region-header-card h2 {
        color: #0f172a;
        font-size: 1.25rem;
        font-weight: 700;
        margin: 0 0 10px 0;
        letter-spacing: -0.01em;
    }
    .climate-badge {
        display: inline-block;
        padding: 5px 16px;
        border-radius: 20px;
        font-size: 0.84rem;
        font-weight: 600;
    }
    .region-explanation {
        color: #475569;
        font-size: 0.88rem;
        line-height: 1.6;
        margin-top: 14px;
    }

    /* ---- Map card ---- */
    .map-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 20px 20px 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.03);
    }
    .section-label {
        color: #64748b;
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin: 0 0 12px 0;
    }

    /* ---- Legend ---- */
    .legend-row {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        margin-top: 12px;
    }
    .legend-chip {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 500;
        color: #334155;
        background: #f1f5f9;
        border: 1px solid #e2e8f0;
    }
    .legend-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        display: inline-block;
        flex-shrink: 0;
    }

    /* ---- Chart card ---- */
    .chart-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }

    /* ---- Comparison cards ---- */
    .compare-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 20px 22px 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .compare-card h4 {
        color: #0f172a;
        font-size: 0.95rem;
        font-weight: 700;
        margin: 0 0 4px 0;
    }
    .compare-card .climate-type {
        font-size: 0.82rem;
        font-weight: 600;
        margin-bottom: 12px;
    }
    .compare-stat {
        display: flex;
        justify-content: space-between;
        padding: 8px 0;
        border-bottom: 1px solid #f1f5f9;
    }
    .compare-stat:last-child {
        border-bottom: none;
    }
    .compare-stat-label {
        color: #64748b;
        font-size: 0.78rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .compare-stat-value {
        color: #0f172a;
        font-size: 0.9rem;
        font-weight: 700;
    }

    /* ---- Download button ---- */
    section[data-testid="stSidebar"] .stDownloadButton button {
        background: #0f766e !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        padding: 10px 20px !important;
        width: 100%;
    }
    section[data-testid="stSidebar"] .stDownloadButton button:hover {
        background: #0d9488 !important;
    }

    /* ---- Hide default streamlit branding ---- */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
"""

CHART_COLORS = dict(
    temp_line="#dc2626",
    temp_trend="#f59e0b",
    precip_bar="#60a5fa",
    precip_line="#2563eb",
    precip_trend="#f97316",
    annual_temp="#4f46e5",
    grid="#f1f5f9",
    text="#64748b",
    title="#334155",
)


@st.cache_data(show_spinner="Loading climate data...")
def load_outputs(paths: ProjectPaths = DEFAULT_PATHS) -> tuple[dict, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    with paths.climate_regions.open("r", encoding="utf-8") as fh:
        geojson = json.load(fh)
    region_summary = pd.read_parquet(paths.region_summary)
    monthly_2025 = pd.read_parquet(paths.region_monthly_2025)
    yearly = pd.read_parquet(paths.region_yearly)
    with paths.app_config.open("r", encoding="utf-8") as fh:
        config = json.load(fh)
    return geojson, region_summary, monthly_2025, yearly, config


def _chart_layout(title: str, height: int, legend_y: float = 1.12) -> dict:
    return dict(
        title=dict(text=title, font=dict(size=13, color=CHART_COLORS["title"]), x=0.0, y=0.97),
        margin=dict(l=8, r=8, t=44, b=8),
        legend=dict(orientation="h", y=legend_y, font=dict(size=10, color=CHART_COLORS["text"])),
        height=height,
        font=dict(family="Inter, sans-serif", color=CHART_COLORS["text"], size=11),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        xaxis=dict(tickfont=dict(size=10), gridcolor=CHART_COLORS["grid"], showline=True, linecolor="#e2e8f0"),
        yaxis=dict(tickfont=dict(size=10), gridcolor=CHART_COLORS["grid"], showline=True, linecolor="#e2e8f0"),
    )


def build_map_figure(
    geojson: dict,
    region_summary: pd.DataFrame,
    highlight_class: str | None = None,
    selected_ids: set[str] | None = None,
) -> go.Figure:
    color_map = {name: DISPLAY_CLASS_STYLES[name]["color"] for name in DISPLAY_CLASS_ORDER}

    if highlight_class and highlight_class != "All":
        opacities = [
            1.0 if row["display_climate_name"] == highlight_class else 0.18
            for _, row in region_summary.iterrows()
        ]
    else:
        opacities = [1.0] * len(region_summary)

    line_widths = []
    line_colors = []
    for _, row in region_summary.iterrows():
        if selected_ids and row["region_id"] in selected_ids:
            line_widths.append(3.0)
            line_colors.append("#0f172a")
        else:
            line_widths.append(0.5)
            line_colors.append("#ffffff")

    fig = go.Figure(
        go.Choropleth(
            geojson=geojson,
            locations=region_summary["region_id"],
            z=region_summary["display_climate_name"].map(
                {name: idx for idx, name in enumerate(DISPLAY_CLASS_ORDER)}
            ),
            featureidkey="properties.region_id",
            colorscale=[
                [i / max(len(DISPLAY_CLASS_ORDER) - 1, 1), color_map[name]]
                for i, name in enumerate(DISPLAY_CLASS_ORDER)
            ],
            marker_line_width=line_widths,
            marker_line_color=line_colors,
            marker_opacity=opacities,
            customdata=region_summary[
                ["region_name", "display_climate_name", "annual_mean_temp_c", "annual_total_precip_mm"]
            ].values,
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "<i>%{customdata[1]}</i><br><br>"
                "Mean Temp: %{customdata[2]:.1f} C<br>"
                "Annual Precip: %{customdata[3]:.0f} mm"
                "<extra></extra>"
            ),
            showscale=False,
        )
    )
    fig.update_geos(
        fitbounds="locations",
        visible=False,
        showcountries=False,
        showcoastlines=True,
        coastlinecolor="#94a3b8",
        projection_type="mercator",
        bgcolor="rgba(0,0,0,0)",
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=520,
        font=dict(family="Inter, sans-serif"),
        hoverlabel=dict(
            bgcolor="#ffffff",
            bordercolor="#e2e8f0",
            font=dict(color="#0f172a", size=13, family="Inter, sans-serif"),
        ),
    )
    return fig


def build_monthly_chart(monthly: pd.DataFrame, region_name: str = "") -> go.Figure:
    month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    monthly = monthly.sort_values("month")
    fig = go.Figure()
    fig.add_bar(
        x=month_labels,
        y=monthly["mean_Rainf_mm"],
        name="Precipitation (mm)",
        marker_color=CHART_COLORS["precip_bar"],
        yaxis="y2",
        opacity=0.6,
    )
    fig.add_scatter(
        x=month_labels,
        y=monthly["mean_Tair_C"],
        name="Temperature (C)",
        mode="lines+markers",
        line=dict(color=CHART_COLORS["temp_line"], width=3),
        marker=dict(size=7, color=CHART_COLORS["temp_line"], line=dict(width=2, color="#ffffff")),
    )
    title = f"{region_name} - 2025 Monthly" if region_name else "2025 Monthly Temperature & Precipitation"
    layout = _chart_layout(title, 290)
    layout["yaxis"]["title"] = "Temp (C)"
    layout["yaxis2"] = dict(
        title="Precip (mm)", overlaying="y", side="right",
        titlefont=dict(size=11), tickfont=dict(size=10),
        gridcolor=CHART_COLORS["grid"], showline=True, linecolor="#e2e8f0",
    )
    fig.update_layout(**layout)
    return fig


def build_yearly_chart(yearly: pd.DataFrame, region_name: str = "", show_trend: bool = True) -> go.Figure:
    yearly = yearly.sort_values("year")
    fig = go.Figure()
    fig.add_bar(
        x=yearly["year"],
        y=yearly["annual_total_precip_mm"],
        name="Annual precip (mm)",
        marker_color=CHART_COLORS["precip_bar"],
        yaxis="y2",
        opacity=0.45,
    )
    fig.add_scatter(
        x=yearly["year"],
        y=yearly["annual_mean_temp_c"],
        name="Annual mean temp (C)",
        mode="lines",
        line=dict(color=CHART_COLORS["annual_temp"], width=3),
    )
    if show_trend and len(yearly) >= 3:
        X = yearly["year"].to_numpy().reshape(-1, 1)

        reg_temp = LinearRegression().fit(X, yearly["annual_mean_temp_c"].to_numpy())
        temp_trend = reg_temp.predict(X)
        temp_slope = reg_temp.coef_[0]
        temp_sign = "+" if temp_slope >= 0 else ""
        fig.add_scatter(
            x=yearly["year"], y=temp_trend,
            name=f"Temp trend ({temp_sign}{temp_slope:.3f} C/yr)",
            mode="lines",
            line=dict(color=CHART_COLORS["temp_trend"], width=2, dash="dash"),
        )

        reg_precip = LinearRegression().fit(X, yearly["annual_total_precip_mm"].to_numpy())
        precip_trend = reg_precip.predict(X)
        precip_slope = reg_precip.coef_[0]
        precip_sign = "+" if precip_slope >= 0 else ""
        fig.add_scatter(
            x=yearly["year"], y=precip_trend,
            name=f"Precip trend ({precip_sign}{precip_slope:.1f} mm/yr)",
            mode="lines",
            line=dict(color=CHART_COLORS["precip_trend"], width=2, dash="dash"),
            yaxis="y2",
        )

    title = f"{region_name} - 1996-2025 Annual" if region_name else "1996-2025 Annual Trend"
    layout = _chart_layout(title, 310, legend_y=1.22)
    layout["yaxis"]["title"] = "Temp (C)"
    layout["yaxis2"] = dict(
        title="Precip (mm)", overlaying="y", side="right",
        titlefont=dict(size=11), tickfont=dict(size=10),
        gridcolor=CHART_COLORS["grid"], showline=True, linecolor="#e2e8f0",
    )
    fig.update_layout(**layout)
    return fig


def build_comparison_chart(
    yearly_a: pd.DataFrame,
    yearly_b: pd.DataFrame,
    name_a: str,
    name_b: str,
) -> go.Figure:
    ya = yearly_a.sort_values("year")
    yb = yearly_b.sort_values("year")
    fig = go.Figure()
    fig.add_scatter(
        x=ya["year"], y=ya["annual_mean_temp_c"],
        name=name_a, mode="lines+markers",
        line=dict(color=CHART_COLORS["annual_temp"], width=2.5),
        marker=dict(size=4),
    )
    fig.add_scatter(
        x=yb["year"], y=yb["annual_mean_temp_c"],
        name=name_b, mode="lines+markers",
        line=dict(color=CHART_COLORS["temp_line"], width=2.5),
        marker=dict(size=4),
    )
    layout = _chart_layout("Temperature Comparison", 280)
    layout["yaxis"]["title"] = "Mean Temp (C)"
    fig.update_layout(**layout)
    return fig


def build_precip_comparison_chart(
    yearly_a: pd.DataFrame,
    yearly_b: pd.DataFrame,
    name_a: str,
    name_b: str,
) -> go.Figure:
    ya = yearly_a.sort_values("year")
    yb = yearly_b.sort_values("year")
    fig = go.Figure()
    fig.add_scatter(
        x=ya["year"], y=ya["annual_total_precip_mm"],
        name=name_a, mode="lines+markers",
        line=dict(color=CHART_COLORS["precip_line"], width=2.5),
        marker=dict(size=4),
    )
    fig.add_scatter(
        x=yb["year"], y=yb["annual_total_precip_mm"],
        name=name_b, mode="lines+markers",
        line=dict(color=CHART_COLORS["precip_trend"], width=2.5),
        marker=dict(size=4),
    )
    layout = _chart_layout("Precipitation Comparison", 280)
    layout["yaxis"]["title"] = "Total Precip (mm)"
    fig.update_layout(**layout)
    return fig


def infer_selected_region(selection_state: object) -> str | None:
    if not selection_state:
        return None
    if isinstance(selection_state, dict):
        points = selection_state.get("selection", {}).get("points") or selection_state.get("points")
    else:
        try:
            points = selection_state.selection.points
        except Exception:
            points = None
    if not points:
        return None
    point = points[0]
    if isinstance(point, dict):
        return point.get("location") or point.get("customdata", [None])[0]
    return getattr(point, "location", None)


def _render_region_panel(
    region: pd.Series,
    monthly_region: pd.DataFrame,
    yearly_region: pd.DataFrame,
    show_trend: bool,
) -> None:
    color = DISPLAY_CLASS_STYLES[region["display_climate_name"]]["color"]
    st.markdown(
        f"<div class='region-header-card' style='border-top: 3px solid {color};'>"
        f"<h2>{region['region_name']}</h2>"
        f"<span class='climate-badge' style='background:{color}18;color:{color};border:1px solid {color}40;'>"
        f"{region['display_climate_name']}</span>"
        f"<p class='region-explanation'>{region['explanation_short']}</p>"
        f"</div>",
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    c1.metric("Annual Mean Temp", f"{region['annual_mean_temp_c']:.1f} C")
    c2.metric("Annual Precip", f"{region['annual_total_precip_mm']:.0f} mm")
    c3, c4 = st.columns(2)
    c3.metric("Coldest Month", f"{region['coldest_month_temp_c']:.1f} C")
    c4.metric("Hottest Month", f"{region['hottest_month_temp_c']:.1f} C")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    short_name = region["region_name"].split(" - ", 1)[-1] if " - " in region["region_name"] else region["region_name"]
    st.plotly_chart(build_monthly_chart(monthly_region, short_name), use_container_width=True)
    st.plotly_chart(build_yearly_chart(yearly_region, short_name, show_trend=show_trend), use_container_width=True)


def _render_compare_card(region: pd.Series) -> None:
    color = DISPLAY_CLASS_STYLES[region["display_climate_name"]]["color"]
    st.markdown(
        f"<div class='compare-card' style='border-top: 3px solid {color};'>"
        f"<h4>{region['region_name']}</h4>"
        f"<div class='climate-type' style='color:{color};'>{region['display_climate_name']}</div>"
        f"<div class='compare-stat'><span class='compare-stat-label'>Mean Temp</span>"
        f"<span class='compare-stat-value'>{region['annual_mean_temp_c']:.1f} C</span></div>"
        f"<div class='compare-stat'><span class='compare-stat-label'>Precip</span>"
        f"<span class='compare-stat-value'>{region['annual_total_precip_mm']:.0f} mm</span></div>"
        f"<div class='compare-stat'><span class='compare-stat-label'>Coldest</span>"
        f"<span class='compare-stat-value'>{region['coldest_month_temp_c']:.1f} C</span></div>"
        f"<div class='compare-stat'><span class='compare-stat-label'>Hottest</span>"
        f"<span class='compare-stat-value'>{region['hottest_month_temp_c']:.1f} C</span></div>"
        f"</div>",
        unsafe_allow_html=True,
    )


def _region_csv(region_id: str, monthly: pd.DataFrame, yearly: pd.DataFrame) -> str:
    m = monthly[monthly["region_id"] == region_id].to_csv(index=False)
    y = yearly[yearly["region_id"] == region_id].to_csv(index=False)
    return f"### 2025 Monthly ###\n{m}\n### 1996-2025 Annual ###\n{y}"


def _render_legend(region_summary: pd.DataFrame) -> None:
    active_classes = set(region_summary["display_climate_name"])
    parts = []
    for name in DISPLAY_CLASS_ORDER:
        if name in active_classes:
            c = DISPLAY_CLASS_STYLES[name]["color"]
            parts.append(
                f"<span class='legend-chip'>"
                f"<span class='legend-dot' style='background:{c}'></span>"
                f"{name}</span>"
            )
    chips = "".join(parts)
    st.markdown(f"<div class='legend-row'>{chips}</div>", unsafe_allow_html=True)


def run_app(paths: ProjectPaths = DEFAULT_PATHS) -> None:
    st.set_page_config(
        page_title="Interactive Global Climate Explorer",
        page_icon="🌍",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    geojson, region_summary, monthly_2025, yearly, config = load_outputs(paths)
    region_ids = region_summary["region_id"].tolist()
    region_names = dict(zip(region_summary["region_id"], region_summary["region_name"]))

    if "selected_region_id" not in st.session_state:
        st.session_state["selected_region_id"] = config["default_selected_region"]

    # ---- Hero banner ----
    st.markdown(
        "<div class='hero-banner'>"
        "<h1>Interactive Global Climate Explorer</h1>"
        "<p>Explore North America's climate regions built from 30 years of NLDAS monthly data "
        "using Koppen-Geiger classification. Click any region on the map to inspect it.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    # ---- Sidebar ----
    with st.sidebar:
        st.markdown("### Filters")
        climate_classes = ["All"] + sorted(set(region_summary["display_climate_name"]))
        highlight_class = st.selectbox("Highlight climate type", climate_classes, index=0)
        show_trend = st.checkbox("Show trend lines", value=True)

        st.markdown("---")
        st.markdown("### Compare")
        compare_enabled = st.checkbox("Enable comparison mode")
        compare_a = st.selectbox(
            "Region A", region_ids,
            format_func=lambda rid: region_names.get(rid, rid),
            index=0,
        )
        compare_b = st.selectbox(
            "Region B", region_ids,
            format_func=lambda rid: region_names.get(rid, rid),
            index=min(1, len(region_ids) - 1),
        )

        st.markdown("---")
        st.markdown("### Export")
        export_region = st.selectbox(
            "Region to export", region_ids,
            format_func=lambda rid: region_names.get(rid, rid),
            key="export_select",
        )
        csv_data = _region_csv(export_region, monthly_2025, yearly)
        st.download_button(
            "Download CSV",
            data=csv_data,
            file_name=f"{export_region}_climate_data.csv",
            mime="text/csv",
        )

    # ---- Comparison mode ----
    if compare_enabled:
        selected_ids = {compare_a, compare_b}

        st.markdown("<div class='map-card'>", unsafe_allow_html=True)
        st.markdown("<p class='section-label'>Climate Region Map</p>", unsafe_allow_html=True)
        map_fig = build_map_figure(
            geojson, region_summary,
            highlight_class if highlight_class != "All" else None,
            selected_ids,
        )
        st.plotly_chart(map_fig, use_container_width=True, key="climate_map_compare")
        _render_legend(region_summary)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

        region_a = region_summary.set_index("region_id").loc[compare_a]
        region_b = region_summary.set_index("region_id").loc[compare_b]
        yearly_a = yearly[yearly["region_id"] == compare_a]
        yearly_b = yearly[yearly["region_id"] == compare_b]
        name_a = region_a["region_name"].split(" - ", 1)[-1]
        name_b = region_b["region_name"].split(" - ", 1)[-1]

        col_a, col_b = st.columns(2, gap="medium")
        with col_a:
            _render_compare_card(region_a)
        with col_b:
            _render_compare_card(region_b)

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

        chart_a, chart_b = st.columns(2, gap="medium")
        with chart_a:
            st.plotly_chart(build_comparison_chart(yearly_a, yearly_b, name_a, name_b), use_container_width=True)
        with chart_b:
            st.plotly_chart(build_precip_comparison_chart(yearly_a, yearly_b, name_a, name_b), use_container_width=True)
        return

    # ---- Normal single-region mode ----
    selected_ids = {st.session_state["selected_region_id"]}
    left, right = st.columns([1.2, 0.8], gap="large")

    with left:
        st.markdown("<div class='map-card'>", unsafe_allow_html=True)
        st.markdown("<p class='section-label'>Climate Region Map</p>", unsafe_allow_html=True)
        map_fig = build_map_figure(
            geojson, region_summary,
            highlight_class if highlight_class != "All" else None,
            selected_ids,
        )
        selection = st.plotly_chart(map_fig, use_container_width=True, key="climate_map", on_select="rerun")
        selected = infer_selected_region(selection)
        if selected and selected in set(region_summary["region_id"]):
            st.session_state["selected_region_id"] = selected
        _render_legend(region_summary)
        st.markdown("</div>", unsafe_allow_html=True)

    selected_id = st.session_state["selected_region_id"]
    region = region_summary.set_index("region_id").loc[selected_id]
    monthly_region = monthly_2025[monthly_2025["region_id"] == selected_id]
    yearly_region = yearly[yearly["region_id"] == selected_id]

    with right:
        _render_region_panel(region, monthly_region, yearly_region, show_trend)
