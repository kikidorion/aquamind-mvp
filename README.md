# AquaMind: AI water intelligence for facilities

AquaMind turns a facility's raw water data into an ESG-ready picture in a few minutes. Upload a CSV of water
consumption and quality readings, and a pipeline of four AI agents finds anomalies, checks quality against
regulatory limits, drafts GRI 303 / CDP-style disclosure text, and recommends savings with estimated ROI.
The result is shown in an interactive dashboard and can be exported as a branded PDF report.

It is an MVP, built so a prospective design partner can see the value end to end in under 10 minutes.

## The problem

Companies that report on water (GRI 303, CDP Water Security) usually have the data in spreadsheets spread across
sites, and turning it into findings and disclosure text is slow manual work. Water quality issues and cost
leaks hide in the same spreadsheets. AquaMind tests whether an agent pipeline can do the first pass:
summarize, flag, write, and recommend, so the sustainability lead starts from a draft instead of a blank page.

## How it works

```
CSV upload ──► Data preview + charts (pandas, Plotly)
                     │
                     ▼
   1. Data Intelligence Agent      consumption patterns, anomalies (>25% above facility monthly average), efficiency
   2. Quality & Security Agent     readings checked against EPA / WHO thresholds, quality score, alerts
   3. ESG Report Writer Agent      GRI 303-1/3/4/5 and CDP-style narrative, water intensity vs benchmarks, metrics table
   4. Recommendations Agent        prioritized actions with water savings, cost savings, effort, ROI
                     │
                     ▼
        Dashboard tabs + downloadable PDF report (fpdf2)
```

Agents 1 and 2 analyze the data independently. Agents 3 and 4 receive both of their outputs, so the report and
recommendations build on the same findings.

Deterministic reference data lives in code, not in prompts:

| Parameter | Limit | Source |
|---|---|---|
| pH | 6.5 to 8.5 | EPA / WHO |
| Turbidity | ≤ 4.0 NTU | EPA Surface Water Treatment Rule |
| Chlorine | 0.2 to 4.0 mg/L | EPA SDWA |
| Nitrate | ≤ 10.0 mg/L | EPA MCL |

Water intensity benchmarks (m³ per employee per month) are set per sector for manufacturing, logistics, and office sites.

## Try it

```bash
git clone https://github.com/kikidorion/aquamind-mvp.git
cd aquamind-mvp
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Paste an Anthropic API key in the sidebar, or set `ANTHROPIC_API_KEY` as an environment variable or in
`.streamlit/secrets.toml` (see `.streamlit/secrets.toml.example`). Then download the sample data from the app and upload it,
or upload your own CSV with these columns:

```
date, facility_name, consumption_m3, ph, turbidity_ntu, chlorine_mg_l, nitrate_mg_l, cost_usd, water_source, employees_on_site
```

`sample_data.csv` covers three facilities (a manufacturing plant, a distribution center, and a headquarters office).
Full setup and deployment notes are in [SETUP.md](SETUP.md).

## Files

| File | What it does |
|---|---|
| `app.py` | Streamlit UI: upload, preview, charts, agent run, results tabs, PDF export |
| `agents.py` | The four agents, regulatory thresholds, and sector benchmarks |
| `pdf_report.py` | Branded multi-section ESG PDF (cover page, metric cards, alerts, tables) |
| `sample_data.csv` | Demo dataset |

## Status and limits

- MVP for demos and design-partner conversations, not a production compliance tool.
- AI-written disclosure text is a draft. A person should review it before anything is published or filed.
- Thresholds and benchmarks are simplified reference values; real deployments need site- and permit-specific limits.

## Next steps

- Per-site thresholds and permit limits instead of global defaults
- Connect to utility bills and meter data directly instead of CSV upload
- Track findings over time so recommendations can be checked against actual savings

Built by [Kiara Dorion](https://linkedin.com/in/kiara-dorion).
