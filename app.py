import streamlit as st
from supabase_client import get_supabase

st.set_page_config(
    page_title="Coach Platform",
    page_icon="💪",
    layout="wide"
)

COACH_PIN = st.secrets["COACH_PIN"]   # set in Streamlit secrets

# ── Session state defaults ──
if "role" not in st.session_state:
    st.session_state.role = None       # "coach" | "client"
if "client_id" not in st.session_state:
    st.session_state.client_id = None
if "client_name" not in st.session_state:
    st.session_state.client_name = None
# Add this right after the session state defaults section
if st.session_state.role is not None:
    with st.sidebar:
        if st.button("Log out", key="global_logout"):
            st.session_state.role = None
            st.session_state.client_id = None
            st.session_state.client_name = None
            st.rerun()


def logout():
    st.session_state.role = None
    st.session_state.client_id = None
    st.session_state.client_name = None
    st.rerun()


# ── Already logged in ──
if st.session_state.role == "coach":
    from components.coach import render_coach
    render_coach()

elif st.session_state.role == "client":
    from components.client import render_client
    render_client(
        client_id=st.session_state.client_id,
        client_name=st.session_state.client_name
    )

# ── Login screen ──
else:
    st.markdown("<h1 style='text-align:center;'>💪 Health Coaching Platform</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:grey;'>Enter your access code to continue</p>", unsafe_allow_html=True)
    st.markdown("---")

    col = st.columns([1, 2, 1])[1]
    with col:
        pin = st.text_input("Access Code", type="password", placeholder="••••••")
        submitted = st.button("Continue", use_container_width=True)

    if submitted and pin:
        # Check coach PIN first
        if pin == COACH_PIN:
            st.session_state.role = "coach"
            st.rerun()
        else:
            # Check client PINs in Supabase
            sb = get_supabase()
            result = sb.table("clients").select("id, name").eq("pin", pin).eq("active", True).execute()
            if result.data:
                client = result.data[0]
                st.session_state.role = "client"
                st.session_state.client_id = client["id"]
                st.session_state.client_name = client["name"]
                st.rerun()
            else:
                st.error("Invalid access code. Please check with your coach.")
