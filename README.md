# Health Coaching Platform — Setup Guide

## Overview

A hosted, multi-client health coaching platform built with Streamlit + Supabase.

- **Clients** visit a URL, enter their PIN, upload their Apple Health export, and view their own dashboard
- **You (coach)** log in with your coach PIN, see all clients, drill into any dashboard, and add annotations

---

## Project Structure

```
coach-platform/
├── app.py                  ← Entry point (routing + PIN auth)
├── insight_engine.py       ← Data pipeline (extensible biometrics)
├── supabase_client.py      ← Supabase connection helper
├── pages/
│   ├── coach.py            ← Coach roster + client management
│   └── client.py           ← Client dashboard (6 tabs)
├── requirements.txt
├── supabase_schema.sql     ← Run once in Supabase SQL editor
└── README.md
```

---

## Step 1 — Supabase Setup

1. Go to [supabase.com](https://supabase.com) → create a free project
2. In the dashboard → **SQL Editor** → paste and run `supabase_schema.sql`
3. Go to **Storage** → create a new bucket called `exports` (set to **private**)
4. Go to **Settings → API** → copy:
   - **Project URL**
   - **anon/public key**

---

## Step 2 — GitHub Repository

1. Create a new GitHub repo (can be private)
2. Push all files from this folder to it:

```bash
git init
git add .
git commit -m "Initial coaching platform"
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

---

## Step 3 — Streamlit Community Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io) → sign in with GitHub
2. Click **New app**
3. Select your repo, branch (`main`), and main file (`app.py`)
4. Click **Advanced settings** → add these secrets:

```toml
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your-anon-key"
COACH_PIN = "your-secure-coach-pin"
```

5. Click **Deploy** — your app will be live at a public URL in ~2 minutes

---

## Step 4 — Adding Clients

1. Log in to your coach dashboard using your `COACH_PIN`
2. Click **Add New Client**
3. Enter their name, set a PIN (min 6 characters), and configure their targets
4. Share the app URL and their PIN with the client

---

## Client Instructions (share this with clients)

1. Visit `[your app URL]`
2. Enter your access code
3. Click **Upload Apple Health Export** and follow the steps:
   - iPhone → Health app → profile photo → Export All Health Data
   - Unzip the file on your phone or computer
   - Upload `export.xml`
4. Your dashboard updates automatically after each upload

---

## Dashboard Tabs

| Tab | Content |
|-----|---------|
| 📈 Charts | Weight, calories, steps, sleep trends with 14-day rolling averages |
| 💧 Hydration | Daily water intake vs target, compliance rate |
| 💊 Vitamins & Minerals | Manual supplement log (Vit D, C, B12, Omega-3, Mg, Zn, Fe + custom) |
| 📋 Recommendations | Latest metrics, coach annotations, full recommendation history |
| 🎯 Composite Score | Daily score trend + per-period bar chart |
| 🗓️ Macrocycle | 2-week period cards + cross-period weight and calorie charts |

---

## Adding New Biometrics

The engine is built to be extensible. To add a new Apple Health metric:

1. Open `insight_engine.py`
2. Add to `METRICS_MAP`:
```python
"HKQuantityTypeIdentifierHeartRateVariabilitySDNN": ("hrv", "mean"),
```
3. Add a target in the `targets` dict and a deviation calculation in `run_engine()`
4. Add a chart/section to the relevant tab in `pages/client.py`

---

## Secrets Reference

| Key | Value |
|-----|-------|
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_KEY` | Your Supabase anon/public key |
| `COACH_PIN` | Your personal coach login code |
