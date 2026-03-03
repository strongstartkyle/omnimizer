import streamlit as st
from supabase_client import get_supabase

st.set_page_config(
    page_title="Coach Platform",
    page_icon="💪",
    layout="wide"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@300;400;600;700;800;900&family=JetBrains+Mono:wght@300;400;500&family=Barlow:wght@200;300;400;500&display=swap');

/* ── Headers ── */
h1 {
    font-family: 'Barlow Condensed', sans-serif !important;
    font-weight: 900 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
}
h2 {
    font-family: 'Barlow Condensed', sans-serif !important;
    font-weight: 800 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
}
h3 {
    font-family: 'Barlow Condensed', sans-serif !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.04em !important;
}

/* ── Body text ── */
p, li, div[data-testid="stText"] {
    font-family: 'Barlow', sans-serif !important;
    font-weight: 300 !important;
}

/* ── Metric cards ── */
[data-testid="metric-container"] {
    background-color: #1C1C1C !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-top: 2px solid #C8102E !important;
    border-radius: 0 !important;
    padding: 16px !important;
}
[data-testid="stMetricLabel"] p {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 10px !important;
    letter-spacing: 0.28em !important;
    text-transform: uppercase !important;
    color: #787878 !important;
}
[data-testid="stMetricValue"] {
    font-family: 'Barlow Condensed', sans-serif !important;
    font-weight: 900 !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background-color: #161616 !important;
    border-bottom: 1px solid rgba(255,255,255,0.11) !important;
    gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 10px !important;
    letter-spacing: 0.22em !important;
    text-transform: uppercase !important;
    color: #787878 !important;
    background-color: transparent !important;
    padding: 12px 18px !important;
}
.stTabs [aria-selected="true"] {
    color: #F5F5F5 !important;
    border-bottom: 2px solid #C8102E !important;
    background-color: transparent !important;
}

/* ── Expanders ── */
[data-testid="stExpander"] {
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: 0 !important;
    background-color: #1C1C1C !important;
}
[data-testid="stExpander"] summary span {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 11px !important;
    letter-spacing: 0.2em !important;
    text-transform: uppercase !important;
    color: #787878 !important;
}

/* ── Buttons ── */
.stButton > button {
    font-family: 'Barlow Condensed', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: 0.22em !important;
    text-transform: uppercase !important;
    background-color: #C8102E !important;
    color: #0A0A0A !important;
    border: none !important;
    border-radius: 0 !important;
}
.stButton > button:hover {
    background-color: #F5F5F5 !important;
    box-shadow: 0 0 24px rgba(200,16,46,0.35) !important;
}

/* ── Captions ── */
[data-testid="stCaptionContainer"] p {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 10px !important;
    letter-spacing: 0.22em !important;
    text-transform: uppercase !important;
    color: #787878 !important;
}

/* ── Alerts ── */
[data-testid="stAlert"] {
    border-radius: 0 !important;
    background-color: #1C1C1C !important;
}
[data-testid="stAlert"] p {
    font-family: 'Barlow', sans-serif !important;
    font-size: 14px !important;
    font-weight: 400 !important;
}

/* ── Inputs ── */
input, textarea {
    border-radius: 0 !important;
    font-family: 'Barlow', sans-serif !important;
}
input:focus, textarea:focus {
    border-color: #C8102E !important;
    box-shadow: 0 0 0 1px #C8102E !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] [data-testid="stMarkdown"] p {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 11px !important;
    letter-spacing: 0.15em !important;
}

/* ── Radio ── */
[data-testid="stRadio"] label p {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 10px !important;
    letter-spacing: 0.2em !important;
    text-transform: uppercase !important;
}

/* ── Divider ── */
hr { border-color: rgba(255,255,255,0.06) !important; }

/* ── Chat messages ── */
[data-testid="stChatMessage"] {
    background-color: #1C1C1C !important;
    border-radius: 0 !important;
    border-left: 2px solid #C8102E !important;
}
</style>
""", unsafe_allow_html=True)

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
