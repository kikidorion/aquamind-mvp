"""
AquaMind AI Agent Pipeline
Three specialized agents run in sequence, each building on the previous output.
"""

import json
import anthropic

# ── EPA / WHO regulatory thresholds used by the Quality Agent ─────────────────
THRESHOLDS = {
    "ph":            {"min": 6.5,  "max": 8.5,  "unit": "",      "standard": "EPA / WHO"},
    "turbidity_ntu": {"min": 0.0,  "max": 4.0,  "unit": "NTU",   "standard": "EPA Surface Water Treatment Rule"},
    "chlorine_mg_l": {"min": 0.2,  "max": 4.0,  "unit": "mg/L",  "standard": "EPA SDWA"},
    "nitrate_mg_l":  {"min": 0.0,  "max": 10.0, "unit": "mg/L",  "standard": "EPA MCL"},
}

# ── Industry water intensity benchmarks (m3 per employee per month) ────────────
BENCHMARKS = {
    "manufacturing":  {"best_in_class": 2.5, "industry_avg": 4.2, "unit": "m3/employee/month"},
    "logistics":      {"best_in_class": 1.8, "industry_avg": 3.1, "unit": "m3/employee/month"},
    "office":         {"best_in_class": 0.6, "industry_avg": 1.1, "unit": "m3/employee/month"},
}

FACILITY_SECTORS = {
    "Main Manufacturing Plant": "manufacturing",
    "Distribution Center A":    "logistics",
    "Corporate HQ":             "office",
}


def _call_claude(client: anthropic.Anthropic, system: str, user: str) -> str:
    """Single Claude API call, returns text content."""
    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return message.content[0].text


# ─────────────────────────────────────────────────────────────────────────────
# AGENT 1: DATA INTELLIGENCE AGENT
# Analyzes consumption patterns, detects anomalies, computes intensity metrics
# ─────────────────────────────────────────────────────────────────────────────

ANALYST_SYSTEM = """You are AquaMind's Data Intelligence Agent — a specialist in water consumption analysis.

Your job: receive structured water consumption data and return a deep analytical report as valid JSON.

Always return ONLY a JSON object with exactly this structure (no markdown, no code fences):
{
  "total_consumption_m3": <number>,
  "total_cost_usd": <number>,
  "reporting_period": "<e.g. Jan 2025 – Dec 2025>",
  "facilities_analyzed": <number>,
  "monthly_trend": "<brief description of overall trend>",
  "peak_month": "<month name>",
  "peak_consumption_m3": <number>,
  "lowest_month": "<month name>",
  "lowest_consumption_m3": <number>,
  "yoy_change_pct": <number or null if single year>,
  "anomalies": [
    {
      "facility": "<name>",
      "month": "<month>",
      "consumption_m3": <number>,
      "expected_m3": <number>,
      "deviation_pct": <number>,
      "likely_cause": "<brief explanation>",
      "severity": "high|medium|low"
    }
  ],
  "facility_breakdown": [
    {
      "facility": "<name>",
      "total_m3": <number>,
      "avg_monthly_m3": <number>,
      "share_of_total_pct": <number>,
      "trend": "increasing|stable|decreasing"
    }
  ],
  "efficiency_opportunities": [
    "<specific observation about potential savings>"
  ],
  "executive_summary": "<3-4 sentence plain-English summary of the data>"
}"""


def run_data_intelligence_agent(client: anthropic.Anthropic, data_summary: str) -> dict:
    """
    Agent 1: Analyzes consumption data and returns structured findings.
    data_summary: string representation of the processed dataframe.
    """
    user_msg = f"""Analyze the following water consumption dataset and return your findings as JSON.

DATASET:
{data_summary}

Identify anomalies as any reading more than 25% above the facility's monthly average.
Be specific about months and facilities. Use real numbers from the data."""

    raw = _call_claude(client, ANALYST_SYSTEM, user_msg)
    # Strip any accidental markdown fences
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw)


# ─────────────────────────────────────────────────────────────────────────────
# AGENT 2: WATER QUALITY & SECURITY AGENT
# Evaluates quality parameters against EPA/WHO thresholds, flags alerts
# ─────────────────────────────────────────────────────────────────────────────

QUALITY_SYSTEM = """You are AquaMind's Water Quality & Security Monitoring Agent.

Your job: evaluate water quality parameter readings against regulatory thresholds and flag alerts.

Always return ONLY a JSON object with exactly this structure:
{
  "overall_quality_status": "COMPLIANT|WATCH|ALERT|CRITICAL",
  "quality_score": <0-100 integer>,
  "alerts": [
    {
      "facility": "<name>",
      "month": "<month>",
      "parameter": "<ph|turbidity_ntu|chlorine_mg_l|nitrate_mg_l>",
      "value": <number>,
      "threshold": <number>,
      "threshold_type": "min|max",
      "regulatory_standard": "<standard name>",
      "severity": "critical|high|medium|low",
      "health_implication": "<brief description of health risk>",
      "recommended_action": "<specific action to take>"
    }
  ],
  "parameters_summary": [
    {
      "parameter": "<name>",
      "avg_value": <number>,
      "min_value": <number>,
      "max_value": <number>,
      "compliant_readings_pct": <number>,
      "status": "compliant|watch|alert"
    }
  ],
  "security_observations": [
    "<any unusual patterns that could indicate tampering, contamination events, or infrastructure issues>"
  ],
  "compliance_statement": "<2-3 sentences suitable for an ESG report on overall quality compliance>"
}"""


def run_quality_agent(
    client: anthropic.Anthropic, quality_data: str, thresholds: dict
) -> dict:
    """Agent 2: Evaluates water quality parameters against thresholds."""
    threshold_text = json.dumps(thresholds, indent=2)
    user_msg = f"""Evaluate the following water quality readings against the provided regulatory thresholds.

QUALITY READINGS:
{quality_data}

REGULATORY THRESHOLDS:
{threshold_text}

Flag every reading that violates or approaches (within 20%) a threshold.
For pH, flag readings outside 6.5-8.5. For turbidity, flag above 3.2 NTU (approaching EPA limit of 4.0).
For chlorine, flag below 0.35 mg/L (approaching minimum). For nitrates, flag above 8.0 mg/L."""

    raw = _call_claude(client, QUALITY_SYSTEM, user_msg)
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw)


# ─────────────────────────────────────────────────────────────────────────────
# AGENT 3: REPORT WRITER AGENT
# Generates professional GRI 303 / CDP-formatted ESG narrative sections
# ─────────────────────────────────────────────────────────────────────────────

REPORTER_SYSTEM = """You are AquaMind's ESG Report Generation Agent — a specialist in water sustainability reporting.

Your job: transform water consumption and quality analysis into a professional, compliance-ready ESG report narrative.

Format your output as valid JSON with these sections:
{
  "report_title": "Water Stewardship Report – [Year]",
  "framework_references": ["GRI 303-1", "GRI 303-3", "GRI 303-4", "GRI 303-5", "CDP Water Security W1", "CDP W4"],
  "sections": {
    "executive_summary": "<2-3 paragraph executive narrative>",
    "gri_303_1_water_interactions": "<GRI 303-1 disclosure: description of interactions with water as a shared resource>",
    "gri_303_3_water_withdrawal": "<GRI 303-3 disclosure: total water withdrawal with breakdown by source, formatted for GRI reporting>",
    "gri_303_4_water_discharge": "<GRI 303-4 disclosure: approach to water discharge and treatment>",
    "gri_303_5_water_consumption": "<GRI 303-5 disclosure: total water consumption and intensity metrics>",
    "quality_and_compliance": "<narrative on water quality monitoring, compliance status, and any incidents>",
    "risk_assessment": "<assessment of water-related risks and opportunities>",
    "targets_and_performance": "<description of water reduction targets and performance against them>",
    "management_approach": "<description of governance, policies, and management systems for water>"
  },
  "key_metrics_table": [
    {"metric": "<name>", "value": "<value with unit>", "framework": "<GRI/CDP reference>"}
  ]
}

Write in professional ESG report language. Be specific with numbers. Reference the actual data provided."""


def run_report_writer_agent(
    client: anthropic.Anthropic,
    analysis: dict,
    quality: dict,
    benchmarks: dict,
    company_name: str,
    reporting_year: str,
    sector: str,
) -> dict:
    """Agent 3: Generates the ESG report narrative from all prior agent outputs."""
    user_msg = f"""Generate a professional water ESG report for:
Company: {company_name}
Reporting Year: {reporting_year}
Primary Sector: {sector}

CONSUMPTION ANALYSIS (from Data Intelligence Agent):
{json.dumps(analysis, indent=2)}

QUALITY ANALYSIS (from Quality Agent):
{json.dumps(quality, indent=2)}

INDUSTRY BENCHMARKS:
{json.dumps(benchmarks, indent=2)}

Generate all report sections. Calculate water intensity (m3 per employee).
Compare performance against best-in-class and industry average benchmarks.
Acknowledge any quality alerts with appropriate disclosures.
Write in a tone suitable for a public ESG report or investor disclosure."""

    raw = _call_claude(client, REPORTER_SYSTEM, user_msg)
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw)


# ─────────────────────────────────────────────────────────────────────────────
# AGENT 4: RECOMMENDATIONS AGENT
# Generates specific, prioritized, quantified optimization recommendations
# ─────────────────────────────────────────────────────────────────────────────

RECOMMENDATIONS_SYSTEM = """You are AquaMind's Water Optimization Agent.

Your job: generate specific, actionable, quantified water reduction and quality improvement recommendations.

Return ONLY valid JSON:
{
  "total_potential_savings_m3_annual": <number>,
  "total_potential_savings_usd_annual": <number>,
  "recommendations": [
    {
      "priority": 1,
      "title": "<short action title>",
      "facility": "<facility name or 'All Facilities'>",
      "category": "leak_detection|efficiency|quality|compliance|technology|process",
      "description": "<2-3 sentence description of the recommended action>",
      "estimated_savings_m3_annual": <number>,
      "estimated_savings_usd_annual": <number>,
      "implementation_effort": "low|medium|high",
      "implementation_timeline": "<e.g. 30 days, 90 days, 6 months>",
      "roi_months": <estimated months to ROI>,
      "relevant_regulation": "<applicable EPA/ESG regulation if any, else null>"
    }
  ]
}

Generate 6-8 recommendations. Be specific and quantified. Base savings estimates on the actual data provided.
Order by priority (1 = highest impact + easiest to implement)."""


def run_recommendations_agent(
    client: anthropic.Anthropic, analysis: dict, quality: dict
) -> dict:
    """Agent 4: Generates prioritized, quantified optimization recommendations."""
    user_msg = f"""Generate water optimization recommendations based on:

CONSUMPTION ANALYSIS:
{json.dumps(analysis, indent=2)}

QUALITY FINDINGS:
{json.dumps(quality, indent=2)}

Focus especially on:
1. The March anomaly at Main Manufacturing Plant (potential leak)
2. The May turbidity spike at Distribution Center A
3. The October pH drop at Corporate HQ
4. Overall efficiency improvements
5. Compliance and monitoring improvements

Make savings estimates realistic and specific to the data provided."""

    raw = _call_claude(client, RECOMMENDATIONS_SYSTEM, user_msg)
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw)
