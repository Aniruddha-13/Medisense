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
ICON_COLOR = "#94977F"

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
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
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
# STYLING
# ---------------------------------------------------------------------------
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Karla:wght@400;500;600;700;800&family=Inconsolata:wght@400;500;600;700&display=swap');

        :root {
            --primary: #2FBF96;
            --primary-dark: #1F9D7C;
            --primary-pale: #DFF7EF;
            --danger: #EF4444;
            --amber: #F5A623;
            --ink: #16211D;
            --ink-soft: #6B7A76;
            --ink-faint: #9AAFA8;
            --border: #E3F1EC;
            --icon: #94977F;

            --font-heading: 'Karla', sans-serif;
            --font-body: 'Inconsolata', monospace;

            --fs-h1: 2.5rem;
            --fs-h2: 2rem;
            --fs-h3: 1.5rem;
            --fs-body: 1rem;
            --fs-small: 0.8125rem;
            --fs-pill: 0.8125rem;
        }

        html, body, [class*="css"] { font-family: var(--font-body); }
        h1.app-title, .card h3, .dx-top-name, .triage-level, .sidebar-title {
            font-family: var(--font-heading);
        }

        .stApp {
            background: linear-gradient(160deg, #D9F5EC 0%, #EAFBF5 45%, #F4FBF9 100%);
        }

        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        div[data-testid="stStatusWidget"] {visibility: hidden;}
        div[data-testid="stDecoration"] {display: none;}

        header[data-testid="stHeader"] { background: transparent; box-shadow: none; }
        [data-testid="collapsedControl"] {
            background: #FFFFFF;
            border-radius: 10px;
            box-shadow: 0 4px 12px rgba(16, 35, 29, 0.10);
            top: 0.6rem;
            transition: transform 0.15s ease;
        }
        [data-testid="collapsedControl"]:hover { transform: scale(1.08); }

        .block-container {
            padding-top: 1.4rem;
            padding-bottom: 2rem;
            max-width: 1100px;
        }

        /* --- Header --- */
        .header-wrap { margin-bottom: 1.1rem; }
        .breadcrumb {
            font-size: var(--fs-small);
            font-weight: 600;
            color: var(--ink-soft);
            margin-bottom: 0.5rem;
            line-height: 1.3;
        }
        .breadcrumb span.current { color: var(--primary-dark); }
        h1.app-title {
            font-size: var(--fs-h1);
            font-weight: 800;
            color: var(--ink);
            letter-spacing: -0.01em;
            margin: 0 0 0.4rem 0;
            line-height: 1.25;
        }
        .app-subtitle {
            color: var(--ink-soft);
            font-size: var(--fs-body);
            line-height: 1.5;
            max-width: 720px;
        }

        /* --- Fade-in for results --- */
        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(10px); }
            to   { opacity: 1; transform: translateY(0); }
        }

        /* --- Card shell --- */
        .card {
            background: #FFFFFF;
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: 1.25rem 1.4rem;
            box-shadow: 0 8px 22px rgba(16, 35, 29, 0.05);
            margin-bottom: 0.9rem;
            height: 100%;
            animation: fadeInUp 0.35s ease both;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .card:hover {
            transform: translateY(-3px);
            box-shadow: 0 16px 34px rgba(16, 35, 29, 0.09);
        }
        .card h3 {
            margin-top: 0;
            margin-bottom: 0.9rem;
            font-size: var(--fs-h2);
            font-weight: 700;
            color: var(--ink);
            line-height: 1.25;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .card-label {
            font-size: var(--fs-small);
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--ink-faint);
            margin-bottom: 0.4rem;
            margin-top: 0.7rem;
            line-height: 1.3;
        }
        .card-label:first-of-type { margin-top: 0; }

        /* --- Symptom pills --- */
        .pill {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 999px;
            font-size: var(--fs-pill);
            font-weight: 600;
            margin: 0 5px 5px 0;
            transition: transform 0.15s ease;
        }
        .pill:hover { transform: scale(1.06); }
        .pill-active { color: var(--primary-dark); background: var(--primary-pale); border: 1px solid #BFEBDD; }
        .pill-negated { color: var(--ink-faint); background: #F1F6F4; border: 1px solid var(--border); text-decoration: line-through; }
        .empty-note { color: var(--ink-faint); font-size: var(--fs-body); font-style: italic; }

        /* --- Diagnosis list --- */
        .dx-top {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: var(--primary-pale);
            border-radius: 12px;
            padding: 0.8rem 1.1rem;
            margin-bottom: 0.6rem;
            transition: transform 0.15s ease;
        }
        .dx-top:hover { transform: scale(1.01); }
        .dx-top-label {
            font-size: var(--fs-small);
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--primary-dark);
            margin-bottom: 0.1rem;
        }
        .dx-top-name { font-size: var(--fs-h3); font-weight: 800; color: var(--ink); line-height: 1.3; }
        .dx-top-conf { font-size: var(--fs-h3); font-weight: 800; color: var(--primary-dark); font-family: var(--font-heading); }

        .dx-row {
            display: flex; align-items: center; padding: 0.4rem 0.4rem;
            border-bottom: 1px solid #F0F6F4;
            border-radius: 8px;
            transition: background 0.15s ease;
        }
        .dx-row:hover { background: #F7FBFA; }
        .dx-row:last-child { border-bottom: none; }
        .dx-dot { width: 8px; height: 8px; border-radius: 50%; margin-right: 10px; flex-shrink: 0; }
        .dx-name { flex: 1; font-weight: 600; color: var(--ink); font-size: var(--fs-body); }
        .dx-conf { text-align: right; font-weight: 700; color: var(--ink); font-size: var(--fs-body); }

        /* --- Triage banner --- */
        .triage-banner {
            border-radius: 14px;
            padding: 0.8rem 1rem;
            margin-bottom: 0.7rem;
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
        .triage-level { font-size: var(--fs-h3); font-weight: 800; margin: 0; line-height: 1.3; }
        .triage-banner.emergency .triage-level { color: #B91C1C; }
        .triage-banner.urgent .triage-level    { color: #B45309; }
        .triage-banner.routine .triage-level   { color: var(--primary-dark); }

        .justification { color: #3D4A46; font-size: var(--fs-body); line-height: 1.5; }
        .action-box {
            background: var(--primary-pale);
            border: 1px solid #BFEBDD;
            border-radius: 10px;
            padding: 0.6rem 0.85rem;
            font-size: var(--fs-body);
            color: var(--primary-dark);
            margin-top: 0.6rem;
            line-height: 1.45;
        }

        .stProgress > div > div > div > div { background-color: var(--primary); transition: width 0.4s ease; }
        .stButton > button {
            transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease, color 0.15s ease;
        }
        .stButton > button:hover { transform: translateY(-1px); }
        .stButton > button[kind="primary"] {
            background: var(--primary);
            border: none;
            border-radius: 999px;
            padding: 0.5rem 1.5rem;
            font-weight: 700;
            font-size: var(--fs-body);
        }
        .stButton > button[kind="primary"]:hover {
            background: var(--primary-dark);
            box-shadow: 0 8px 20px rgba(47, 191, 150, 0.35);
        }

        /* --- Sidebar --- */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #EAFBF5 0%, #FFFFFF 60%);
        }
        /* Streamlit reserves top padding on this inner wrapper independent of
           .block-container — collapsing both is what actually removes the gap. */
        section[data-testid="stSidebar"] > div:first-child { padding-top: 0 !important; }
        section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] { padding-top: 0.4rem !important; }
        section[data-testid="stSidebar"] .block-container { padding-top: 0.4rem !important; }

        .sidebar-title { font-size: var(--fs-h2); font-weight: 800; color: var(--ink); margin-bottom: 0.15rem; }
        .sidebar-caption { color: var(--ink-soft); font-size: var(--fs-small); margin-bottom: 1rem; line-height: 1.4; }
        .scenario-row { display: flex; align-items: center; gap: 8px; margin-bottom: 0.4rem; }
        .scenario-icon-box {
            width: 34px; height: 34px; min-width: 34px;
            border-radius: 10px;
            background: #FFFFFF;
            border: 1px solid var(--border);
            display: flex; align-items: center; justify-content: center;
        }
        section[data-testid="stSidebar"] .stButton > button {
            border-radius: 999px;
            border: 1px solid var(--border);
            background: #FFFFFF;
            font-size: var(--fs-body);
        }
        section[data-testid="stSidebar"] .stButton > button:hover {
            border-color: var(--primary);
            color: var(--primary-dark);
        }

        .disclaimer-box {
            margin-top: 1.2rem;
            padding: 0.75rem 0.9rem;
            background: #FFFFFF;
            border: 1px solid var(--border);
            border-radius: 12px;
            color: var(--ink-faint);
            font-size: var(--fs-small);
            line-height: 1.45;
        }

        div[data-testid="stTextArea"] div[data-baseweb="textarea"] {
            border: none !important;
            background: transparent !important;
            box-shadow: none !important;
        }
        .stTextArea textarea {
            background-color: #FFFFFF !important;
            border: 1px solid var(--border) !important;
            border-radius: 16px !important;
            font-size: 15px !important;
            font-family: var(--font-body) !important;
            color: var(--ink) !important;
            padding: 14px !important;
            box-shadow: 0 6px 18px rgba(16, 35, 29, 0.04);
            transition: border-color 0.15s ease, box-shadow 0.15s ease;
        }
        .stTextArea textarea:focus {
            border: 1px solid var(--primary) !important;
            box-shadow: 0 0 0 3px rgba(47, 191, 150, 0.15) !important;
        }

        hr { border-top: 1px solid var(--border); margin: 1.1rem 0; }
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
        ("heart", "Acute Cardiac Case",
         "Patient is a 52-year-old presenting with sudden sharp chest pain, "
         "shortness of breath, and palpitations. Denies cough, fever, and vomiting."),
        ("wind", "Upper Respiratory & Ear Case",
         "Patient reports headache, stuffiness in nose and right ear feels blocked. "
         "Suspects cold, but denies chest pain or vomiting."),
        ("activity", "Abdominal Distress Case",
         "Patient complains of sharp abdominal pain, nausea, and vomiting since morning. "
         "No shortness of breath or dizziness."),
    ]

    for icon_name, label, note in scenarios:
        icon_col, btn_col = st.columns([1, 5], vertical_alignment="center")
        with icon_col:
            st.markdown(
                f'<div class="scenario-icon-box">{icon(icon_name, 16)}</div>',
                unsafe_allow_html=True
            )
        with btn_col:
            if st.button(label, use_container_width=True, key=f"demo_{icon_name}"):
                st.session_state["demo_note"] = note

    st.markdown(
        html_block(
            '<div class="disclaimer-box">Research Prototype: MediSense is a decision-support ',
            'demonstration tool for AI laboratory and triage research. It does not provide ',
            'medical treatment or replace licensed clinical evaluation.</div>'
        ),
        unsafe_allow_html=True
    )

# ---------------------------------------------------------------------------
# HEADER
# ---------------------------------------------------------------------------
st.markdown(
    html_block("""
        <div class="header-wrap">
            <div class="breadcrumb">Home &nbsp;›&nbsp; <span class="current">Clinical Triage</span></div>
            <h1 class="app-title">MediSense Clinical Triage</h1>
            <div class="app-subtitle">Enter unstructured patient notes or consultation summaries to
            extract clinical entities and evaluate differential diagnoses.</div>
        </div>
    """),
    unsafe_allow_html=True
)

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
# RESULTS  —  Diagnoses full-width on top, Urgency + Evidence side-by-side below
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

            st.markdown("<hr>", unsafe_allow_html=True)

            predictions = result["predictions"]
            triage = result["triage"]

            # --- 1. RANKED DIFFERENTIAL DIAGNOSES ---
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