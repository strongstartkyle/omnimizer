import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import io
from datetime import datetime, date
from supabase_client import get_supabase


# ── Helpers ──────────────────────────────────────────────────────────────────

def load_dashboard_data(sb, client_id: str) -> pd.DataFrame | None:
    """Load cached processed dashboard CSV from Supabase."""
    res = sb.table("dashboard_cache").select("csv_data").eq("client_id", client_id).execute()
    if not res.data:
        return None
    try:
        df = pd.read_csv(io.StringIO(res.data[0]["csv_data"]), parse_dates=["date"])
        return df
    except Exception:
        return None


def get_targets(sb, client_id: str) -> dict:
    res = sb.table("clients").select("targets").eq("id", client_id).execute()
    if res.data and res.data[0].get("targets"):
        return res.data[0]["targets"]
    return {"calories": 2500, "steps": 8000, "water": 2500, "sleep": 7.5, "weight_change_pct_per_week": -0.75}


def load_annotations(sb, client_id: str) -> pd.DataFrame:
    res = sb.table("annotations").select("*").eq("client_id", client_id).order("date", desc=True).execute()
    return pd.DataFrame(res.data or [])


def load_vitamin_logs(sb, client_id: str) -> pd.DataFrame:
    res = sb.table("vitamin_logs").select("*").eq("client_id", client_id).order("date", desc=True).execute()
    return pd.DataFrame(res.data or [])


# ── Main render ──────────────────────────────────────────────────────────────

def render_client(client_id: str, client_name: str, coach_mode: bool = False):
    sb = get_supabase()
    targets = get_targets(sb, client_id)

    # Top bar
    col1, col2 = st.columns([6, 1])
    with col1:
        st.title(f"{'📋 ' if coach_mode else ''}{'Client: ' if coach_mode else ''}{client_name}'s Dashboard")
    with col2:
        if not coach_mode:
            if st.button("Log out", use_container_width=True):
                from app import logout
                logout()

    # ── Load data ─────────────────────────────────────────────────────────────
    df = load_dashboard_data(sb, client_id)

    if df is None or df.empty:
        st.info("Your dashboard is being set up. Your coach will update this shortly after receiving your Health export.")
        return

    latest = df.dropna(subset=["composite_score"]).iloc[-1] if not df.dropna(subset=["composite_score"]).empty else df.iloc[-1]

    # ── Sidebar summary ───────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown(f"**{client_name}**")
        st.caption(f"{df['date'].min().strftime('%d %b')} → {df['date'].max().strftime('%d %b %Y')}")
        st.markdown("---")
        st.markdown("**Targets**")
        st.caption(f"🔥 Calories: {targets.get('calories', '—')} kcal")
        st.caption(f"👟 Steps: {targets.get('steps', '—'):,}")
        st.caption(f"💧 Water: {targets.get('water', '—')} ml")
        st.caption(f"😴 Sleep: {targets.get('sleep', '—')} hrs")
        st.markdown("---")
        st.markdown("**Latest Recommendation**")
        st.info(latest.get("recommendation", "N/A"))

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📈 Charts",
        "💧 Hydration",
        "💊 Vitamins & Minerals",
        "📋 Recommendations",
        "🎯 Composite Score",
        "🗓️ Macrocycle"
    ])

    # ── TAB 1: CHARTS ─────────────────────────────────────────────────────────
    with tab1:
        st.header("Trend Charts")
        rolling_window = 14

        # Weight
        st.subheader("⚖️ Weight")
        fig_w = go.Figure()
        fig_w.add_trace(go.Scatter(x=df['date'], y=df['weight'], name='Daily', mode='lines',
                                   line=dict(color='lightblue', width=1), opacity=0.5))
        fig_w.add_trace(go.Scatter(x=df['date'], y=df['weight_avg'], name='14-Day Avg', mode='lines',
                                   line=dict(color='royalblue', width=2.5)))
        fig_w.update_layout(xaxis_title="Date", yaxis_title="kg", hovermode="x unified", height=320,
                            legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig_w, use_container_width=True)

        c1, c2 = st.columns(2)

        with c1:
            st.subheader("🔥 Calories")
            fig_c = go.Figure()
            fig_c.add_trace(go.Bar(x=df['date'], y=df['calories'], name='Daily', marker_color='lightsalmon', opacity=0.5))
            fig_c.add_trace(go.Scatter(x=df['date'], y=df['calories_avg'], name='14-Day Avg', mode='lines',
                                       line=dict(color='tomato', width=2.5)))
            fig_c.add_hline(y=targets.get('calories', 2500), line_dash="dash", line_color="red", annotation_text="Target")
            fig_c.update_layout(xaxis_title="Date", yaxis_title="kcal", hovermode="x unified", height=300,
                                legend=dict(orientation="h", y=1.1))
            st.plotly_chart(fig_c, use_container_width=True)

        with c2:
            st.subheader("👟 Steps")
            fig_s = go.Figure()
            fig_s.add_trace(go.Bar(x=df['date'], y=df['steps'], name='Daily', marker_color='lightgreen', opacity=0.5))
            fig_s.add_trace(go.Scatter(x=df['date'], y=df['steps_avg'], name='14-Day Avg', mode='lines',
                                       line=dict(color='seagreen', width=2.5)))
            fig_s.add_hline(y=targets.get('steps', 8000), line_dash="dash", line_color="green", annotation_text="Target")
            fig_s.update_layout(xaxis_title="Date", yaxis_title="Steps", hovermode="x unified", height=300,
                                legend=dict(orientation="h", y=1.1))
            st.plotly_chart(fig_s, use_container_width=True)

        # Sleep
        if 'sleep_avg' in df.columns:
            st.subheader("😴 Sleep")
            fig_sl = go.Figure()
            fig_sl.add_trace(go.Bar(x=df['date'], y=df['sleep'], name='Daily', marker_color='plum', opacity=0.5))
            fig_sl.add_trace(go.Scatter(x=df['date'], y=df['sleep_avg'], name='14-Day Avg', mode='lines',
                                        line=dict(color='purple', width=2.5)))
            fig_sl.add_hline(y=targets.get('sleep', 7.5), line_dash="dash", line_color="purple", annotation_text="Target")
            fig_sl.update_layout(xaxis_title="Date", yaxis_title="Hours", hovermode="x unified", height=300,
                                 legend=dict(orientation="h", y=1.1))
            st.plotly_chart(fig_sl, use_container_width=True)

    # ── TAB 2: HYDRATION ──────────────────────────────────────────────────────
    with tab2:
        st.header("💧 Hydration")
        target_water = targets.get('water', 2500)

        if 'water_avg' not in df.columns or df['water'].isna().all():
            st.info("No water intake data found in your Apple Health export. Make sure you're logging water in the Health app or a connected app.")
        else:
            c1, c2, c3 = st.columns(3)
            c1.metric("Latest Daily Water", f"{df['water'].dropna().iloc[-1]:.0f} ml",
                      f"{((df['water'].dropna().iloc[-1] - target_water) / target_water * 100):.1f}% vs target")
            c2.metric("14-Day Avg", f"{df['water_avg'].dropna().iloc[-1]:.0f} ml")
            c3.metric("Target", f"{target_water} ml")

            fig_wat = go.Figure()
            fig_wat.add_trace(go.Bar(x=df['date'], y=df['water'], name='Daily Water',
                                     marker_color='lightcyan', opacity=0.6))
            fig_wat.add_trace(go.Scatter(x=df['date'], y=df['water_avg'], name='14-Day Avg',
                                         mode='lines', line=dict(color='deepskyblue', width=2.5)))
            fig_wat.add_hline(y=target_water, line_dash="dash", line_color="blue", annotation_text="Target")
            fig_wat.update_layout(xaxis_title="Date", yaxis_title="ml", hovermode="x unified", height=380,
                                  legend=dict(orientation="h", y=1.1))
            st.plotly_chart(fig_wat, use_container_width=True)

            # Hydration compliance
            compliant = (df['water'] >= target_water * 0.9).sum()
            total = df['water'].notna().sum()
            st.metric("Days Meeting Target (≥90%)", f"{compliant} / {total}")

    # ── TAB 3: VITAMINS & MINERALS ────────────────────────────────────────────
    with tab3:
        st.header("💊 Vitamins & Minerals")
        st.caption("Log your daily supplementation here. Your coach can view and annotate these entries.")

        vitamin_logs = load_vitamin_logs(sb, client_id)

        # Log form
        with st.expander("➕ Add Today's Entry", expanded=True):
            with st.form("vitamin_form"):
                log_date = st.date_input("Date", value=date.today())
                col1, col2 = st.columns(2)
                with col1:
                    vit_d    = st.number_input("Vitamin D (IU)", min_value=0, step=100, value=0)
                    vit_c    = st.number_input("Vitamin C (mg)", min_value=0, step=50, value=0)
                    vit_b12  = st.number_input("Vitamin B12 (mcg)", min_value=0, step=10, value=0)
                    omega3   = st.number_input("Omega-3 (mg)", min_value=0, step=100, value=0)
                with col2:
                    magnesium = st.number_input("Magnesium (mg)", min_value=0, step=50, value=0)
                    zinc      = st.number_input("Zinc (mg)", min_value=0, step=5, value=0)
                    iron      = st.number_input("Iron (mg)", min_value=0, step=5, value=0)
                    other     = st.text_input("Other (free text)")

                notes = st.text_area("Notes", placeholder="e.g. took with food, forgot evening dose...")
                submitted = st.form_submit_button("Save Entry")

                if submitted:
                    entry = {
                        "client_id": client_id,
                        "date": str(log_date),
                        "vitamin_d": vit_d,
                        "vitamin_c": vit_c,
                        "vitamin_b12": vit_b12,
                        "omega3": omega3,
                        "magnesium": magnesium,
                        "zinc": zinc,
                        "iron": iron,
                        "other": other,
                        "notes": notes
                    }
                    sb.table("vitamin_logs").upsert(entry, on_conflict="client_id,date").execute()
                    st.success("Entry saved!")
                    st.rerun()

        # History table
        if not vitamin_logs.empty:
            st.subheader("Log History")
            display_cols = ['date', 'vitamin_d', 'vitamin_c', 'vitamin_b12', 'omega3',
                            'magnesium', 'zinc', 'iron', 'other', 'notes']
            display_cols = [c for c in display_cols if c in vitamin_logs.columns]
            st.dataframe(vitamin_logs[display_cols].sort_values('date', ascending=False).reset_index(drop=True),
                         use_container_width=True)
        else:
            st.info("No entries yet. Use the form above to log your supplements.")

    # ── TAB 4: RECOMMENDATIONS ────────────────────────────────────────────────
    with tab4:
        st.header("📋 Recommendations")

        # Latest metrics summary
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Avg Weight (14d)", f"{latest.get('weight_avg', 0):.1f} kg",
                  f"{latest.get('weight_pct_change', 0):.2f}% change" if pd.notna(latest.get('weight_pct_change')) else "N/A")
        c2.metric("Avg Calories (14d)", f"{latest.get('calories_avg', 0):.0f} kcal",
                  f"{latest.get('cal_dev', 0):.1f}% vs target" if pd.notna(latest.get('cal_dev')) else "N/A")
        c3.metric("Avg Steps (14d)", f"{latest.get('steps_avg', 0):.0f}",
                  f"{latest.get('steps_dev', 0):.1f}% vs target" if pd.notna(latest.get('steps_dev')) else "N/A")
        if pd.notna(latest.get('sleep_avg')):
            c4.metric("Avg Sleep (14d)", f"{latest.get('sleep_avg', 0):.1f} hrs",
                      f"{latest.get('sleep_dev', 0):.1f}% vs target")

        st.divider()

        # Coach annotations (visible to both)
        st.subheader("📝 Coach Annotations")
        annotations = load_annotations(sb, client_id)

        if coach_mode:
            with st.form("annotation_form"):
                ann_date = st.date_input("Date", value=date.today())
                ann_text = st.text_area("Annotation / Note")
                if st.form_submit_button("Save Annotation"):
                    sb.table("annotations").insert({
                        "client_id": client_id,
                        "date": str(ann_date),
                        "note": ann_text
                    }).execute()
                    st.success("Annotation saved!")
                    st.rerun()

        if not annotations.empty:
            for _, row in annotations.iterrows():
                with st.chat_message("assistant"):
                    st.markdown(f"**{row['date']}** — {row['note']}")
        else:
            st.info("No coach annotations yet.")

        st.divider()

        # Full recommendation history
        st.subheader("Daily Recommendation History")
        rec_df = df[['date', 'period_label', 'weight_avg', 'calories_avg', 'steps_avg', 'recommendation']].copy()
        rec_df = rec_df[rec_df['recommendation'].notna() & (rec_df['recommendation'] != "Insufficient data")]
        rec_df['date'] = rec_df['date'].dt.strftime('%d %b %Y')
        rec_df.columns = ['Date', 'Period', 'Avg Weight', 'Avg Calories', 'Avg Steps', 'Recommendation']
        st.dataframe(rec_df.iloc[::-1].reset_index(drop=True), use_container_width=True)

    # ── TAB 5: COMPOSITE SCORE ────────────────────────────────────────────────
    with tab5:
        st.header("🎯 Composite Score")
        st.caption("Lower = better. Reflects total deviation from all targets combined.")

        fig_cs = go.Figure()
        fig_cs.add_trace(go.Scatter(x=df['date'], y=df['composite_score'], mode='lines+markers',
                                    line=dict(color='mediumpurple', width=2), marker=dict(size=4)))
        fig_cs.add_hline(y=0.3, line_dash="dash", line_color="orange", annotation_text="Tolerance (0.3)")
        fig_cs.update_layout(xaxis_title="Date", yaxis_title="Score", hovermode="x unified", height=360)
        st.plotly_chart(fig_cs, use_container_width=True)

        # Per-period bar
        period_score = df.groupby('period_label')['composite_score'].mean().reset_index()
        fig_ps = px.bar(period_score, x='period_label', y='composite_score',
                        color='composite_score', color_continuous_scale='RdYlGn_r',
                        title="Avg Score per 2-Week Period",
                        labels={'composite_score': 'Avg Score', 'period_label': 'Period'})
        fig_ps.add_hline(y=0.3, line_dash="dash", line_color="orange")
        fig_ps.update_layout(height=300, coloraxis_showscale=False)
        st.plotly_chart(fig_ps, use_container_width=True)

    # ── TAB 6: MACROCYCLE ─────────────────────────────────────────────────────
    with tab6:
        st.header("🗓️ Macrocycle Overview")
        st.caption("3-month macrocycle split into 2-week observation periods.")

        periods = df.groupby('period_label').agg(
            Start=('date', 'min'),
            End=('date', 'max'),
            Avg_Weight=('weight_avg', 'mean'),
            Avg_Calories=('calories_avg', 'mean'),
            Avg_Steps=('steps_avg', 'mean'),
            Avg_Sleep=('sleep_avg', 'mean') if 'sleep_avg' in df.columns else ('date', 'count'),
            Avg_Score=('composite_score', 'mean'),
            Weight_Change=('weight_pct_change', 'last'),
        ).reset_index()

        periods['Date Range'] = periods['Start'].dt.strftime('%d %b') + " → " + periods['End'].dt.strftime('%d %b')

        for _, row in periods.iterrows():
            with st.expander(f"**{row['period_label']}** &nbsp; {row['Date Range']}", expanded=False):
                c1, c2, c3, c4, c5 = st.columns(5)
                c1.metric("Avg Weight", f"{row['Avg_Weight']:.1f} kg",
                          f"{row['Weight_Change']:.2f}%" if pd.notna(row['Weight_Change']) else "N/A")
                c2.metric("Avg Calories", f"{row['Avg_Calories']:.0f} kcal")
                c3.metric("Avg Steps", f"{row['Avg_Steps']:.0f}")
                if 'sleep_avg' in df.columns:
                    c4.metric("Avg Sleep", f"{row['Avg_Sleep']:.1f} hrs" if pd.notna(row['Avg_Sleep']) else "N/A")
                c5.metric("Avg Score", f"{row['Avg_Score']:.3f}" if pd.notna(row['Avg_Score']) else "N/A")

        st.divider()

        # Cross-period weight trend
        fig_pw = px.line(df, x='date', y='weight_avg', color='period_label',
                         title="Weight Trend Across Periods",
                         labels={'weight_avg': 'Avg Weight (kg)', 'date': 'Date', 'period_label': 'Period'})
        fig_pw.update_layout(height=340, hovermode="x unified")
        st.plotly_chart(fig_pw, use_container_width=True)
