import streamlit as st
import pandas as pd
from supabase_client import get_supabase
from components.client import render_client


def render_coach():
    sb = get_supabase()

    # ── Top bar ──
    col1, col2 = st.columns([6, 1])
    with col1:
        st.title("🏋️ Coach Dashboard")
    with col2:
        if st.button("Log out", use_container_width=True, key="coach_logout_main"):
            from app import logout
            logout()

    # ── Drill into a specific client ──
    if "viewing_client_id" in st.session_state and st.session_state.viewing_client_id:
        if st.button("← Back to all clients", key="coach_back_btn"):
            st.session_state.viewing_client_id = None
            st.session_state.viewing_client_name = None
            st.rerun()
        render_client(
            client_id=st.session_state.viewing_client_id,
            client_name=st.session_state.viewing_client_name,
            coach_mode=True
        )
        return

    # ── Client roster ──
    st.subheader("Your Clients")

    clients_res = sb.table("clients").select("*").eq("active", True).execute()
    clients = clients_res.data or []

    if not clients:
        st.info("No clients yet. Add your first client below.")
    else:
        for c in clients:
            col1, col2, col3 = st.columns([4, 2, 2])
            with col1:
                st.markdown(f"**{c['name']}**")
                st.caption(f"PIN: `{c['pin']}`  •  Started: {c.get('created_at', '')[:10]}")
            with col2:
                # Last upload timestamp
                cache = sb.table("dashboard_cache").select("updated_at").eq("client_id", c['id']).execute()
                if cache.data:
                    st.caption(f"Last sync: {cache.data[0]['updated_at'][:10]}")
                else:
                    st.caption("No data yet")
            with col3:
                if st.button("View Dashboard", key=f"view_{c['id']}", use_container_width=True):
                    st.session_state.viewing_client_id = c['id']
                    st.session_state.viewing_client_name = c['name']
                    st.rerun()
            st.divider()

    # ── Add new client ──
    with st.expander("➕ Add New Client"):
        with st.form("add_client"):
            new_name = st.text_input("Client Name")
            new_pin  = st.text_input("Access PIN (min 6 characters)")
            t_cal    = st.number_input("Target Calories (kcal)", value=2500, step=50)
            t_steps  = st.number_input("Target Steps", value=8000, step=500)
            t_water  = st.number_input("Target Water (ml)", value=2500, step=100)
            t_sleep  = st.number_input("Target Sleep (hours)", value=7.5, step=0.5)
            t_wchg   = st.number_input("Target Weight Change %/week (negative = loss)", value=-0.75, step=0.05, format="%.2f")

            submitted = st.form_submit_button("Add Client")
            if submitted:
                if not new_name or len(new_pin) < 6:
                    st.error("Please enter a name and a PIN of at least 6 characters.")
                else:
                    targets = {
                        "calories": t_cal,
                        "steps": t_steps,
                        "water": t_water,
                        "sleep": t_sleep,
                        "weight_change_pct_per_week": t_wchg
                    }
                    sb.table("clients").insert({
                        "name": new_name,
                        "pin": new_pin,
                        "targets": targets,
                        "active": True
                    }).execute()
                    st.success(f"Client **{new_name}** added! Share PIN: `{new_pin}`")
                    st.rerun()
