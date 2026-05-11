# 💼 IT Contracts Clawback Dashboard

A Streamlit dashboard for identifying financial recovery opportunities across IT vendor contracts — including unused funds, underconsumption, and outage-related refunds.

---

## Overview

IT organizations often leave money on the table at contract renewal or expiry. This dashboard gives procurement, finance, and IT teams a single view to surface:

- **Unused funds** — the gap between contracted and actual spend
- **Outage costs** — estimated losses attributable to vendor-side incidents
- **Potential clawback** — the combined recovery opportunity per contract

The app ships with a fully simulated dataset (40 contracts, 10 vendors) so it runs out of the box with no external data required.
---

## Features

| Feature | Details |
|---|---|
| Summary metrics | Total contracts, total contract value, total potential clawback, high-priority count |
| Alert banner | Fires automatically when contracts exceed the clawback threshold |
| Stacked bar chart | Unused funds vs. outage cost per vendor |
| Bubble scatter chart | Per-contract breakdown of unused funds vs. outage cost, sized by clawback magnitude |
| Timeline area chart | Clawback opportunities aggregated by contract end month |
| Interactive table | Full contract detail with conditional row highlighting |
| Sidebar filters | Filter by vendor, contract start date range, and custom alert threshold |
| CSV export | Download the currently filtered dataset with one click |

---

## Project Structure

```
it-clawback-dashboard/
└── app.py          # Self-contained Streamlit application
└── README.md       # This file
```

---

## Requirements

- Python 3.9+
- streamlit
- pandas
- numpy
- plotly

---

## Installation

```bash
# 1. Clone or download the project
git clone https://github.com/your-org/it-clawback-dashboard.git
cd it-clawback-dashboard

# 2. Create and activate a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
.venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install streamlit pandas numpy plotly
```

---

## Running the App

```bash
streamlit run app.py
```

The app will open automatically at `http://localhost:8501`.

---

## Dataset Schema

The simulated dataset is generated inside `app.py` via `generate_data()` using a fixed random seed (`np.random.seed(42)`) for reproducibility.

| Column | Type | Description |
|---|---|---|
| `ContractID` | string | Unique contract identifier (e.g. `CTR-1001`) |
| `Vendor` | string | Vendor name (10 real IT vendors) |
| `ContractAmount` | float | Total contracted value ($100K–$2M) |
| `UsedAmount` | float | Actual spend (40–100% of contract amount) |
| `UnusedFunds` | float | `ContractAmount − UsedAmount` |
| `OutageCost` | float | Estimated cost of vendor outages (0–15% of contract amount; ~30% of contracts have no outage) |
| `PotentialClawback` | float | `UnusedFunds + OutageCost` |
| `ContractStart` | date | Random start date between 2022–2024 |
| `ContractEnd` | date | Start date + random duration (6–36 months) |

To swap in real data, replace the `generate_data()` function with a loader that returns a DataFrame with the same column names.

---

## Connecting Real Data

To use your own contracts data instead of the simulated dataset, replace the `generate_data()` function body with a data loader. For example, loading from a CSV:

```python
@st.cache_data
def generate_data() -> pd.DataFrame:
    df = pd.read_csv("contracts.csv", parse_dates=["ContractStart", "ContractEnd"])
    # Ensure computed columns exist
    df["UnusedFunds"] = df["ContractAmount"] - df["UsedAmount"]
    df["PotentialClawback"] = df["UnusedFunds"] + df["OutageCost"]
    return df
```

The rest of the app will work without any other changes.

---

## Configuration

All interactive configuration is available in the sidebar at runtime:

| Control | Default | Description |
|---|---|---|
| Vendor multiselect | All vendors | Filter contracts to specific vendors |
| Contract Start From | Earliest date in dataset | Lower bound for contract start date |
| Contract Start To | Latest date in dataset | Upper bound for contract start date |
| Highlight Threshold ($) | $50,000 | Contracts with `PotentialClawback` at or above this value are highlighted in amber in the table and counted in the summary metric |

---

## Design

The UI uses a dark enterprise aesthetic:

- **Font**: IBM Plex Sans (body) + IBM Plex Mono (metrics, code)
- **Background**: `#0d1117` (main), `#161b22` (sidebar, cards)
- **Accent**: Amber `#f0b429` — used for high-value indicators, alerts, and the download button
- **Charts**: Plotly with matching dark theme and transparent backgrounds

---

## License

MIT License. See `LICENSE` for details.

---

## Author

Built with [Streamlit](https://streamlit.io) and [Plotly](https://plotly.com/python/).
