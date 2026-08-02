# Enterprise Risk Command Center — Streamlit-in-Snowflake entry point (10 tabs).
# Co-authored with CoCo
"""
Enterprise Risk Command Center — Main Application
Streamlit entry point with 10 feature tabs, running natively in Snowflake.
"""

import streamlit as st

# ─── Page Configuration ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="Enterprise Risk Command Center",
    page_icon="🏗️",
    layout="wide",
)

# ─── Branding (dark theme only) ───────────────────────────────────────────────
st.sidebar.markdown("### 🏗️ Risk Command Center")
st.sidebar.caption("Enterprise Unstructured Data Intelligence")
_dark = True
st.session_state["plotly_template"] = "plotly_dark"


def _theme_css(dark):
    if dark:
        bg, text, sidebar = "#0F172A", "#E2E8F0", "#111827"
        card, border, value, label = "#1E293B", "#334155", "#F1F5F9", "#94A3B8"
        accent, tab_bg, tab_active = "#3B82F6", "#1E293B", "#2563EB"
        input_bg, hover = "#1E293B", "#334155"
    else:
        bg, text, sidebar = "#F8FAFC", "#1E293B", "#FFFFFF"
        card, border, value, label = "#FFFFFF", "#E2E8F0", "#0F172A", "#475569"
        accent, tab_bg, tab_active = "#2563EB", "#F1F5F9", "#2563EB"
        input_bg, hover = "#FFFFFF", "#F1F5F9"
    return f"""<style>
    /* ─── Base ─── */
    .stApp {{ background-color: {bg} !important; color: {text} !important; }}
    .stApp p, .stApp span, .stApp label, .stApp li, .stApp td, .stApp th,
    .stApp .stMarkdown, .stApp .stText, .stApp .stCaption,
    .stApp [data-testid="stText"], .stApp [data-testid="stCaptionContainer"],
    .stApp div, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {{
        color: {text} !important;
    }}
    .stApp a {{ color: {accent} !important; }}
    [data-testid="stSidebar"] {{ background-color: {sidebar} !important; border-right: 1px solid {border}; }}
    [data-testid="stSidebar"] * {{ color: {text} !important; }}

    /* ─── Input elements ─── */
    .stSelectbox label, .stMultiSelect label, .stTextInput label,
    .stNumberInput label, .stTextArea label, .stRadio label,
    .stCheckbox label, .stSlider label, .stDateInput label {{
        color: {text} !important;
    }}
    .stSelectbox [data-baseweb="select"] span,
    .stMultiSelect [data-baseweb="select"] span,
    .stTextInput input, .stNumberInput input, .stTextArea textarea {{
        color: {text} !important;
        background-color: {input_bg} !important;
    }}
    .stSelectbox [data-baseweb="select"],
    .stMultiSelect [data-baseweb="select"] {{
        background-color: {input_bg} !important;
        border-color: {border} !important;
    }}
    .stRadio div[role="radiogroup"] label span {{ color: {text} !important; }}
    .stCheckbox span {{ color: {text} !important; }}

    /* ─── Buttons text ─── */
    .stButton button {{ color: {text} !important; background-color: {card} !important; }}
    .stButton button:hover {{ border-color: {accent} !important; background-color: {hover} !important; }}
    .stDownloadButton button {{ color: {text} !important; background-color: {card} !important; }}

    /* ─── Expander content ─── */
    .streamlit-expanderHeader {{ font-weight: 600; color: {text} !important; }}
    .streamlit-expanderContent, .streamlit-expanderContent * {{ color: {text} !important; }}
    [data-testid="stExpander"] summary span {{ color: {text} !important; }}
    [data-testid="stExpander"] div {{ color: {text} !important; }}

    /* ─── DataFrames ─── */
    .stDataFrame {{ border-radius: 8px; overflow: hidden; border: 1px solid {border}; }}
    .stDataFrame td, .stDataFrame th {{ color: {text} !important; background-color: {card} !important; }}
    .stDataFrame [data-testid="glideDataEditor"] {{ background-color: {card} !important; }}
    [data-testid="stDataFrameResizable"] {{ background-color: {card} !important; border: 1px solid {border}; border-radius: 8px; overflow: hidden; }}
    [data-testid="stDataFrameResizable"] [data-testid="ScrollbarV"],
    [data-testid="stDataFrameResizable"] [data-testid="ScrollbarH"],
    .dvn-scroller::-webkit-scrollbar {{ display: none !important; width: 0 !important; height: 0 !important; }}
    [data-testid="stDataFrameResizable"] {{ scrollbar-width: none !important; }}

    /* ─── st.table (static HTML table) — match dark theme ─── */
    [data-testid="stTable"] table {{ background: {card} !important; color: {text} !important;
        border: 1px solid {border} !important; border-radius: 8px; overflow: hidden; }}
    [data-testid="stTable"] thead th {{ background: {hover} !important; color: {text} !important;
        border-color: {border} !important; }}
    [data-testid="stTable"] tbody th, [data-testid="stTable"] tbody td {{
        background: {card} !important; color: {text} !important; border-color: {border} !important; }}

    /* ─── Alerts / Info / Success / Warning / Error boxes ─── */
    [data-testid="stAlert"] p, [data-testid="stAlert"] span {{ color: {text} !important; }}

    /* ─── Typography ─── */
    .main-header {{ font-size: 1.8rem; font-weight: 800; color: {text} !important;
        letter-spacing: -0.5px; margin-bottom: 0; }}
    .sub-header {{ font-size: 0.9rem; color: {label} !important; margin-top: -4px; margin-bottom: 16px; }}

    /* ─── Tab Navigation Bar ─── */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 2px; background: {tab_bg}; padding: 4px 6px;
        border-radius: 10px; border: 1px solid {border};
        overflow-x: auto; flex-wrap: nowrap;
    }}
    .stTabs [data-baseweb="tab"] {{
        padding: 6px 10px; border-radius: 6px; font-size: 0.72rem;
        font-weight: 600; color: {label} !important;
        background: transparent; border: none;
        white-space: nowrap; min-width: fit-content;
    }}
    .stTabs [data-baseweb="tab"]:hover {{
        background: {hover} !important; color: {text} !important;
    }}
    .stTabs [aria-selected="true"] {{
        background: {tab_active} !important; color: #FFFFFF !important;
        box-shadow: 0 2px 8px rgba(37, 99, 235, 0.3);
    }}
    .stTabs [data-baseweb="tab-highlight"] {{ display: none; }}
    .stTabs [data-baseweb="tab-border"] {{ display: none; }}

    /* ─── Metric Cards ─── */
    .stMetric {{
        background: linear-gradient(135deg, {card} 0%, {hover} 100%) !important;
        border: 1px solid {border} !important;
        border-radius: 12px; padding: 16px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
    }}
    .stMetric [data-testid="stMetricValue"] {{ color: {value} !important; font-size: 1.5rem !important; font-weight: 700; }}
    .stMetric label {{ color: {label} !important; font-size: 0.75rem !important; text-transform: uppercase; letter-spacing: 0.5px; }}
    .stMetric [data-testid="stMetricDelta"] {{ font-size: 0.8rem; }}

    /* ─── Section Headers ─── */
    .stMarkdown h2, .stMarkdown h3 {{ color: {text} !important; font-weight: 700; }}

    /* ─── Plotly Charts ─── */
    .stPlotlyChart {{ border-radius: 8px; overflow: hidden; }}

    /* ─── Dividers ─── */
    hr {{ border-color: {border} !important; opacity: 0.5; }}

    /* ─── Container Cards (simulated without border=True) ─── */
    .card-section {{ background: {card}; border: 1px solid {border}; border-radius: 10px;
        padding: 16px 20px; margin-bottom: 12px; }}
</style>"""


st.markdown(_theme_css(_dark), unsafe_allow_html=True)

# ─── Session State ────────────────────────────────────────────────────────────
if "client" not in st.session_state:
    try:
        from app.utils.snowflake_client import SnowflakeClient
        st.session_state.client = SnowflakeClient()
    except Exception as _e:
        st.error(f"Could not initialize Snowflake session: {_e}")
        st.stop()

client = st.session_state.client

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.divider()

    # Pipeline controls
    st.markdown("#### ⚡ Pipeline")
    if st.button("▶️ Run Full Pipeline", use_container_width=True):
        progress = st.progress(0, text="Starting pipeline...")
        stages = [
            (0.15, "Parsing documents (Bronze → Silver)..."),
            (0.40, "Extracting entities with AI..."),
            (0.65, "Generating vector embeddings..."),
            (0.85, "Refreshing Gold layer views..."),
        ]
        for pct, msg in stages:
            progress.progress(pct, text=msg)
        result = client.run_pipeline()
        progress.progress(1.0, text="Pipeline complete!")
        st.success(result)

    if st.button("📊 Pipeline Status", use_container_width=True):
        status = client.get_pipeline_status()
        if status:
            for s in status:
                count = s.get('RECORDS_PROCESSED', 0)
                icon = "✅" if count > 0 else "⏳"
                st.caption(f"{icon} {s.get('PROCEDURE_NAME', '')} — {count} records")

    st.divider()

    # Document corpus overview (read live from Bronze layer)
    st.markdown("#### 📁 Document Corpus")
    docs = client.get_document_registry(limit=500)
    if docs:
        st.metric("Registered Documents", len(docs))
        types = {}
        for d in docs:
            t = (d.get("FILE_TYPE") or "other").upper()
            types[t] = types.get(t, 0) + 1
        st.caption(" | ".join(f"{k}: {v}" for k, v in sorted(types.items())))
    else:
        st.caption("No documents registered yet.")

    st.divider()
    st.caption("Powered by Snowflake Cortex AI")
    st.caption("Running natively in Snowflake")

# ─── Main Header ─────────────────────────────────────────────────────────────
st.markdown('<p class="main-header">🏗️ Enterprise Risk Command Center</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Unstructured Data Intelligence • AI-Powered Risk Detection • Real-Time Insights</p>', unsafe_allow_html=True)

# ─── Tab Navigation ──────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
    "📊 Overview",
    "🗺️ Heatmap",
    "🔍 Root Cause",
    "📄 Evidence",
    "💰 Financial",
    "✅ Actions",
    "📝 Reports",
    "🤖 CoCo",
    "🔒 Quality",
    "⚙️ Admin",
])

# ─── Tab Rendering (lazy imports inside try/except for resilience) ────────────
with tab1:
    try:
        from app.components import executive_dashboard
        executive_dashboard.render(client)
    except Exception as e:
        st.error(f"Tab error: {e}")

with tab2:
    try:
        from app.components import risk_heatmap
        risk_heatmap.render(client)
    except Exception as e:
        st.error(f"Tab error: {e}")

with tab3:
    try:
        from app.components import root_cause_explorer
        root_cause_explorer.render(client)
    except Exception as e:
        st.error(f"Tab error: {e}")

with tab4:
    try:
        from app.components import evidence_viewer
        evidence_viewer.render(client)
    except Exception as e:
        st.error(f"Tab error: {e}")

with tab5:
    try:
        from app.components import financial_calculator
        financial_calculator.render(client)
    except Exception as e:
        st.error(f"Tab error: {e}")

with tab6:
    try:
        from app.components import action_recommendations
        action_recommendations.render(client)
    except Exception as e:
        st.error(f"Tab error: {e}")

with tab7:
    try:
        from app.components import report_generator
        report_generator.render(client)
    except Exception as e:
        st.error(f"Tab error: {e}")

with tab8:
    try:
        from app.components import coco_assistant
        coco_assistant.render(client)
    except Exception as e:
        st.error(f"Tab error: {e}")

with tab9:
    try:
        from app.components import data_quality
        data_quality.render(client)
    except Exception as e:
        st.error(f"Tab error: {e}")

with tab10:
    try:
        from app.components import admin_panel
        admin_panel.render(client)
    except Exception as e:
        st.error(f"Tab error: {e}")
