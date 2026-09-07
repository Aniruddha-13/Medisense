import os
import sys
import streamlit as st

# Ensure src/ is in the python path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from pipeline import MediSensePipeline

st.set_page_config(
    page_title="MediSense Clinical Triage",
    page_icon="⚕️",
    layout="wide",
    initial_sidebar_state="expanded"
)

ACCENTS = ["#2FBF96", "#8B7CF6", "#F5A623"]
ICON_COLOR = "#1F9D7C"

ICON_PATHS = {
    "heart": '<path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 1 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>',
    "wind": '<path d="M9.59 4.59A2 2 0 1 1 11 8H2m10.59 11.41A2 2 0 1 0 14 16H2m15.73-8.27A2.5 2.5 0 1 1 19.5 12H2"/>',
    "activity": '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>',
    "list": '<line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/>',
    "alert-triangle": '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
    "search": '<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>',
}


def icon(name: str, size: int = 16, color: str = ICON_COLOR) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
        f'stroke="{color}" stroke-width="2" stroke-linecap="round" '
        f'stroke-linejoin="round" style="vertical-align:middle;">{ICON_PATHS[name]}</svg>'
    )


def html_block(*lines: str) -> str:
    """
    Join HTML fragments into a single line of markup so Streamlit's markdown
    parser never mistakes indented content for a code block.
    """
    return "".join(line.strip() for line in lines)


# ---------------------------------------------------------------------------
# STYLING — Dashboard-style layout matching reference image
# ---------------------------------------------------------------------------
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inconsolata:wght@300;400;500;600;700&family=Karla:wght@400;500;600;700;800;900&display=swap');

        :root {
            --primary: #2FBF96;
            --primary-dark: #1F9D7C;
            --primary-pale: #DFF7EF;
            --primary-mist: #C8F0E2;
            --accent-purple: #8B7CF6;
            --accent-purple-pale: #EDE9FE;
            --accent-amber: #F5A623;
            --accent-amber-pale: #FFF4E0;
            --danger: #EF4444;
            --amber: #F5A623;
            --ink: #111827;
            --ink-soft: #4B5563;
            --ink-faint: #9CA3AF;
            --border: #DEDFE1;
            --border-light: #F3F4F6;
            --surface: #FFFFFF;
            --icon: #1F9D7C;

            --font-heading: 'Karla', sans-serif;
            --font-subheading: 'Inconsolata', sans-serif;
            --font-body: 'Karla', sans-serif;
            --font-mono: 'Inconsolata', sans-serif;

            /* Type scale — every var(--fs-*) referenced below must be defined
               here, otherwise the browser silently falls back to the inherited
               16px body size and the intended heading/label hierarchy collapses
               (this was the cause of the flat, "everything looks the same
               size" look). */
            --fs-h1: 52px;
            --fs-h2: 28px;
            --fs-h3: 20px;
            --fs-body: 15px;
            --fs-small: 13px;
            --fs-caption: 12px;
            --fs-xs: 14px;

            --radius-xl: 20px;
            --radius-lg: 16px;
            --radius-md: 12px;
            --radius-sm: 8px;
            --radius-pill: 999px;

            --shadow-card: 0 1px 3px rgba(22,50,39,0.04), 0 6px 18px rgba(22,50,39,0.03);
            --shadow-card-hover: 0 4px 12px rgba(22,50,39,0.07), 0 12px 28px rgba(22,50,39,0.05);
            --shadow-subtle: 0 1px 2px rgba(22,50,39,0.03);
        }

        html, body, [class*="css"] {
            font-family: var(--font-body);
            font-size: 16px;
            line-height: 1.55;
            color: #111827;
            -webkit-font-smoothing: antialiased;
        }
        /* Headings — Karla */
        h1.app-title, .card h3, .dx-top-name, .dx-top-conf, .triage-level,
        .sidebar-title, .cta-title, .metric-value {
            font-family: var(--font-heading);
        }
        /* Subheadings / labels / captions — Inconsolata */
        .kpi-label, .card-label, .sidebar-caption, .breadcrumb,
        .dx-top-label, .results-header-text, .disclaimer-box {
            font-family: var(--font-subheading);
        }

        /* ── Background ── */
        .stApp {
            background: #EDF9F6;
        }

        /* ── Hide chrome ── */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        div[data-testid="stStatusWidget"] {visibility: hidden;}
        div[data-testid="stDecoration"] {display: none;}

        header[data-testid="stHeader"] { background: transparent; box-shadow: none; }
        [data-testid="collapsedControl"] {
            background: var(--surface);
            border-radius: var(--radius-md);
            box-shadow: var(--shadow-card);
            top: 0.6rem;
            transition: transform 0.18s ease;
        }
        [data-testid="collapsedControl"]:hover { transform: scale(1.06); }

        .block-container {
            padding-top: 1.2rem;
            padding-bottom: 2rem;
            max-width: 1200px;
        }

        /* ── Breadcrumb + header ── */
        .header-wrap { margin-bottom: 0.8rem; }
        .breadcrumb {
            font-size: var(--fs-small);
            line-height: 1.55;
            color: var(--ink-soft);
            margin-bottom: 0.3rem;
            line-height: 1.3;
            letter-spacing: 0.01em;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .breadcrumb span.sep { color: var(--ink-faint); font-size: 0.7rem; }
        .breadcrumb span.current { color: var(--ink); font-weight: 600; }
        h1.app-title {
            font-family: 'karla', sans-serif !important;
            font-size: 52px;
            font-weight: 800;
            color: #111827;
            margin: 0 0 0.15rem 0;
            line-height: 1.08;
        }
        .app-subtitle {
            color: var(--ink-soft);
            font-size: 16px;
            line-height: 1.55;
            max-width: 720px;
            font-weight: 400;
        }

        /* ── Fade-in for results ── */
        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(8px); }
            to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes fadeIn {
            from { opacity: 0; }
            to   { opacity: 1; }
        }

        /* ── KPI metric cards (top row) ── */
        .kpi-row {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 14px;
            margin-bottom: 1rem;
        }
        .kpi-card {
            background: var(--surface);
            border: 1px solid var(--border-light);
            border-radius: var(--radius-lg);
            padding: 1rem 1.15rem;
            box-shadow: var(--shadow-card);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            animation: fadeInUp 0.3s ease both;
        }
        .kpi-card:nth-child(2) { animation-delay: 0.04s; }
        .kpi-card:nth-child(3) { animation-delay: 0.08s; }
        .kpi-card:nth-child(4) { animation-delay: 0.12s; }
        .kpi-card:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-card-hover);
        }
        .kpi-icon-row {
            display: flex;
            align-items: center;
            gap: 7px;
            margin-bottom: 0.45rem;
        }
        .kpi-icon {
            width: 30px; height: 30px; min-width: 30px;
            border-radius: var(--radius-sm);
            background: var(--primary-pale);
            display: flex; align-items: center; justify-content: center;
        }
        .kpi-card:nth-child(1) .kpi-icon { background: var(--primary-pale); }
        .kpi-card:nth-child(2) .kpi-icon { background: var(--accent-purple-pale); }
        .kpi-card:nth-child(3) .kpi-icon { background: var(--accent-amber-pale); }
        .kpi-label {
            font-size: var(--fs-small);
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: var(--ink-soft);
            line-height: 1.5;
        }
        .metric-value {
            font-size: var(--fs-h3);
            font-weight: 700;
            color: #111827;
            letter-spacing: -0.01em;
            line-height: 1.35;
        }
        .metric-delta {
            display: inline-block;
            font-size: var(--fs-xs);
            font-weight: 600;
            margin-left: 6px;
            padding: 1px 6px;
            border-radius: var(--radius-pill);
            vertical-align: middle;
        }
        .metric-delta.positive { color: #15803D; background: #DCFCE7; }
        .metric-delta.negative { color: #B91C1C; background: #FEE2E2; }
        .metric-delta.neutral  { color: var(--ink-faint); background: #F1F5F3; }

        /* ── Card shell ── */
        .card {
            background: var(--surface);
            border: 1px solid #DEDFE1;
            border-radius: var(--radius-xl);
            padding: 1.2rem 1.35rem;
            box-shadow: var(--shadow-card);
            margin-bottom: 0.85rem;
            height: 100%;
            animation: fadeInUp 0.35s ease both;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .card:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-card-hover);
        }
        .card h3 {
            font-size: 26px;
            font-weight: 700;
            color: #111827;
            line-height: 1.2;
            letter-spacing: -0.01em;
            margin-top: 0;
            margin-bottom: 0.85rem;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .card-label {
            font-size: var(--fs-small);
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: var(--ink-soft);
            margin-bottom: 0.35rem;
            margin-top: 0.65rem;
            line-height: 1.5;
        }
        .card-label:first-of-type { margin-top: 0; }

        /* ── CTA banner (promotional / highlight) ── */
        .cta-banner {
            background: linear-gradient(135deg, #2FBF96 0%, #1AAD82 45%, #149C74 100%);
            border-radius: var(--radius-xl);
            padding: 1.4rem 1.5rem;
            color: #FFFFFF;
            margin-bottom: 0.85rem;
            position: relative;
            overflow: hidden;
            animation: fadeInUp 0.35s ease both;
        }
        .cta-banner::before {
            content: '';
            position: absolute;
            top: -30%; right: -15%;
            width: 180px; height: 180px;
            background: rgba(255,255,255,0.07);
            border-radius: 50%;
        }
        .cta-banner::after {
            content: '';
            position: absolute;
            bottom: -20%; left: -10%;
            width: 120px; height: 120px;
            background: rgba(255,255,255,0.05);
            border-radius: 50%;
        }
        .cta-title {
            font-family: var(--font-heading);
            font-size: 1.3rem;
            font-weight: 800;
            line-height: 1.25;
            margin-bottom: 0.5rem;
            position: relative;
            z-index: 1;
        }
        .cta-link {
            font-size: var(--fs-body);
            font-weight: 600;
            color: rgba(255,255,255,0.9);
            text-decoration: none;
            position: relative;
            z-index: 1;
            display: inline-flex;
            align-items: center;
            gap: 4px;
        }

        /* ── Symptom pills ── */
        .pill {
            display: inline-block;
            padding: 4px 12px;
            border-radius: var(--radius-pill);
            font-size: var(--fs-body);
            font-weight: 500;
            color: #0F172A;
            margin: 0 5px 5px 0;
            transition: transform 0.15s ease;
        }
        .pill:hover { transform: scale(1.06); }
        .pill-active { color: var(--primary-dark); background: var(--primary-pale); border: 1px solid #BFEBDD; }
        .pill-negated { color: var(--ink-faint); background: #F1F6F4; border: 1px solid var(--border); text-decoration: line-through; }
        .empty-note { color: var(--ink-faint); font-size: var(--fs-body); font-style: italic; }

        /* ── Diagnosis list ── */
        .dx-top {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: var(--primary-pale);
            border-radius: var(--radius-md);
            padding: 0.75rem 1rem;
            margin-bottom: 0.55rem;
            transition: transform 0.15s ease;
        }
        .dx-top:hover { transform: scale(1.01); }
        .dx-top-label {
            font-size: var(--fs-caption);
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            color: #64748B;
            margin-bottom: 0.05rem;
            line-height: 1.5;
        }
        .dx-top-name { font-size: var(--fs-h2); font-weight: 750; color: var(--ink); line-height: 1.3; }
        .dx-top-conf { font-size: var(--fs-h2); font-weight: 750; color: var(--primary-dark); }

        .dx-row {
            display: flex; align-items: center; padding: 0.35rem 0.4rem;
            border-bottom: 1px solid #EEF4F1;
            border-radius: var(--radius-sm);
            transition: background 0.15s ease;
        }
        .dx-row:hover { background: #F5FAF8; }
        .dx-row:last-child { border-bottom: none; }
        .dx-dot { width: 8px; height: 8px; border-radius: 50%; margin-right: 10px; flex-shrink: 0; }
        .dx-name { flex: 1; font-weight: 600; color: var(--ink); font-size: var(--fs-body); }
        .dx-conf { text-align: right; font-weight: 700; color: var(--ink); font-size: var(--fs-body); font-family: var(--font-mono); }

        /* ── Triage banner ── */
        .triage-banner {
            border-radius: var(--radius-md);
            padding: 0.75rem 1rem;
            margin-bottom: 0.6rem;
            display: flex;
            align-items: center;
            gap: 10px;
            transition: transform 0.15s ease;
        }
        .triage-banner:hover { transform: scale(1.01); }
        .triage-banner.emergency { background: #FEF2F2; }
        .triage-banner.urgent    { background: #FFF8EB; }
        .triage-banner.routine   { background: var(--primary-pale); }
        .triage-dot { width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0; }
        .triage-banner.emergency .triage-dot { background: var(--danger); }
        .triage-banner.urgent .triage-dot    { background: var(--amber); }
        .triage-banner.routine .triage-dot   { background: var(--primary); }
        .triage-level { font-size: var(--fs-h2); font-weight: 800; margin: 0; line-height: 1.3; }
        .triage-banner.emergency .triage-level { color: #B91C1C; }
        .triage-banner.urgent .triage-level    { color: #B45309; }
        .triage-banner.routine .triage-level   { color: var(--primary-dark); }

        .justification { color: #3D4A46; font-size: var(--fs-body); line-height: 1.6; }
        .action-box {
            background: var(--primary-pale);
            border: 1px solid #BFEBDD;
            border-radius: var(--radius-sm);
            padding: 0.55rem 0.85rem;
            font-size: var(--fs-body);
            color: var(--primary-dark);
            margin-top: 0.55rem;
            line-height: 1.6;
        }

        .stProgress > div > div > div > div { background-color: var(--primary); transition: width 0.4s ease; }

        /* ── Buttons ── */
        .stButton > button {
            transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease, color 0.15s ease;
        }
        .stButton > button:hover { transform: translateY(-1px); }
        .stButton > button[kind="primary"] {
            background: var(--primary) !important;
            border: none;
            border-radius: 9999px !important;
            padding: 0.55rem 1.6rem;
            font-weight: 700 !important;
            font-size: 16px !important;
            color: #FFFFFF !important;
            line-height: 1.55;
            letter-spacing: normal;
            transition: all 0.2s ease;
        }
        .stButton > button[kind="primary"]:hover {
            background: var(--primary-dark) !important;
            box-shadow: 0 6px 18px rgba(47, 191, 150, 0.3) !important;
        }

        /* ── Sidebar ── */
        section[data-testid="stSidebar"] {
            background: #F4FCFA;
            border-right: 1px solid var(--primary-mist);
        }
        section[data-testid="stSidebar"] > div:first-child { padding-top: 0 !important; }
        section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] { padding-top: 0.4rem !important; }
        section[data-testid="stSidebar"] .block-container { padding-top: 0.4rem !important; }

        .sidebar-title { font-size: var(--fs-h2); font-weight: 800; color: var(--ink); margin-bottom: 0.5rem; letter-spacing: -0.01em; line-height: 1.25; }
        .sidebar-caption { color: var(--ink-soft); font-size: var(--fs-small); margin-bottom: 0.85rem; line-height: 1.55; }
        .scenario-row { display: flex; align-items: center; gap: 8px; margin-bottom: 0.4rem; }
        .scenario-icon-box {
            width: 44px; height: 44px; min-width: 44px;
            border-radius: var(--radius-sm);
            background: var(--surface);
            border: 1px solid var(--border);
            display: flex; align-items: center; justify-content: center;
            transition: border-color 0.15s ease;
            margin: 0 !important;
            padding: 0 !important;
            box-sizing: border-box;
        }
        /* Override Streamlit's markdown p margin to fix vertical alignment */
        section[data-testid="stSidebar"] [data-testid="column"] .stMarkdown p {
            margin-bottom: 0 !important;
            margin-top: 0 !important;
            padding: 0 !important;
            line-height: 0 !important;
        }
        .scenario-icon-box:hover { border-color: var(--primary); }
        section[data-testid="stSidebar"] .stButton > button {
            border-radius: 9999px !important;
            border: 1.5px solid var(--primary-mist) !important;
            background: #FFFFFF !important;
            font-size: 0.9rem !important;
            font-weight: 500;
            color: #111827 !important;
            line-height: 1;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            height: 44px;
            margin: 0 !important;
            box-sizing: border-box;
        }
        section[data-testid="stSidebar"] .stButton > button:hover {
            border-color: var(--primary) !important;
            color: var(--primary) !important;
        }

        .disclaimer-box {
            margin-top: 1.2rem;
            padding: 0.7rem 0.85rem;
            background: var(--surface);
            border: 1px solid var(--border-light);
            border-radius: var(--radius-md);
            color: var(--ink-faint);
            font-size: var(--fs-xs);
            line-height: 1.45;
        }

        div[data-testid="stTextArea"] div[data-baseweb="textarea"] {
            border: none !important;
            background: transparent !important;
            box-shadow: none !important;
        }
        .stTextArea textarea {
            background-color: #FFFFFF !important;
            border: 1.5px solid var(--primary-mist) !important;
            border-radius: 14px !important;
            font-size: 16px !important;
            font-family: 'Inconsolata', monospace !important;
            line-height: 1.55 !important;
            color: #111827 !important;
            padding: 1rem !important;
            box-shadow: var(--shadow-subtle);
            transition: border-color 0.15s ease, box-shadow 0.15s ease;
        }
        .stTextArea textarea:focus {
            border: 1.5px solid var(--primary) !important;
            box-shadow: 0 0 0 3px rgba(47, 191, 150, 0.12) !important;
        }

        hr { border-top: 1px solid var(--border-light); margin: 0.9rem 0; }

        /* ── Section dividers ── */
        .section-divider {
            height: 1px;
            background: var(--border-light);
            margin: 0.6rem 0 0.9rem 0;
        }

        /* ── Results grid layout ── */
        .results-header {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 0.5rem;
        }
        .results-header-dot {
            width: 8px; height: 8px;
            border-radius: 50%;
            background: var(--primary);
        }
        .results-header-text {
            font-size: var(--fs-small);
            font-weight: 700;
            color: var(--ink-soft);
            text-transform: uppercase;
            letter-spacing: 0.06em;
            line-height: 1.5;
        }

        /* ── Responsive KPI grid ── */
        @media (max-width: 900px) {
            .kpi-row { grid-template-columns: repeat(2, 1fr); }
        }
        @media (max-width: 600px) {
            .kpi-row { grid-template-columns: 1fr; }
        }
    </style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_pipeline():
    return MediSensePipeline()


pipeline = load_pipeline()

# ---------------------------------------------------------------------------
# SIDEBAR: PATIENT DEMOGRAPHICS
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="sidebar-title">Patient Demographics</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sidebar-caption">Clinical context applied for differential guardrails</div>',
        unsafe_allow_html=True
    )

    age = st.number_input("Patient Age", min_value=1, max_value=120, value=28)
    sex = st.selectbox("Biological Sex", ["Female", "Male", "Other"])

    is_pregnant = False
    if sex == "Female":
        is_pregnant = st.checkbox("Currently Pregnant?", value=False)

    chronic_history = st.multiselect(
        "Pre-existing Conditions",
        ["Asthma", "Hypertension", "Diabetes", "Cardiovascular Disease", "None"],
        default=["None"]
    )

    patient_profile = {
        "age": age,
        "sex": sex,
        "is_pregnant": is_pregnant,
        "chronic_history": chronic_history
    }

    st.markdown("---")
    st.markdown('<div class="sidebar-title" style="font-size:1.15rem;">Demo Clinical Scenarios</div>',
                unsafe_allow_html=True)
    st.write("")

    scenarios = [
        (":material/favorite_border:", "Acute Cardiac Case",
         "Patient is a 52-year-old presenting with sudden sharp chest pain, "
         "shortness of breath, and palpitations. Denies cough, fever, and vomiting.", "heart"),
        (":material/air:", "Upper Respiratory & Ear Case",
         "Patient reports headache, stuffiness in nose and right ear feels blocked. "
         "Suspects cold, but denies chest pain or vomiting.", "wind"),
        (":material/monitor_heart:", "Abdominal Distress Case",
         "Patient complains of sharp abdominal pain, nausea, and vomiting since morning. "
         "No shortness of breath or dizziness.", "activity"),
    ]

    for icon_val, label, note, key_name in scenarios:
        if st.button(label, icon=icon_val, use_container_width=True, key=f"demo_{key_name}"):
            st.session_state["demo_note"] = note

    st.markdown(
        html_block(
            '<div class="disclaimer-box">Research Prototype: MediSense is a decision-support demonstration tool for AI laboratory and triage research. It does not provide medical treatment or replace licensed clinical evaluation.</div>'
        ),
        unsafe_allow_html=True
    )

# ---------------------------------------------------------------------------
# HEADER — Breadcrumb + Title + Subtitle (matches reference dashboard nav)
# ---------------------------------------------------------------------------
st.markdown(
    html_block("""
        <div class="header-wrap">
            <div class="breadcrumb">
                <span class="current">Home</span>
                <span class="sep">›</span>
                <span class="current">Clinical Triage</span>
            </div>
            <h1 class="app-title">MediSense Clinical Triage</h1>
            <div class="app-subtitle">MediSense is an AI-powered triage assistant. Enter unstructured patient notes or consultation summaries to
            automatically extract clinical entities, evaluate differential diagnoses, and assess urgency.</div>
        </div>
    """),
    unsafe_allow_html=True
)

# ---------------------------------------------------------------------------
# INPUT — Text area + Run button
# ---------------------------------------------------------------------------
default_text = st.session_state.get(
    "demo_note",
    "Patient reports headache, stuffiness in nose and right ear feels blocked. "
    "Suspects cold, but denies chest pain or vomiting."
)

patient_note = st.text_area(
    "Clinical Narrative / Consultation Note",
    value=default_text,
    height=110,
    label_visibility="collapsed"
)

run_analysis = st.button("Run Diagnosis & Triage →", type="primary")

# ---------------------------------------------------------------------------
# RESULTS
# ---------------------------------------------------------------------------
if run_analysis:
    if not patient_note.strip():
        st.warning("Please enter clinical text or select a demo scenario.")
    else:
        with st.spinner("Processing clinical entities and differential diagnoses..."):
            result = pipeline.analyze(patient_note, patient_profile=patient_profile)

        if result.get("status") == "error":
            st.error(result.get("message", "An error occurred during analysis."))
        else:
            if result.get("warning"):
                st.warning(result["warning"])

            st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

            predictions = result["predictions"]
            triage = result["triage"]

            # --- KPI metric cards (top row) ---
            active_symptoms_text = ", ".join(result["active_symptoms"]) if result["active_symptoms"] else "None"
            negated_symptoms_text = ", ".join(result["negated_symptoms"]) if result["negated_symptoms"] else "None"
            top_disease = predictions[0]["disease"] if predictions else "None"
            top_conf = predictions[0]["confidence"] if predictions else 0
            triage_level_text = triage["triage_level"]

            kpi_html = html_block(
                '<div class="kpi-row">',

                # KPI 1 — Active Symptoms
                '<div class="kpi-card">',
                '<div class="kpi-icon-row">',
                f'<div class="kpi-icon">{icon("search", 14, ACCENTS[0])}</div>',
                '<span class="kpi-label">Active Symptoms</span>',
                '</div>',
                f'<div class="metric-value">{active_symptoms_text}</div>',
                '</div>',

                # KPI 2 — Negated Symptoms
                '<div class="kpi-card">',
                '<div class="kpi-icon-row">',
                f'<div class="kpi-icon">{icon("wind", 14, ACCENTS[1])}</div>',
                '<span class="kpi-label">Negated Symptoms</span>',
                '</div>',
                f'<div class="metric-value">{negated_symptoms_text}</div>',
                '</div>',

                # KPI 3 — Top Prediction
                '<div class="kpi-card">',
                '<div class="kpi-icon-row">',
                f'<div class="kpi-icon">{icon("activity", 14, ACCENTS[2])}</div>',
                '<span class="kpi-label">Top Prediction</span>',
                '</div>',
                f'<div class="metric-value">{top_disease} <span style="font-size: 0.9rem; font-weight: normal; color: #64748B;">({top_conf}%)</span>',
                f'<span class="metric-delta {"positive" if top_conf >= 60 else "negative" if top_conf < 40 else "neutral"}">'
                f'{"↑ High" if top_conf >= 60 else "↓ Low" if top_conf < 40 else "— Moderate"}</span></div>',
                '</div>',

                '</div>'
            )
            st.markdown(kpi_html, unsafe_allow_html=True)

            # --- Results header ----
            st.markdown(
                '<div class="results-header">'
                '<div class="results-header-dot"></div>'
                '<span class="results-header-text">Detailed Analysis</span>'
                '</div>',
                unsafe_allow_html=True
            )

            # --- 1. RANKED DIFFERENTIAL DIAGNOSES (full width) ---
            top_html = ""
            rest_html = ""
            if predictions:
                top = predictions[0]
                top_html = html_block(
                    '<div class="dx-top">',
                    '<div><div class="dx-top-label">Most Likely</div>',
                    f'<div class="dx-top-name">{top["disease"]}</div></div>',
                    f'<div class="dx-top-conf">{top["confidence"]}%</div>',
                    '</div>'
                )
                for i, pred in enumerate(predictions[1:], start=2):
                    color = ACCENTS[(i - 1) % len(ACCENTS)]
                    rest_html += (
                        f'<div class="dx-row"><div class="dx-dot" style="background:{color};"></div>'
                        f'<div class="dx-name">{i}. {pred["disease"]}</div>'
                        f'<div class="dx-conf">{pred["confidence"]}%</div></div>'
                    )

            dx_card_html = html_block(
                f'<div class="card"><h3>{icon("list", 20)} Ranked Differential Diagnoses</h3>',
                f'<div class="card-label">Context — Sex: {sex} · Age: {age} · Pregnant: {is_pregnant}</div>',
                top_html,
                rest_html,
                '</div>'
            )
            st.markdown(dx_card_html, unsafe_allow_html=True)

            # --- 2. URGENCY (left)  +  3. SUPPORTING EVIDENCE (right) ---
            col1, col2 = st.columns([1, 1], gap="medium")

            with col1:
                level = triage["triage_level"]
                if "EMERGENCY" in level:
                    banner_class = "emergency"
                elif "URGENT" in level:
                    banner_class = "urgent"
                else:
                    banner_class = "routine"

                urgency_html = html_block(
                    f'<div class="card"><h3>{icon("alert-triangle", 20)} Urgency Assessment</h3>',
                    f'<div class="triage-banner {banner_class}">',
                    '<div class="triage-dot"></div>',
                    f'<p class="triage-level">{level}</p></div>',
                    '<div class="card-label">Clinical Justification</div>',
                    f'<div class="justification">{triage["justification"]}</div>',
                    f'<div class="action-box"><strong>Recommended Action:</strong> {triage["action_recommendation"]}</div>',
                    '</div>'
                )
                st.markdown(urgency_html, unsafe_allow_html=True)

            with col2:
                active_pills = "".join(
                    f'<span class="pill pill-active">{s}</span>' for s in result["active_symptoms"]
                ) or '<div class="empty-note">None detected</div>'

                negated_pills = "".join(
                    f'<span class="pill pill-negated">{s}</span>' for s in result["negated_symptoms"]
                ) or '<div class="empty-note">None detected</div>'

                evidence_html = html_block(
                    f'<div class="card"><h3>{icon("search", 20)} Supporting Evidence (NLP)</h3>',
                    '<div class="card-label">Confirmed Active Symptoms</div>',
                    f'<div>{active_pills}</div>',
                    '<div class="card-label">Negated / Denied Symptoms</div>',
                    f'<div>{negated_pills}</div></div>'
                )
                st.markdown(evidence_html, unsafe_allow_html=True)