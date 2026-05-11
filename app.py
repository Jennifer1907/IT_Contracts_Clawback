"""
IT Contracts Clawback Dashboard
================================
A Streamlit app to identify opportunities to claw back unused funds,
overpayments, or outage-related refunds from IT contracts.

Run with: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta
import io

# ─────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="IT Contracts Clawback Dashboard",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────
# CUSTOM CSS — dark enterprise aesthetic with amber accents
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600;700&display=swap');

  html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
  }

  /* Main background */
  .stApp {
    background-color: #f5f7fa;
    color: #1a1f2e;
  }

  /* Sidebar */
  [data-testid="stSidebar"] {
    background-color: #ffffff;
    border-right: 1px solid #e2e8f0;
  }
  [data-testid="stSidebar"] .stMarkdown h2,
  [data-testid="stSidebar"] .stMarkdown h3 {
    color: #c47f00;
  }

  /* Metric cards */
  [data-testid="metric-container"] {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 16px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  }
  [data-testid="metric-container"] label {
    color: #64748b !important;
    font-size: 0.75rem !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-family: 'IBM Plex Mono', monospace !important;
  }
  [data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #c47f00 !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 1.6rem !important;
    font-weight: 600;
  }

  /* Section headers */
  h1, h2, h3 {
    font-family: 'IBM Plex Sans', sans-serif;
    color: #1a1f2e;
  }
  h1 { border-bottom: 2px solid #f0b429; padding-bottom: 8px; }

  /* Alert / highlight box */
  .clawback-alert {
    background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
    border-left: 4px solid #f0b429;
    border-radius: 4px;
    padding: 12px 16px;
    margin: 8px 0;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.85rem;
    color: #92400e;
  }

  /* Download button */
  .stDownloadButton > button {
    background-color: #f0b429;
    color: #1a1f2e;
    border: none;
    border-radius: 6px;
    font-weight: 700;
    font-family: 'IBM Plex Sans', sans-serif;
    letter-spacing: 0.05em;
    padding: 8px 20px;
  }
  .stDownloadButton > button:hover {
    background-color: #c47f00;
    color: #ffffff;
  }

  /* Multiselect tags */
  .stMultiSelect span[data-baseweb="tag"] {
    background-color: #f0b429 !important;
    color: #1a1f2e !important;
  }

  /* Divider */
  hr { border-color: #e2e8f0; }

  /* Dataframe */
  .stDataFrame { border: 1px solid #e2e8f0; border-radius: 6px; box-shadow: 0 1px 4px rgba(0,0,0,0.04); }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# SIMULATED DATASET
# ─────────────────────────────────────────────────────────────
@st.cache_data
def generate_data() -> pd.DataFrame:
    """Generate a realistic simulated IT contracts dataset."""
    np.random.seed(42)

    vendors = [
        "Microsoft", "AWS", "Oracle", "Salesforce", "ServiceNow",
        "IBM", "Cisco", "SAP", "Workday", "Palo Alto Networks",
    ]

    n = 40
    base_start = date(2022, 1, 1)

    contract_ids = [f"CTR-{str(i).zfill(4)}" for i in range(1001, 1001 + n)]
    vendor_col   = np.random.choice(vendors, size=n)

    # Contract amounts: 100k–2M
    contract_amounts = np.random.randint(100_000, 2_000_000, size=n).astype(float)

    # Used between 40% and 100% of contract amount
    usage_pct    = np.random.uniform(0.40, 1.00, size=n)
    used_amounts = (contract_amounts * usage_pct).round(2)

    unused_funds = (contract_amounts - used_amounts).round(2)

    # Outage cost: 0–15% of contract amount; ~30% of contracts have no outage
    outage_mask  = np.random.random(n) > 0.30
    outage_costs = np.where(
        outage_mask,
        (contract_amounts * np.random.uniform(0.00, 0.15, size=n)).round(2),
        0.0,
    )

    potential_clawback = (unused_funds + outage_costs).round(2)

    # Random start dates spanning 2022–2024
    start_offsets = np.random.randint(0, 730, size=n)
    starts = [base_start + timedelta(days=int(d)) for d in start_offsets]

    # Contract durations: 6–36 months
    durations = np.random.randint(180, 1080, size=n)
    ends = [s + timedelta(days=int(d)) for s, d in zip(starts, durations)]

    df = pd.DataFrame({
        "ContractID":        contract_ids,
        "Vendor":            vendor_col,
        "ContractAmount":    contract_amounts,
        "UsedAmount":        used_amounts,
        "UnusedFunds":       unused_funds,
        "OutageCost":        outage_costs,
        "PotentialClawback": potential_clawback,
        "ContractStart":     starts,
        "ContractEnd":       ends,
    })
    return df


df_full = generate_data()


# ─────────────────────────────────────────────────────────────
# SIDEBAR — FILTERS
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔍 Filters")
    st.markdown("---")

    # Vendor filter
    all_vendors = sorted(df_full["Vendor"].unique().tolist())
    selected_vendors = st.multiselect(
        "Vendor",
        options=all_vendors,
        default=all_vendors,
        help="Select one or more vendors to include.",
    )

    st.markdown("---")

    # Date range filter
    min_date = df_full["ContractStart"].min()
    max_date = df_full["ContractEnd"].max()

    st.markdown("**Contract Start — From / To**")
    start_from = st.date_input("Start From", value=min_date, min_value=min_date, max_value=max_date)
    start_to   = st.date_input("Start To",   value=max_date, min_value=min_date, max_value=max_date)

    st.markdown("---")

    # Clawback threshold
    clawback_threshold = st.number_input(
        "🚨 Highlight Threshold ($)",
        min_value=0,
        max_value=1_000_000,
        value=50_000,
        step=5_000,
        help="Contracts with PotentialClawback above this value will be highlighted.",
    )

    st.markdown("---")
    st.markdown("### 📋 About")
    st.caption(
        "This dashboard helps identify IT contract clawback opportunities: "
        "unused funds and outage-related refunds."
    )


# ─────────────────────────────────────────────────────────────
# APPLY FILTERS
# ─────────────────────────────────────────────────────────────
df = df_full[
    (df_full["Vendor"].isin(selected_vendors)) &
    (df_full["ContractStart"] >= start_from) &
    (df_full["ContractStart"] <= start_to)
].copy()


# ─────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────
st.markdown("# 💼 IT Contracts Clawback Dashboard")
st.caption("Identify unused funds, overpayments, and outage-related refund opportunities.")

if df.empty:
    st.warning("No contracts match the current filters. Adjust sidebar selections.")
    st.stop()


# ─────────────────────────────────────────────────────────────
# SUMMARY METRICS
# ─────────────────────────────────────────────────────────────
st.markdown("## Overview")
col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Contracts",        f"{len(df):,}")
col2.metric("Total Contract Amount",  f"${df['ContractAmount'].sum():,.0f}")
col3.metric("Total Potential Clawback", f"${df['PotentialClawback'].sum():,.0f}")
col4.metric(
    f"Contracts ≥ ${clawback_threshold:,}",
    f"{(df['PotentialClawback'] >= clawback_threshold).sum():,}",
)

# Alert for high-clawback contracts
n_alerts = (df["PotentialClawback"] >= clawback_threshold).sum()
if n_alerts:
    st.markdown(
        f'<div class="clawback-alert">⚠️  {n_alerts} contract(s) exceed the '
        f'${clawback_threshold:,} clawback threshold and require immediate review.</div>',
        unsafe_allow_html=True,
    )

st.markdown("---")


# ─────────────────────────────────────────────────────────────
# CHARTS
# ─────────────────────────────────────────────────────────────
st.markdown("## Analytics")

chart_col1, chart_col2 = st.columns(2)

# --- Chart 1: Potential Clawback per Vendor (bar) ---
with chart_col1:
    st.markdown("#### Potential Clawback by Vendor")
    vendor_agg = (
        df.groupby("Vendor")[["UnusedFunds", "OutageCost", "PotentialClawback"]]
        .sum()
        .reset_index()
        .sort_values("PotentialClawback", ascending=False)
    )

    fig1 = go.Figure()
    fig1.add_bar(
        x=vendor_agg["Vendor"],
        y=vendor_agg["UnusedFunds"],
        name="Unused Funds",
        marker_color="#3b82f6",
        hovertemplate="Unused Funds: $%{y:,.0f}<extra></extra>",
    )
    fig1.add_bar(
        x=vendor_agg["Vendor"],
        y=vendor_agg["OutageCost"],
        name="Outage Cost",
        marker_color="#f0b429",
        hovertemplate="Outage Cost: $%{y:,.0f}<extra></extra>",
    )
    fig1.update_layout(
        barmode="stack",
        paper_bgcolor="#ffffff",
        plot_bgcolor="#f5f7fa",
        font=dict(color="#1a1f2e", family="IBM Plex Sans"),
        legend=dict(bgcolor="#ffffff", bordercolor="#e2e8f0"),
        xaxis=dict(gridcolor="#e2e8f0"),
        yaxis=dict(gridcolor="#e2e8f0", tickprefix="$", tickformat=",.0f"),
        margin=dict(l=10, r=10, t=10, b=10),
        height=340,
    )
    st.plotly_chart(fig1, use_container_width=True)

# --- Chart 2: UnusedFunds vs OutageCost scatter ---
with chart_col2:
    st.markdown("#### Unused Funds vs. Outage Cost (per Contract)")
    fig2 = px.scatter(
        df,
        x="UnusedFunds",
        y="OutageCost",
        size="PotentialClawback",
        color="Vendor",
        hover_data=["ContractID", "PotentialClawback"],
        size_max=28,
        color_discrete_sequence=px.colors.qualitative.Bold,
    )
    fig2.update_layout(
        paper_bgcolor="#ffffff",
        plot_bgcolor="#f5f7fa",
        font=dict(color="#1a1f2e", family="IBM Plex Sans"),
        legend=dict(bgcolor="#ffffff", bordercolor="#e2e8f0"),
        xaxis=dict(gridcolor="#e2e8f0", tickprefix="$", tickformat=",.0f", title="Unused Funds"),
        yaxis=dict(gridcolor="#e2e8f0", tickprefix="$", tickformat=",.0f", title="Outage Cost"),
        margin=dict(l=10, r=10, t=10, b=10),
        height=340,
    )
    fig2.update_traces(
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Unused Funds: $%{x:,.0f}<br>"
            "Outage Cost: $%{y:,.0f}<br>"
            "Potential Clawback: $%{customdata[1]:,.0f}<extra></extra>"
        )
    )
    st.plotly_chart(fig2, use_container_width=True)

# --- Chart 3: Clawback over time (contracts ending) ---
st.markdown("#### Clawback Opportunities Timeline")
df_time = df.copy()
df_time["EndMonth"] = pd.to_datetime(df_time["ContractEnd"]).dt.to_period("M").astype(str)
time_agg = df_time.groupby("EndMonth")["PotentialClawback"].sum().reset_index()
time_agg.columns = ["Month", "PotentialClawback"]

fig3 = px.area(
    time_agg,
    x="Month",
    y="PotentialClawback",
    line_shape="spline",
    color_discrete_sequence=["#f0b429"],
)
fig3.update_traces(fill="tozeroy", fillcolor="rgba(240,180,41,0.15)", line_width=2)
fig3.update_layout(
    paper_bgcolor="#ffffff",
    plot_bgcolor="#f5f7fa",
    font=dict(color="#1a1f2e", family="IBM Plex Sans"),
    xaxis=dict(gridcolor="#e2e8f0", title="Contract End Month"),
    yaxis=dict(gridcolor="#e2e8f0", tickprefix="$", tickformat=",.0f", title="Total Potential Clawback"),
    margin=dict(l=10, r=10, t=10, b=10),
    height=260,
)
st.plotly_chart(fig3, use_container_width=True)

st.markdown("---")


# ─────────────────────────────────────────────────────────────
# CONTRACT TABLE WITH HIGHLIGHTING
# ─────────────────────────────────────────────────────────────
st.markdown("## Contract Details")

# Build display DataFrame
df_display = df[[
    "ContractID", "Vendor", "ContractAmount", "UsedAmount",
    "UnusedFunds", "OutageCost", "PotentialClawback",
    "ContractStart", "ContractEnd",
]].copy()

# Format currency columns for display
currency_cols = ["ContractAmount", "UsedAmount", "UnusedFunds", "OutageCost", "PotentialClawback"]

def style_clawback_table(styler):
    """Apply row-level highlight when PotentialClawback exceeds threshold."""
    def highlight_row(row):
        if row["PotentialClawback"] >= clawback_threshold:
            return ["background-color: #fef3c7; color: #92400e; font-weight: 600;"] * len(row)
        return [""] * len(row)

    styler.apply(highlight_row, axis=1)
    styler.format({c: "${:,.0f}" for c in currency_cols})
    styler.format({"ContractStart": "{:%Y-%m-%d}", "ContractEnd": "{:%Y-%m-%d}"})
    return styler

styled_df = df_display.style.pipe(style_clawback_table)

st.dataframe(
    styled_df,
    use_container_width=True,
    height=420,
    hide_index=True,
)

# Legend note
st.markdown(
    f'<div class="clawback-alert" style="font-size:0.78rem;">🟡 Highlighted rows have '
    f'PotentialClawback ≥ ${clawback_threshold:,}</div>',
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────────────────────
# DOWNLOAD FILTERED DATA AS CSV
# ─────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📥 Export")

csv_buffer = io.StringIO()
df_display.to_csv(csv_buffer, index=False)
csv_data = csv_buffer.getvalue()

st.download_button(
    label="⬇ Download Filtered Contracts as CSV",
    data=csv_data,
    file_name="it_clawback_contracts.csv",
    mime="text/csv",
)

st.caption(f"Showing {len(df):,} of {len(df_full):,} total contracts based on current filters.")
