"""
AquaMind MVP – Water Intelligence Platform
A fully agentic AI pipeline for water ESG reporting and quality monitoring.

Run:  streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import anthropic
import tempfile
import os
import json
from datetime import datetime

from agents import (
    run_data_intelligence_agent,
    run_quality_agent,
    run_report_writer_agent,
    run_recommendations_agent,
    THRESHOLDS,
    BENCHMARKS,
    FACILITY_SECTORS,
)
from pdf_report import build_pdf

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AquaMind – Water Intelligence",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Main brand colors */
    :root {
        --navy:  #0D3B66;
        --blue:  #1565C0;
        --teal:  #00897B;
        --gray:  #607D8B;
    }
    .main-header {
        background: linear-gradient(135deg, #0D3B66 0%, #1565C0 100%);
        padding: 1.5rem 2rem;
        border-radius: 8px;
        margin-bottom: 1.5rem;
        color: white;
    }
    .main-header h1 { color: white; margin: 0; font-size: 2rem; }
    .main-header p  { color: #B3D4F5; margin: 0.3rem 0 0 0; font-size: 1rem; }

    .agent-card {
        border-left: 4px solid #1565C0;
        background: #F8FBFF;
        padding: 0.75rem 1rem;
        border-radius: 0 6px 6px 0;
        margin-bottom: 0.5rem;
    }
    .agent-card.running  { border-left-color: #00897B; background: #F0FAF9; }
    .agent-card.complete { border-left-color: #2E7D32; background: #F1F8E9; }
    .agent-card.error    { border-left-color: #C62828; background: #FFF8F8; }

    .metric-highlight {
        background: linear-gradient(135deg, #E3F2FD, #F0FAF9);
        border: 1px solid #B3D4F5;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
    }
    .alert-critical { background:#FFEBEE; border-left:4px solid #B71C1C; padding:0.5rem 1rem; border-radius:0 6px 6px 0; margin:0.3rem 0; }
    .alert-high     { background:#FFF3E0; border-left:4px solid #E65100; padding:0.5rem 1rem; border-radius:0 6px 6px 0; margin:0.3rem 0; }
    .alert-medium   { background:#FFF8E1; border-left:4px solid #F57F17; padding:0.5rem 1rem; border-radius:0 6px 6px 0; margin:0.3rem 0; }
    .alert-low      { background:#E8EAF6; border-left:4px solid #1565C0; padding:0.5rem 1rem; border-radius:0 6px 6px 0; margin:0.3rem 0; }

    .stButton>button {
        background: linear-gradient(135deg, #0D3B66, #1565C0);
        color: white;
        border: none;
        padding: 0.6rem 2rem;
        border-radius: 6px;
        font-weight: bold;
        font-size: 1rem;
        width: 100%;
    }
    .stButton>button:hover { background: linear-gradient(135deg, #1565C0, #00897B); }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 💧 AquaMind")
    st.markdown("*AI-Native Water Intelligence*")
    st.divider()

    api_key = st.text_input(
        "Anthropic API Key",
        type="password",
        placeholder="sk-ant-...",
        help="Get your key at console.anthropic.com",
    )

    st.divider()
    company_name = st.text_input("Company Name", value="Acme Industrial Corp.")
    reporting_year = st.selectbox("Reporting Year", ["2025", "2024", "2023"], index=0)
    primary_sector = st.selectbox(
        "Primary Sector",
        ["Manufacturing", "Food & Beverage", "Logistics", "Real Estate", "Data Centers", "Hospitality"],
        index=0,
    )

    st.divider()
    st.markdown("**Agent Pipeline**")
    st.markdown("1. 📊 Data Intelligence Agent")
    st.markdown("2. 🔬 Quality & Security Agent")
    st.markdown("3. 📝 ESG Report Writer Agent")
    st.markdown("4. 💡 Recommendations Agent")
    st.divider()
    st.caption("AquaMind MVP v0.1 · Phase 1 Demo")


# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
  <h1>💧 AquaMind Water Intelligence Platform</h1>
  <p>Upload your water data → 4 AI agents analyze, monitor, report, and optimize → Download your ESG report</p>
</div>
""", unsafe_allow_html=True)

# ── File upload ─────────────────────────────────────────────────────────────────
col1, col2 = st.columns([2, 1])
with col1:
    uploaded_file = st.file_uploader(
        "Upload Water Data CSV",
        type=["csv"],
        help="Required columns: date, facility_name, consumption_m3, ph, turbidity_ntu, chlorine_mg_l, nitrate_mg_l, cost_usd",
    )
with col2:
    st.markdown("##### Need sample data?")
    with open(os.path.join(os.path.dirname(__file__), "sample_data.csv"), "rb") as f:
        st.download_button(
            "⬇ Download Sample CSV",
            data=f,
            file_name="aquamind_sample_data.csv",
            mime="text/csv",
        )

# ── Load & preview data ─────────────────────────────────────────────────────────
if uploaded_file:
    df = pd.read_csv(uploaded_file, parse_dates=["date"])
    df = df.sort_values("date")

    st.markdown("---")
    st.markdown("### 📋 Data Preview")

    # Summary stats
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Records", f"{len(df):,}")
    with c2:
        st.metric("Facilities", df["facility_name"].nunique())
    with c3:
        months = df["date"].dt.to_period("M").nunique()
        st.metric("Months of Data", months)
    with c4:
        st.metric("Total Consumption", f"{df['consumption_m3'].sum():,.0f} m³")

    with st.expander("View raw data"):
        st.dataframe(df, use_container_width=True)

    # ── Pre-analysis charts ────────────────────────────────────────────────────
    st.markdown("### 📊 Consumption Overview")
    monthly = df.groupby([df["date"].dt.to_period("M"), "facility_name"])["consumption_m3"].sum().reset_index()
    monthly["date"] = monthly["date"].dt.to_timestamp()

    fig = px.bar(
        monthly, x="date", y="consumption_m3", color="facility_name",
        title="Monthly Water Consumption by Facility (m³)",
        labels={"consumption_m3": "Consumption (m³)", "date": "Month", "facility_name": "Facility"},
        color_discrete_map={
            "Main Manufacturing Plant": "#0D3B66",
            "Distribution Center A":   "#1E88E5",
            "Corporate HQ":            "#00897B",
        },
    )
    fig.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(t=60, b=40),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Quality parameters chart
    st.markdown("### 🔬 Water Quality Parameters")
    fig2 = make_subplots(rows=2, cols=2, subplot_titles=["pH (Safe: 6.5–8.5)", "Turbidity NTU (Max: 4.0)", "Chlorine mg/L (Min: 0.2)", "Nitrate mg/L (Max: 10.0)"])

    for facility, color in [("Main Manufacturing Plant", "#0D3B66"), ("Distribution Center A", "#1E88E5"), ("Corporate HQ", "#00897B")]:
        fdf = df[df["facility_name"] == facility].sort_values("date")
        showlegend = True

        for row, col, param in [(1,1,"ph"), (1,2,"turbidity_ntu"), (2,1,"chlorine_mg_l"), (2,2,"nitrate_mg_l")]:
            fig2.add_trace(go.Scatter(x=fdf["date"], y=fdf[param], name=facility,
                                      line=dict(color=color), showlegend=showlegend), row=row, col=col)
            showlegend = False

    # Threshold lines
    thresholds_plot = [(1,1,6.5,"min"),(1,1,8.5,"max"),(1,2,4.0,"max"),(2,1,0.2,"min"),(2,1,4.0,"max"),(2,2,10.0,"max")]
    for row, col, val, ttype in thresholds_plot:
        fig2.add_hline(y=val, line_dash="dash", line_color="red", row=row, col=col, opacity=0.5)

    fig2.update_layout(height=500, plot_bgcolor="white", paper_bgcolor="white",
                       legend=dict(orientation="h", yanchor="bottom", y=1.02))
    st.plotly_chart(fig2, use_container_width=True)

    # ── Agent pipeline ─────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🤖 AI Agent Pipeline")

    if not api_key:
        st.warning("⚠️ Enter your Anthropic API key in the sidebar to run the agent pipeline.")
    else:
        run_button = st.button("🚀 Run AquaMind Agent Pipeline", use_container_width=True)

        if run_button or st.session_state.get("analysis_complete"):

            if run_button:
                # Clear previous results
                for key in ["analysis", "quality", "report", "recs", "analysis_complete"]:
                    st.session_state.pop(key, None)

            # ── AGENT 1: DATA INTELLIGENCE ──────────────────────────────────
            agent1_placeholder = st.empty()
            agent1_placeholder.markdown('<div class="agent-card running">📊 <b>Agent 1: Data Intelligence Agent</b> — Analyzing consumption patterns and detecting anomalies…</div>', unsafe_allow_html=True)

            if "analysis" not in st.session_state:
                try:
                    client = anthropic.Anthropic(api_key=api_key)
                    data_summary = df.to_string(index=False)
                    analysis = run_data_intelligence_agent(client, data_summary)
                    st.session_state["analysis"] = analysis
                    agent1_placeholder.markdown('<div class="agent-card complete">✅ <b>Agent 1: Data Intelligence Agent</b> — Complete. Anomalies detected, facility breakdown computed.</div>', unsafe_allow_html=True)
                except Exception as e:
                    agent1_placeholder.markdown(f'<div class="agent-card error">❌ <b>Agent 1 Error:</b> {str(e)}</div>', unsafe_allow_html=True)
                    st.stop()
            else:
                agent1_placeholder.markdown('<div class="agent-card complete">✅ <b>Agent 1: Data Intelligence Agent</b> — Complete (cached).</div>', unsafe_allow_html=True)

            # ── AGENT 2: QUALITY & SECURITY ─────────────────────────────────
            agent2_placeholder = st.empty()
            agent2_placeholder.markdown('<div class="agent-card running">🔬 <b>Agent 2: Water Quality & Security Agent</b> — Evaluating parameters against EPA/WHO thresholds…</div>', unsafe_allow_html=True)

            if "quality" not in st.session_state:
                try:
                    client = anthropic.Anthropic(api_key=api_key)
                    quality_cols = ["date", "facility_name", "ph", "turbidity_ntu", "chlorine_mg_l", "nitrate_mg_l"]
                    quality_data = df[quality_cols].to_string(index=False)
                    quality = run_quality_agent(client, quality_data, THRESHOLDS)
                    st.session_state["quality"] = quality
                    alert_count = len(quality.get("alerts", []))
                    agent2_placeholder.markdown(f'<div class="agent-card complete">✅ <b>Agent 2: Quality & Security Agent</b> — Complete. {alert_count} alert(s) flagged. Quality score: {quality.get("quality_score", "N/A")}/100.</div>', unsafe_allow_html=True)
                except Exception as e:
                    agent2_placeholder.markdown(f'<div class="agent-card error">❌ <b>Agent 2 Error:</b> {str(e)}</div>', unsafe_allow_html=True)
                    st.stop()
            else:
                agent2_placeholder.markdown(f'<div class="agent-card complete">✅ <b>Agent 2: Quality & Security Agent</b> — Complete (cached). Quality score: {st.session_state["quality"].get("quality_score", "N/A")}/100.</div>', unsafe_allow_html=True)

            # ── AGENT 3: ESG REPORT WRITER ───────────────────────────────────
            agent3_placeholder = st.empty()
            agent3_placeholder.markdown('<div class="agent-card running">📝 <b>Agent 3: ESG Report Writer Agent</b> — Generating GRI 303 / CDP-formatted narrative…</div>', unsafe_allow_html=True)

            if "report" not in st.session_state:
                try:
                    client = anthropic.Anthropic(api_key=api_key)
                    report = run_report_writer_agent(
                        client,
                        st.session_state["analysis"],
                        st.session_state["quality"],
                        BENCHMARKS,
                        company_name,
                        reporting_year,
                        primary_sector,
                    )
                    st.session_state["report"] = report
                    agent3_placeholder.markdown('<div class="agent-card complete">✅ <b>Agent 3: ESG Report Writer Agent</b> — Complete. GRI 303 and CDP sections generated.</div>', unsafe_allow_html=True)
                except Exception as e:
                    agent3_placeholder.markdown(f'<div class="agent-card error">❌ <b>Agent 3 Error:</b> {str(e)}</div>', unsafe_allow_html=True)
                    st.stop()
            else:
                agent3_placeholder.markdown('<div class="agent-card complete">✅ <b>Agent 3: ESG Report Writer Agent</b> — Complete (cached).</div>', unsafe_allow_html=True)

            # ── AGENT 4: RECOMMENDATIONS ─────────────────────────────────────
            agent4_placeholder = st.empty()
            agent4_placeholder.markdown('<div class="agent-card running">💡 <b>Agent 4: Recommendations Agent</b> — Generating prioritized optimization opportunities…</div>', unsafe_allow_html=True)

            if "recs" not in st.session_state:
                try:
                    client = anthropic.Anthropic(api_key=api_key)
                    recs = run_recommendations_agent(client, st.session_state["analysis"], st.session_state["quality"])
                    st.session_state["recs"] = recs
                    n_recs = len(recs.get("recommendations", []))
                    savings = recs.get("total_potential_savings_usd_annual", 0)
                    agent4_placeholder.markdown(f'<div class="agent-card complete">✅ <b>Agent 4: Recommendations Agent</b> — Complete. {n_recs} recommendations generated. Estimated savings: ${savings:,.0f}/year.</div>', unsafe_allow_html=True)
                except Exception as e:
                    agent4_placeholder.markdown(f'<div class="agent-card error">❌ <b>Agent 4 Error:</b> {str(e)}</div>', unsafe_allow_html=True)
                    st.stop()
            else:
                agent4_placeholder.markdown('<div class="agent-card complete">✅ <b>Agent 4: Recommendations Agent</b> — Complete (cached).</div>', unsafe_allow_html=True)

            st.session_state["analysis_complete"] = True

            # ── RESULTS DISPLAY ──────────────────────────────────────────────
            analysis = st.session_state["analysis"]
            quality  = st.session_state["quality"]
            report   = st.session_state["report"]
            recs     = st.session_state["recs"]

            st.markdown("---")
            st.markdown("### 📈 Analysis Results")

            # KPI row
            r1c1, r1c2, r1c3, r1c4 = st.columns(4)
            with r1c1:
                st.metric("Total Withdrawal", f"{analysis.get('total_consumption_m3', 0):,.0f} m³")
            with r1c2:
                st.metric("Total Cost", f"${analysis.get('total_cost_usd', 0):,.0f}")
            with r1c3:
                q_score  = quality.get("quality_score", 0)
                q_status = quality.get("overall_quality_status", "WATCH")
                st.metric("Quality Score", f"{q_score}/100", delta=q_status)
            with r1c4:
                sav = recs.get("total_potential_savings_usd_annual", 0)
                st.metric("Savings Identified", f"${sav:,.0f}/yr")

            # Tabs for sections
            tab1, tab2, tab3, tab4 = st.tabs(["🔍 Anomalies", "⚠️ Quality Alerts", "📄 ESG Report", "💡 Recommendations"])

            with tab1:
                anomalies = analysis.get("anomalies", [])
                if anomalies:
                    for a in anomalies:
                        severity = a.get("severity", "medium")
                        css_class = f"alert-{severity}"
                        st.markdown(f"""
                        <div class="{css_class}">
                            <b>{a.get('facility')} — {a.get('month')}</b><br>
                            Detected: <b>{a.get('consumption_m3'):,.0f} m³</b> (expected ~{a.get('expected_m3'):,.0f} m³ · +{a.get('deviation_pct', 0):.0f}% deviation)<br>
                            Likely cause: {a.get('likely_cause', '')}
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.success("✅ No significant consumption anomalies detected.")
                st.markdown("**Efficiency Opportunities:**")
                for opp in analysis.get("efficiency_opportunities", []):
                    st.markdown(f"• {opp}")

            with tab2:
                alerts = quality.get("alerts", [])
                if alerts:
                    for a in alerts:
                        severity = a.get("severity", "medium")
                        css_class = f"alert-{severity}"
                        st.markdown(f"""
                        <div class="{css_class}">
                            <b>[{severity.upper()}] {a.get('facility')} — {a.get('month')}</b><br>
                            {a.get('parameter','').replace('_',' ').title()}: <b>{a.get('value')}</b>
                            (threshold: {a.get('threshold_type','max')} {a.get('threshold')} per {a.get('regulatory_standard','')})<br>
                            Health risk: {a.get('health_implication','')}<br>
                            ➤ Action: <b>{a.get('recommended_action','')}</b>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.success("✅ All quality parameters within regulatory limits.")
                security_obs = quality.get("security_observations", [])
                if security_obs:
                    st.markdown("**Security Observations:**")
                    for obs in security_obs:
                        st.markdown(f"• {obs}")

            with tab3:
                sections = report.get("sections", {})
                st.markdown("**Frameworks:** " + " · ".join(report.get("framework_references", [])))
                st.divider()
                section_labels = {
                    "executive_summary":            "Executive Summary",
                    "gri_303_1_water_interactions":  "GRI 303-1: Water as a Shared Resource",
                    "gri_303_3_water_withdrawal":    "GRI 303-3: Water Withdrawal",
                    "gri_303_4_water_discharge":     "GRI 303-4: Water Discharge",
                    "gri_303_5_water_consumption":   "GRI 303-5: Water Consumption",
                    "quality_and_compliance":        "Quality and Compliance",
                    "risk_assessment":               "Risk Assessment",
                    "targets_and_performance":       "Targets and Performance",
                    "management_approach":           "Management Approach",
                }
                for key, label in section_labels.items():
                    content = sections.get(key, "")
                    if content:
                        with st.expander(f"📌 {label}"):
                            st.write(content)

                key_metrics = report.get("key_metrics_table", [])
                if key_metrics:
                    st.markdown("**Key Reported Metrics:**")
                    metrics_df = pd.DataFrame(key_metrics)
                    st.dataframe(metrics_df, use_container_width=True, hide_index=True)

            with tab4:
                total_m3_sav  = recs.get("total_potential_savings_m3_annual", 0)
                total_usd_sav = recs.get("total_potential_savings_usd_annual", 0)
                st.metric("Total Identified Savings Potential",
                          f"{total_m3_sav:,.0f} m³/year  ·  ${total_usd_sav:,.0f}/year")
                st.divider()
                for r in recs.get("recommendations", []):
                    with st.expander(f"#{r.get('priority')} · {r.get('title')} — {r.get('facility')}"):
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.markdown(f"**Category:** {r.get('category','').replace('_',' ').title()}")
                            st.markdown(f"**Effort:** {r.get('implementation_effort','').title()}")
                            st.markdown(f"**Timeline:** {r.get('implementation_timeline','')}")
                        with col_b:
                            st.metric("Water Savings", f"{r.get('estimated_savings_m3_annual', 0):,.0f} m³/yr")
                            st.metric("Cost Savings",  f"${r.get('estimated_savings_usd_annual', 0):,.0f}/yr")
                            st.metric("ROI",           f"{r.get('roi_months', '?')} months")
                        st.markdown(r.get("description", ""))
                        if r.get("relevant_regulation"):
                            st.caption(f"📋 Regulation: {r.get('relevant_regulation')}")

            # ── PDF DOWNLOAD ─────────────────────────────────────────────────
            st.markdown("---")
            st.markdown("### 📥 Download ESG Report")
            st.markdown("Generate a professional, branded PDF report with all findings — ready to share with investors, sustainability teams, or regulators.")

            if st.button("📄 Generate & Download PDF Report"):
                with st.spinner("Generating PDF report…"):
                    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                        tmp_path = tmp.name
                    build_pdf(
                        analysis=analysis,
                        quality=quality,
                        report=report,
                        recommendations=recs,
                        company_name=company_name,
                        reporting_year=reporting_year,
                        output_path=tmp_path,
                    )
                    with open(tmp_path, "rb") as f:
                        pdf_bytes = f.read()
                    os.unlink(tmp_path)

                filename = f"AquaMind_Water_Report_{company_name.replace(' ','_')}_{reporting_year}.pdf"
                st.download_button(
                    label="⬇ Download PDF Report",
                    data=pdf_bytes,
                    file_name=filename,
                    mime="application/pdf",
                )
                st.success(f"✅ Report generated successfully: {filename}")

else:
    # ── Landing state ──────────────────────────────────────────────────────────
    st.markdown("### How It Works")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("""
        **① Upload Data**
        Upload a CSV with your water consumption and quality readings. Use the sample file to try it now.
        """)
    with col2:
        st.markdown("""
        **② Agents Analyze**
        4 AI agents run in sequence — consumption analysis, quality monitoring, ESG report writing, and optimization.
        """)
    with col3:
        st.markdown("""
        **③ View Dashboard**
        Instant charts, anomaly alerts, quality flags, and compliance status — all updated in real time.
        """)
    with col4:
        st.markdown("""
        **④ Download Report**
        One-click PDF report formatted for GRI 303, CDP Water Security, and investor disclosure.
        """)
    st.info("⬆ Upload your CSV file above — or download the sample data to try the platform immediately.")
