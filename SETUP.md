# AquaMind MVP — Setup & Deployment Guide

## What This Is
A fully agentic AI water intelligence platform. Upload water consumption + quality data → 4 AI agents analyze it → live dashboard → professional ESG PDF report. Built to demo to design partners in under 10 minutes.

---

## Step 1: Get Your Tools (15 minutes)

### Python
You need Python 3.10+. Check: `python --version`
If not installed: https://www.python.org/downloads/

### Anthropic API Key
1. Go to https://console.anthropic.com
2. Sign up or log in
3. Click "API Keys" → "Create Key"
4. Copy it — you'll paste it into the app sidebar

---

## Step 2: Set Up the Project (5 minutes)

Open your terminal (Mac: press Cmd+Space, type "Terminal").

```bash
# Navigate to where you want the project
cd ~/Desktop

# Create a folder and move the AquaMind files here
mkdir aquamind
# Copy all the files from your outputs folder into this aquamind/ folder

# Create a Python virtual environment (keeps things clean)
python -m venv venv

# Activate it
# On Mac/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install all dependencies (takes about 2 minutes)
pip install -r requirements.txt
```

---

## Step 3: Run the App (30 seconds)

```bash
streamlit run app.py
```

Your browser will open automatically at `http://localhost:8501`.

If it doesn't open, go there manually.

---

## Step 4: Use the App

1. **Paste your Anthropic API key** in the sidebar (left side)
2. **Enter the company name** you're demoing for
3. **Upload a CSV** — or click "Download Sample CSV" to try it with demo data
4. **Click "Run AquaMind Agent Pipeline"** — watch all 4 agents run live
5. **Explore the results** in the Anomalies, Quality Alerts, ESG Report, and Recommendations tabs
6. **Click "Generate & Download PDF Report"** to get the full branded report

---

## Step 5: Deploy Online (So Anyone Can Access It)

Once you're ready to share with design partners, deploy to Railway (free tier available):

### Option A: Railway (Recommended — easiest)
1. Go to https://railway.app and sign up
2. Click "New Project" → "Deploy from GitHub"
3. Push your aquamind/ folder to a GitHub repo first:
   ```bash
   git init
   git add .
   git commit -m "AquaMind MVP v0.1"
   git remote add origin <your-github-repo-url>
   git push -u origin main
   ```
4. Connect to Railway → it auto-detects Streamlit
5. Add environment variable: `ANTHROPIC_API_KEY` = your key
6. Your app gets a public URL like `aquamind.up.railway.app`

### Option B: Streamlit Community Cloud (Free)
1. Go to https://share.streamlit.io
2. Connect your GitHub repo
3. Set `ANTHROPIC_API_KEY` in the secrets manager
4. Deploy — free public URL instantly

---

## CSV Format

Your CSV must have these columns:

| Column | Description | Example |
|--------|-------------|---------|
| date | First day of month | 2025-01-01 |
| facility_name | Name of location | Main Plant |
| consumption_m3 | Water used in cubic meters | 1248 |
| ph | pH reading | 7.2 |
| turbidity_ntu | Turbidity in NTU | 0.8 |
| chlorine_mg_l | Free chlorine in mg/L | 0.50 |
| nitrate_mg_l | Nitrate in mg/L | 3.1 |
| cost_usd | Water cost in USD | 3120 |
| water_source | Source type | municipal |
| employees_on_site | Headcount at facility | 320 |

**Don't have all quality data?** You can start with just date, facility_name, consumption_m3, and cost_usd — the agents will work with what's available.

---

## What the 4 AI Agents Do

| Agent | Role | Output |
|-------|------|--------|
| Data Intelligence Agent | Analyzes consumption patterns, detects anomalies (25%+ deviations), computes facility breakdowns | Structured JSON with trends, anomalies, executive summary |
| Quality & Security Agent | Evaluates pH, turbidity, chlorine, nitrates against EPA/WHO thresholds | Alert list with severity, health implications, recommended actions |
| ESG Report Writer Agent | Generates GRI 303 and CDP Water Security narrative sections | Full ESG disclosure text ready for investor/regulatory submission |
| Recommendations Agent | Produces prioritized, quantified optimization recommendations | 6-8 recommendations with savings estimates and ROI timelines |

---

## Demoing to Design Partners

**The 10-minute demo script:**

1. "Let me show you what AquaMind does with your data." — Upload their CSV (or sample data)
2. Show the consumption chart. Point to any visible spike.
3. "Now I'll run our AI agent pipeline." — Click Run. Narrate each agent as it completes.
4. Go to Quality Alerts tab. "This is what your current system probably isn't catching."
5. Go to ESG Report tab. "This is your GRI 303 disclosure — auto-generated, audit-ready."
6. Go to Recommendations tab. "Agent 4 found $X in potential savings. Here's how."
7. Generate the PDF. "You can take this to your board today."
8. "What would it be worth to have this running on your real data every month?"

---

## Troubleshooting

**"ModuleNotFoundError"** → Run `pip install -r requirements.txt` again with your venv active

**"API key invalid"** → Double-check key at console.anthropic.com, make sure you copied the full key

**"JSONDecodeError" from an agent** → The agent returned unexpected output. Try running again — it usually resolves.

**Slow agent responses** → Each agent call takes 15-45 seconds. This is normal — Claude Opus is doing deep analysis.

---

## Next Steps After Your First Demo

1. **Close your first design partner** — offer 3 months free in exchange for: real data access, monthly feedback calls, and a public case study
2. **Connect real meter data** — most smart meters have REST APIs. Map their API → your CSV format
3. **Add your company's branding** — swap AquaMind logo in `pdf_report.py` header section
4. **Build the waitlist landing page** — Framer or Webflow, point design partners here

---

*AquaMind MVP v0.1 · Built with Streamlit + Anthropic Claude*
