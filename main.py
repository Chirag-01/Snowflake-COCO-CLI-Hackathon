# Enterprise Risk Command Center — Streamlit-in-Snowflake entry point (10 tabs).
# Co-authored with CoCo
"""
Enterprise Risk Command Center — Main Application
Streamlit entry point with 10 feature tabs, running natively in Snowflake.
"""

import streamlit as st
from app.config.domain_loader import list_domains, load_domain, set_domain, get_cfg

# ─── Domain bootstrap (before page config so icon is correct) ────────────────
if "domain_id" not in st.session_state:
    st.session_state["domain_id"]  = "construction"
    st.session_state["domain_cfg"] = load_domain("construction")
_boot_cfg = get_cfg()

# ─── Page Configuration ──────────────────────────────────────────────────────
st.set_page_config(
    page_title=_boot_cfg.get("page_title", "Enterprise Risk Command Center"),
    page_icon=_boot_cfg.get("icon", "🏗️"),
    layout="wide",
)

# ─── Branding — pulled from active domain config ─────────────────────────────
_cfg = get_cfg()
st.sidebar.markdown(f"### {_cfg['ui']['app_title']}")
st.sidebar.caption(_cfg["ui"]["app_subtitle"])
_dark = True
st.session_state["plotly_template"] = "plotly_dark"

# ─── Domain Selector ─────────────────────────────────────────────────────────
_available = list_domains()
if len(_available) > 1:
    _domain_labels = {d["id"]: f"{d['icon']} {d['display_name']}" for d in _available}
    _current_id    = st.session_state.get("domain_id", "construction")
    _current_idx   = next((i for i, d in enumerate(_available) if d["id"] == _current_id), 0)
    _selected_id   = st.sidebar.selectbox(
        "🌐 Domain",
        options=[d["id"] for d in _available],
        index=_current_idx,
        format_func=lambda x: _domain_labels.get(x, x),
        key="domain_selector",
    )
    if _selected_id != _current_id:
        set_domain(_selected_id)
        st.rerun()
    st.sidebar.divider()


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
    .stSelectbox [data-baseweb="select"],
    .stSelectbox [data-baseweb="select"] div,
    .stMultiSelect [data-baseweb="select"],
    .stMultiSelect [data-baseweb="select"] div,
    [data-testid="stSelectbox"] > div > div,
    [data-testid="stSelectbox"] > div > div > div,
    .stTextInput input, .stNumberInput input, .stTextArea textarea,
    [data-testid="stFileUploadDropzone"],
    [data-testid="stFileUploadDropzone"] > div,
    [data-testid="stFileUploadDropzone"] > div > div,
    [data-testid="stUploadedFile"],
    [data-testid="stUploadedFile"] > div,
    [data-testid="stUploadedFile"] > div > div {{
        background-color: {input_bg} !important;
        border-color: {border} !important;
        color: {text} !important;
    }}
    .stSelectbox [data-baseweb="select"] span,
    .stMultiSelect [data-baseweb="select"] span {{
        color: {text} !important;
    }}
    .stRadio div[role="radiogroup"] label span {{ color: {text} !important; }}
    .stCheckbox span {{ color: {text} !important; }}

    /* ─── File Uploader ─── */
    [data-testid="stFileUploader"] * {{ color: {text} !important; }}
    [data-testid="stFileUploadDropzone"] button {{
        background-color: {card} !important;
        color: {text} !important;
        border-color: {border} !important;
    }}

    /* ─── Buttons text ─── */
    .stButton button, .stDownloadButton button, 
    [data-testid="stFormSubmitButton"] button, button[data-testid="stFormSubmitButton"],
    [data-testid="baseButton-secondary"], [data-testid="baseButton-primary"],
    button[kind="secondary"], button[kind="primary"], 
    button[kind="secondaryFormSubmit"], button[kind="primaryFormSubmit"] {{ 
        color: {text} !important; 
        background-color: {card} !important; 
        border-color: {border} !important;
    }}
    .stButton button:hover, .stDownloadButton button:hover, 
    [data-testid="stFormSubmitButton"] button:hover, button[data-testid="stFormSubmitButton"]:hover,
    [data-testid="baseButton-secondary"]:hover, [data-testid="baseButton-primary"]:hover,
    button[kind="secondary"]:hover, button[kind="primary"]:hover,
    button[kind="secondaryFormSubmit"]:hover, button[kind="primaryFormSubmit"]:hover {{ 
        border-color: {accent} !important; 
        background-color: {hover} !important; 
        color: {text} !important;
    }}

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

    # ── Team Credits (compact — just above Pipeline) ───────────────────────
    st.markdown(
        """
<div style="
  background:linear-gradient(135deg,#1e3a5f 0%,#312e81 100%);
  border-radius:10px;padding:10px 14px;margin-bottom:4px;
  border:1px solid rgba(99,102,241,0.25);
  display:flex;align-items:center;gap:10px;
">
  <div style="font-size:1.3rem;flex-shrink:0">⚗️</div>
  <div>
    <div style="font-size:.58rem;font-weight:700;color:#a5b4fc;letter-spacing:.1em;
                text-transform:uppercase;line-height:1">Built with ❤️ by</div>
    <div style="font-size:.82rem;font-weight:700;color:#e2e8f0;margin:2px 0 1px">
      Data Alchemists</div>
    <div style="font-size:.65rem;color:#94a3b8;line-height:1.5">
      Chirag Lalwani · Pratik Kanade · Abhishek Bhardwaj</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

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
        result = client.run_pipeline(domain=st.session_state.get("domain_id", "construction"))
        progress.progress(1.0, text="Pipeline complete!")
        for line in result.split('\n'):
            if 'FAILED' in line:
                st.error(line)
            else:
                st.success(line)

    if st.button("📊 Pipeline Status", use_container_width=True):
        status = client.get_pipeline_status()
        if status:
            for s in status:
                count = s.get('RECORDS_PROCESSED', 0)
                icon = "✅" if count > 0 else "⏳"
                st.caption(f"{icon} {s.get('PROCEDURE_NAME', '')} — {count} records")

    st.divider()

    # Document Upload
    _active_domain = st.session_state.get("domain_id", "construction")
    _active_cfg    = get_cfg()
    st.markdown(f"#### 📤 Upload {_active_cfg['entity']['projects']} Documents")
    st.caption(f"Domain: **{_active_cfg['display_name']}** — uploaded files will be tagged as `{_active_domain}`")
    uploaded_files = st.file_uploader(
        "Upload Documents",
        type=["pdf", "csv", "txt", "xlsx", "log", "eml", "msg", "json", "xml", "doc", "docx"],
        label_visibility="collapsed",
        accept_multiple_files=True,
    )
    if uploaded_files:
        st.caption(f"{len(uploaded_files)} file(s) selected")
        if st.button("📥 Process Upload", use_container_width=True):
            import uuid
            success_count = 0
            for uploaded_file in uploaded_files:
                file_name = uploaded_file.name
                file_size = uploaded_file.size
                file_type = file_name.rsplit(".", 1)[-1] if "." in file_name else "unknown"
                doc_id = f"DOC-{uuid.uuid4().hex[:16].upper()}"
                file_path = f"upload/{file_name}"

                with st.spinner(f"Uploading {file_name}..."):
                    # Upload to internal stage
                    try:
                        session = client._session
                        session.file.put_stream(
                            uploaded_file,
                            f"@RISK_COMMAND_CENTER.BRONZE.RAW_INTERNAL_STAGE/{file_path}",
                            auto_compress=False
                        )
                    except Exception:
                        pass

                    # Register in document registry WITH domain tag
                    client.execute(f"""
                        INSERT INTO RISK_COMMAND_CENTER.BRONZE.DOCUMENT_REGISTRY
                        (DOCUMENT_ID, FILE_NAME, FILE_PATH, FILE_SIZE, FILE_TYPE, STATUS, UPLOADED_AT, DOMAIN)
                        VALUES ('{doc_id}', '{file_name}', '{file_path}', {file_size}, '{file_type}',
                                'UPLOADED', CURRENT_TIMESTAMP(), '{_active_domain}')
                    """)
                    success_count += 1

            st.success(f"✅ {success_count} file(s) registered as **{_active_domain}**. Click **Run Full Pipeline** to process.")

    st.divider()

    # Document corpus overview
    st.markdown("#### 📁 Document Corpus")
    docs = client.get_document_registry(limit=500)
    if docs:
        # Domain summary counts
        domain_counts = {}
        for d in docs:
            dm = (d.get("DOMAIN") or "construction").lower()
            domain_counts[dm] = domain_counts.get(dm, 0) + 1
        total = len(docs)
        this_domain = domain_counts.get(_active_domain, 0)

        # KPI row
        k1, k2 = st.columns(2)
        k1.metric("This Domain", f"{this_domain}")
        k2.metric("Total", f"{total}")

        # Domain breakdown chips
        chips = " &nbsp; ".join(
            f'<span style="background:#1e3a5f;color:#7dd3fc;padding:2px 8px;'
            f'border-radius:6px;font-size:.65rem;font-weight:600">'
            f'{k}: {v}</span>'
            for k, v in sorted(domain_counts.items())
        )
        st.markdown(chips, unsafe_allow_html=True)
        st.markdown("")  # small spacer

        # Document list — show name, type, status for this domain
        domain_docs = [d for d in docs
                       if (d.get("DOMAIN") or "construction").lower() == _active_domain]
        if domain_docs:
            import pandas as pd
            df_docs = pd.DataFrame(domain_docs[:20])
            status_map = {
                "PARSED": "✅", "PROCESSED": "✅", "SUCCESS": "✅",
                "UPLOADED": "⏳", "FAILED": "❌", "UNSUPPORTED": "⚠️",
            }
            df_show = pd.DataFrame({
                "📄 Document": [d.get("FILE_NAME", "")[:30] for d in domain_docs[:20]],
                "Type": [str(d.get("FILE_TYPE", "")).upper()[:6] for d in domain_docs[:20]],
                "Status": [status_map.get(str(d.get("STATUS", "")).upper(), "❓")
                           for d in domain_docs[:20]],
            })
            st.dataframe(df_show, use_container_width=True, hide_index=True,
                         height=min(35 * len(df_show) + 38, 280))
    else:
        st.caption("No documents yet — upload files above.")


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
