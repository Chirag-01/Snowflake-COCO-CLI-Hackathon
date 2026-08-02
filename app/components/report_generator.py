# Report generator with embedded Plotly charts, HTML tables, Overview Charts, and domain-config support.
# Co-authored with CoCo
"""
Tab 7: Auto-Generated Reports + Overview Charts.
Generates AI-powered reports with live charts and tables, rendered as styled HTML.
"""

import base64
import io
import streamlit as st
import pandas as pd
from app.utils.snowflake_client import SnowflakeClient
from app.config.domain_loader import get_cfg

# ── Chart helpers ─────────────────────────────────────────────────────────────

def _make_risk_by_category(risk_data: list[dict]):
    try:
        import plotly.express as px
        df = pd.DataFrame(risk_data)
        if df.empty or "RISK_CATEGORY" not in df.columns:
            return None
        cat_counts = df.groupby("RISK_CATEGORY").size().reset_index(name="COUNT")
        cat_counts = cat_counts.sort_values("COUNT", ascending=False).head(10)
        fig = px.bar(cat_counts, x="RISK_CATEGORY", y="COUNT",
                     color="COUNT", color_continuous_scale="Reds",
                     title="Risk Count by Category", labels={"RISK_CATEGORY": "Category", "COUNT": "Risks"})
        fig.update_layout(showlegend=False, margin=dict(l=0, r=0, t=40, b=0), font=dict(color="#e2e8f0"),
                          height=320, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        return fig
    except Exception:
        return None


def _make_exposure_by_project(projects: list[dict]):
    try:
        import plotly.express as px
        df = pd.DataFrame(projects)
        if df.empty:
            return None
        col = next((c for c in ("TOTAL_RISK_EXPOSURE", "TOTAL_COMBINED_EXPOSURE") if c in df.columns), None)
        if not col:
            return None
        df = df[df[col] > 0].nlargest(10, col)
        fig = px.bar(df, x="PROJECT_NAME" if "PROJECT_NAME" in df.columns else df.index,
                     y=col, color=col, color_continuous_scale="Blues",
                     title="Financial Exposure by Project ($)",
                     labels={col: "Exposure ($)", "PROJECT_NAME": ""})
        fig.update_layout(showlegend=False, margin=dict(l=0, r=0, t=40, b=0), font=dict(color="#e2e8f0"),
                          height=320, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        return fig
    except Exception:
        return None


def _make_severity_donut(risk_data: list[dict]):
    try:
        import plotly.express as px
        df = pd.DataFrame(risk_data)
        if df.empty or "SEVERITY" not in df.columns:
            return None
        sev = df["SEVERITY"].value_counts().reset_index()
        sev.columns = ["Severity", "Count"]
        color_map = {"Critical": "#DC2626", "High": "#F97316", "Medium": "#FBBF24", "Low": "#22C55E"}
        fig = px.pie(sev, names="Severity", values="Count",
                     color="Severity", color_discrete_map=color_map,
                     hole=0.55, title="Risks by Severity")
        fig.update_layout(margin=dict(l=0, r=0, t=40, b=0), font=dict(color="#e2e8f0"), height=320,
                          paper_bgcolor="rgba(0,0,0,0)")
        return fig
    except Exception:
        return None


def _make_project_progress(projects: list[dict]):
    try:
        import plotly.express as px
        df = pd.DataFrame(projects)
        if df.empty:
            return None
        for c in ("PERCENT_COMPLETE", "PROJECT_NAME"):
            if c not in df.columns:
                return None
        df = df[df["PERCENT_COMPLETE"].notna()].head(10)
        df["PERCENT_COMPLETE"] = pd.to_numeric(df["PERCENT_COMPLETE"], errors="coerce").fillna(0)
        df = df.sort_values("PERCENT_COMPLETE")
        colors = ["#22C55E" if v >= 75 else "#FBBF24" if v >= 40 else "#DC2626"
                  for v in df["PERCENT_COMPLETE"]]
        fig = px.bar(df, x="PERCENT_COMPLETE", y="PROJECT_NAME", orientation="h",
                     title="Project Completion (%)", color="PERCENT_COMPLETE",
                     color_continuous_scale=[[0, "#DC2626"], [0.4, "#FBBF24"], [1, "#22C55E"]],
                     range_x=[0, 100])
        fig.update_layout(showlegend=False, margin=dict(l=0, r=0, t=40, b=0), font=dict(color="#e2e8f0"),
                          height=320, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        return fig
    except Exception:
        return None


def _make_vendor_chart(vendors: list[dict]):
    try:
        import plotly.express as px
        df = pd.DataFrame(vendors)
        if df.empty or "VENDOR_NAME" not in df.columns:
            return None
        score_col = next((c for c in ("VENDOR_RISK_SCORE", "COMPOSITE_SCORE") if c in df.columns), None)
        if not score_col:
            return None
        df = df.nlargest(10, score_col)
        fig = px.bar(df, x=score_col, y="VENDOR_NAME", orientation="h",
                     color=score_col, color_continuous_scale="OrRd",
                     title="Top Vendor Risk Scores")
        fig.update_layout(showlegend=False, margin=dict(l=0, r=0, t=40, b=0), font=dict(color="#e2e8f0"),
                          height=320, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        return fig
    except Exception:
        return None


def _make_risk_category_treemap(risk_data: list[dict]):
    try:
        import plotly.express as px
        df = pd.DataFrame(risk_data)
        if df.empty:
            return None
        needed = {"PROJECT_NAME", "RISK_CATEGORY", "TOTAL_FINANCIAL_EXPOSURE"}
        if not needed.issubset(df.columns):
            return None
        df["TOTAL_FINANCIAL_EXPOSURE"] = pd.to_numeric(
            df["TOTAL_FINANCIAL_EXPOSURE"], errors="coerce").fillna(1000)
        df = df[df["TOTAL_FINANCIAL_EXPOSURE"] > 0]
        if df.empty:
            return None
        fig = px.treemap(df, path=["PROJECT_NAME", "RISK_CATEGORY"],
                         values="TOTAL_FINANCIAL_EXPOSURE",
                         color="TOTAL_FINANCIAL_EXPOSURE",
                         color_continuous_scale="Reds",
                         title="Risk Exposure Treemap by Project & Category ($)")
        fig.update_layout(margin=dict(l=0, r=0, t=40, b=0), font=dict(color="#e2e8f0"), height=380,
                          paper_bgcolor="rgba(0,0,0,0)")
        return fig
    except Exception:
        return None


def _fig_to_html_div(fig) -> str:
    """Convert a plotly figure to HTML for report — forces light theme (dark text on white)."""
    try:
        import plotly.io as pio
        import copy
        fig2 = copy.deepcopy(fig)
        fig2.update_layout(
            paper_bgcolor="white",
            plot_bgcolor="#f8fafc",
            font=dict(color="#1e293b", family="Inter, Arial, sans-serif"),
            title_font=dict(color="#1e3a5f"),
        )
        return pio.to_html(fig2, full_html=False, include_plotlyjs=False,
                           config={"displayModeBar": False})
    except Exception:
        return ""


def _df_to_html_table(df: pd.DataFrame, max_rows: int = 20) -> str:
    """Convert a DataFrame to a styled HTML table."""
    df = df.head(max_rows)
    rows = ""
    for _, row in df.iterrows():
        cells = "".join(f"<td>{v}</td>" for v in row)
        rows += f"<tr>{cells}</tr>"
    headers = "".join(f"<th>{c}</th>" for c in df.columns)
    return f"""<table class="data-table">
<thead><tr>{headers}</tr></thead>
<tbody>{rows}</tbody>
</table>"""


# ── HTML Report Builder ───────────────────────────────────────────────────────

def _md_to_html_body(text: str) -> str:
    """Convert markdown text to clean HTML — strips stray #, *, and escape sequences."""
    import re
    # Clean LLM artefacts
    text = text.replace('\\n', '\n').replace('\\t+', '\n• ').replace('\\t', '  ')
    text = re.sub(r'\t\+\s*', '• ', text)
    text = re.sub(r'^\t', '', text, flags=re.MULTILINE)
    # Remove stray backslash sequences
    text = re.sub(r'\\([^n])', r'\1', text)

    lines = text.split('\n')
    out, in_list = [], False

    for line in lines:
        line = line.rstrip()
        stripped = line.strip()
        if not stripped:
            if in_list:
                out.append('</ul>'); in_list = False
            continue
        # Headers — strip leading # chars
        if stripped.startswith('#### '):
            if in_list: out.append('</ul>'); in_list = False
            out.append(f'<h4>{_inline(stripped[5:])}</h4>')
        elif stripped.startswith('### '):
            if in_list: out.append('</ul>'); in_list = False
            out.append(f'<h3>{_inline(stripped[4:])}</h3>')
        elif stripped.startswith('## '):
            if in_list: out.append('</ul>'); in_list = False
            out.append(f'<h2>{_inline(stripped[3:])}</h2>')
        elif stripped.startswith('# '):
            if in_list: out.append('</ul>'); in_list = False
            out.append(f'<h2>{_inline(stripped[2:])}</h2>')  # # → h2, not h1 (cover already is h1)
        elif stripped.startswith(('- ', '* ', '+ ', '• ')):
            if not in_list:
                out.append('<ul>'); in_list = True
            content = _inline(re.sub(r'^[-\*\+•]\s+', '', stripped))
            out.append(f'<li>{content}</li>')
        elif stripped.startswith('**') and stripped.endswith('**') and len(stripped) > 4:
            if in_list: out.append('</ul>'); in_list = False
            out.append(f'<p class="bold-line">{_inline(stripped[2:-2])}</p>')
        else:
            if in_list: out.append('</ul>'); in_list = False
            out.append(f'<p>{_inline(stripped)}</p>')

    if in_list:
        out.append('</ul>')
    return '\n'.join(out)


def _inline(text: str) -> str:
    """Apply inline markdown: **bold**, _italic_, remove stray chars."""
    import re
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.*?)\*',   r'<em>\1</em>',          text)
    text = re.sub(r'_(.*?)_',     r'<em>\1</em>',          text)
    # Remove lone # or * that aren't part of markdown
    text = re.sub(r'(?<!\w)#(?!\w)', '', text)
    return text.strip()


def _to_html_report(md_text: str, report_title: str,
                    chart_htmls: list[tuple[str, str]] = None,
                    table_htmls: list[tuple[str, str]] = None,
                    cfg: dict = None) -> str:
    """Build a multi-tab HTML report with charts, tables, and AI narrative."""
    cover_title = (cfg or {}).get("report", {}).get("cover_title", "Enterprise Risk Command Center")
    gen_date    = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')
    body_html   = _md_to_html_body(md_text)

    # ── Chart tab ────────────────────────────────────────────────────────
    if chart_htmls:
        pairs = [chart_htmls[i:i+2] for i in range(0, len(chart_htmls), 2)]
        chart_rows = ""
        for pair in pairs:
            chart_rows += '<div class="chart-row">'
            for title, div in pair:
                chart_rows += (
                    f'<div class="chart-box">'
                    f'<div class="chart-label">{title}</div>'
                    f'{div}'
                    f'</div>'
                )
            # pad odd row
            if len(pair) == 1:
                chart_rows += '<div class="chart-box chart-empty"></div>'
            chart_rows += '</div>'
        charts_tab_content = f'<section id="tab-charts" class="tab-pane">{chart_rows}</section>'
        charts_tab_btn = '<button class="tab-btn" onclick="showTab(\'charts\')">📊 Charts</button>'
    else:
        charts_tab_content = ''
        charts_tab_btn = ''

    # ── Tables tab ────────────────────────────────────────────────────────
    if table_htmls:
        tables_inner = ""
        for title, tbl in table_htmls:
            tables_inner += f'<div class="table-wrap"><div class="section-title">{title}</div>{tbl}</div>'
        tables_tab_content = f'<section id="tab-tables" class="tab-pane">{tables_inner}</section>'
        tables_tab_btn = '<button class="tab-btn" onclick="showTab(\'tables\')">📋 Tables</button>'
    else:
        tables_tab_content = ''
        tables_tab_btn = ''

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{cover_title} — {report_title}</title>
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:'Inter',Arial,sans-serif;background:#f0f4f8;color:#1e293b;min-height:100vh}}

  /* ── Cover ─────────────────────────────────────────── */
  .cover{{background:linear-gradient(135deg,#1e3a5f 0%,#1d4ed8 60%,#0891b2 100%);
          color:#fff;padding:56px 60px 48px;position:relative}}
  .cover h1{{font-size:1.75rem;font-weight:700;letter-spacing:-.01em;margin-bottom:6px}}
  .cover .sub{{font-size:1.1rem;opacity:.9;margin-bottom:24px;font-weight:500}}
  .cover .meta{{font-size:.8rem;opacity:.75;display:flex;gap:12px;flex-wrap:wrap}}
  .badge{{background:rgba(255,255,255,.15);border-radius:20px;padding:4px 14px;
          backdrop-filter:blur(4px)}}
  .print-btn{{position:absolute;top:24px;right:24px;background:rgba(255,255,255,.2);
              color:#fff;border:1px solid rgba(255,255,255,.4);padding:8px 18px;
              border-radius:8px;font-size:.85rem;cursor:pointer;
              font-family:'Inter',sans-serif;backdrop-filter:blur(4px)}}
  .print-btn:hover{{background:rgba(255,255,255,.35)}}

  /* ── Tab bar ────────────────────────────────────────── */
  .tab-bar{{background:#fff;border-bottom:2px solid #e2e8f0;display:flex;gap:0;
            position:sticky;top:0;z-index:100;box-shadow:0 1px 4px rgba(0,0,0,.06)}}
  .tab-btn{{padding:14px 28px;background:none;border:none;border-bottom:3px solid transparent;
            font-size:.9rem;font-weight:500;color:#64748b;cursor:pointer;
            font-family:'Inter',sans-serif;transition:all .15s}}
  .tab-btn:hover{{color:#1d4ed8;background:#f8fafc}}
  .tab-btn.active{{color:#1d4ed8;border-bottom-color:#1d4ed8;font-weight:600}}

  /* ── Tab panes ──────────────────────────────────────── */
  .tab-pane{{display:none;padding:40px 60px;max-width:1100px;margin:0 auto;
             animation:fadeIn .2s ease}}
  .tab-pane.active{{display:block}}
  @keyframes fadeIn{{from{{opacity:0;transform:translateY(4px)}}to{{opacity:1;transform:none}}}}

  /* ── Narrative ──────────────────────────────────────── */
  h2{{font-size:1.25rem;color:#1e3a5f;font-weight:700;
      border-left:4px solid #1d4ed8;padding-left:14px;
      margin:32px 0 14px}}
  h3{{font-size:1.05rem;color:#334155;font-weight:600;margin:22px 0 8px}}
  h4{{font-size:.95rem;color:#475569;font-weight:600;margin:16px 0 6px}}
  p{{color:#334155;line-height:1.75;margin:8px 0}}
  ul{{margin:8px 0 12px 24px}}
  li{{color:#334155;line-height:1.7;margin:4px 0;list-style:disc}}
  strong,.bold-line{{color:#1e293b;font-weight:600}}
  .bold-line{{display:block;margin:10px 0 4px}}

  /* ── Charts ─────────────────────────────────────────── */
  .chart-row{{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:20px}}
  .chart-box{{background:#fff;border-radius:12px;padding:18px;
              box-shadow:0 1px 6px rgba(0,0,0,.08);min-height:200px}}
  .chart-box.chart-empty{{background:transparent;box-shadow:none}}
  .chart-label{{font-size:.78rem;font-weight:600;color:#64748b;
                text-transform:uppercase;letter-spacing:.05em;margin-bottom:10px}}

  /* ── Tables ─────────────────────────────────────────── */
  .table-wrap{{background:#fff;border-radius:12px;padding:24px;margin:20px 0;
               box-shadow:0 1px 6px rgba(0,0,0,.08);overflow-x:auto}}
  .section-title{{font-size:.85rem;font-weight:600;color:#64748b;
                  text-transform:uppercase;letter-spacing:.05em;margin-bottom:14px}}
  .data-table{{width:100%;border-collapse:collapse;font-size:.84rem}}
  .data-table th{{background:#1e3a5f;color:#fff;padding:9px 14px;
                  text-align:left;font-weight:600}}
  .data-table td{{padding:8px 14px;border-bottom:1px solid #e2e8f0;color:#334155}}
  .data-table tr:nth-child(even){{background:#f8fafc}}
  .data-table tr:hover{{background:#eff6ff}}

  /* ── Footer ─────────────────────────────────────────── */
  .footer{{background:#1e293b;color:#94a3b8;padding:20px 60px;
           font-size:.78rem;text-align:center;margin-top:60px}}

  /* ── Print ──────────────────────────────────────────── */
  @media print{{
    .print-btn,.tab-bar{{display:none!important}}
    .tab-pane{{display:block!important;padding:24px 40px}}
    .cover{{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
    .chart-row{{page-break-inside:avoid}}
    .table-wrap{{page-break-inside:avoid}}
  }}
</style>
<script>
function showTab(id){{
  document.querySelectorAll('.tab-pane').forEach(p=>p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b=>b.classList.remove('active'));
  var pane=document.getElementById('tab-'+id);
  if(pane)pane.classList.add('active');
  event.target.classList.add('active');
}}
window.onload=function(){{showTab('narrative');}};
</script>
</head>
<body>
<div class="cover">
  <button class="print-btn" onclick="window.print()">🖨️ Save as PDF</button>
  <h1>{cover_title}</h1>
  <div class="sub">{report_title}</div>
  <div class="meta">
    <span class="badge">📅 {gen_date}</span>
    <span class="badge">🔒 Confidential</span>
    <span class="badge">Powered by Snowflake Cortex AI</span>
  </div>
</div>

<div class="tab-bar">
  <button class="tab-btn active" onclick="showTab('narrative')">📝 Report</button>
  {charts_tab_btn}
  {tables_tab_btn}
</div>

<section id="tab-narrative" class="tab-pane active">
  {body_html}
</section>

{charts_tab_content}
{tables_tab_content}

<div class="footer">
  {cover_title} &nbsp;•&nbsp; Powered by Snowflake Cortex AI &nbsp;•&nbsp; Confidential
</div>
</body>
</html>"""


# ── Overview Charts Panel ─────────────────────────────────────────────────────

def render_overview_charts(client: SnowflakeClient):
    """Standalone overview charts section — call from report tab or separate tab."""
    st.subheader("📊 Portfolio Overview Charts")
    st.caption("Live charts from Gold views — refreshed on page load")

    with st.spinner("Loading chart data..."):
        risk_data   = client.get_unified_risk_matrix()
        projects    = client.get_project_risk_summary()
        vendors     = client.get_vendor_risk_ranking()
        fin_data    = client.get_financial_exposure()

    if not risk_data and not projects:
        st.info("No data yet. Run the pipeline first to populate charts.")
        return

    # Row 1: severity donut + category bar
    figs_r1 = [
        ("ov_sev", _make_severity_donut(risk_data)),
        ("ov_cat", _make_risk_by_category(risk_data)),
    ]
    r1_figs = [(k, f) for k, f in figs_r1 if f]
    if r1_figs:
        cols = st.columns(len(r1_figs))
        for col, (key, fig) in zip(cols, r1_figs):
            col.plotly_chart(fig, use_container_width=True, key=key)

    # Row 2: exposure by project + completion
    figs_r2 = [
        ("ov_exp",  _make_exposure_by_project(fin_data or projects)),
        ("ov_prog", _make_project_progress(projects)),
    ]
    r2_figs = [(k, f) for k, f in figs_r2 if f]
    if r2_figs:
        cols = st.columns(len(r2_figs))
        for col, (key, fig) in zip(cols, r2_figs):
            col.plotly_chart(fig, use_container_width=True, key=key)

    # Row 3: vendor risk + treemap
    figs_r3 = [
        ("ov_ven",  _make_vendor_chart(vendors)),
        ("ov_tree", _make_risk_category_treemap(risk_data)),
    ]
    r3_figs = [(k, f) for k, f in figs_r3 if f]
    if r3_figs:
        cols = st.columns(len(r3_figs))
        for col, (key, fig) in zip(cols, r3_figs):
            col.plotly_chart(fig, use_container_width=True, key=key)

    # Summary KPI bar
    if projects:
        df_proj = pd.DataFrame(projects)
        total_exp = sum(
            float(p.get("TOTAL_RISK_EXPOSURE") or 0) for p in projects
        )
        critical_cnt = sum(
            1 for r in risk_data
            if str(r.get("SEVERITY", "")).lower() in ("critical", "high")
        )
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total Projects",    len(projects))
        k2.metric("Total Risk Events", len(risk_data))
        k3.metric("High/Critical Risks", critical_cnt)
        k4.metric("Total Exposure ($M)", f"${total_exp/1e6:.1f}M" if total_exp else "—")


# ── Main Render ───────────────────────────────────────────────────────────────

def render(client: SnowflakeClient):
    """Render the Reports tab with Overview Charts + AI Report Generator."""
    cfg = get_cfg()
    st.header("📝 Reports & Analytics")

    tab_charts, tab_generate = st.tabs(["📊 Overview Charts", "✨ Generate Report"])

    # ── Tab 1: Overview Charts ──────────────────────────────────────────────
    with tab_charts:
        render_overview_charts(client)

    # ── Tab 2: Report Generator ─────────────────────────────────────────────
    with tab_generate:
        st.subheader("AI-Generated Report")
        st.caption("AI generates a professional narrative using live risk data")

        # Report type list from config
        rpt_types = cfg["report"]["report_types"]
        rpt_id_map = {r["id"]: r["label"] for r in rpt_types}

        col1, col2 = st.columns(2)
        with col1:
            report_type = st.selectbox(
                "Report Type",
                [r["id"] for r in rpt_types],
                format_func=lambda x: rpt_id_map.get(x, x),
                key="rg_type"
            )
        with col2:
            projects_list = client.get_projects()
            project_options = {"Portfolio-Level (All Projects)": None}
            project_options.update({p["PROJECT_NAME"]: p["PROJECT_ID"] for p in projects_list})
            selected_proj = st.selectbox("Project Filter", list(project_options.keys()), key="rg_proj")
            project_id = project_options[selected_proj]

        include_charts = st.checkbox("Embed charts in downloaded report", value=True)

        if st.button("✨ Generate Report", use_container_width=True):
            # Step 1: fetch all data once (fast)
            with st.spinner("📊 Loading data..."):
                rpt_risk     = client.get_unified_risk_matrix()
                rpt_projects = client.get_project_risk_summary()
                rpt_vendors  = client.get_vendor_risk_ranking()
                rpt_fin      = client.get_financial_exposure(project_id)
            # Step 2: AI narrative (slow — happens once)
            with st.spinner("🧠 Generating AI narrative..."):
                report_text = client.generate_report(report_type, project_id)
            st.session_state.update({
                "generated_report":        report_text,
                "generated_report_type":   report_type,
                "generated_report_projid": project_id,
                "rpt_risk":     rpt_risk,
                "rpt_projects": rpt_projects,
                "rpt_vendors":  rpt_vendors,
                "rpt_fin":      rpt_fin,
            })

        if st.session_state.get("generated_report"):
            report_text  = st.session_state["generated_report"]
            report_title = st.session_state["generated_report_type"].replace("_", " ").title()
            proj_id_used = st.session_state.get("generated_report_projid")

            # Reuse cached data — no re-query
            risk_data = st.session_state.get("rpt_risk", [])
            projects  = st.session_state.get("rpt_projects", [])
            vendors   = st.session_state.get("rpt_vendors", [])
            fin_data  = st.session_state.get("rpt_fin", [])

            st.success("Report generated.")
            st.divider()

            # Build charts once from cached data
            chart_fns = [
                (_make_severity_donut,      "Risks by Severity",              risk_data),
                (_make_risk_by_category,    "Risk Count by Category",         risk_data),
                (_make_exposure_by_project, "Financial Exposure by Project", fin_data or projects),
                (_make_project_progress,    "Project Completion %",           projects),
            ]
            if report_type == "VENDOR_PERFORMANCE":
                chart_fns.append((_make_vendor_chart, "Vendor Risk Scores", vendors))

            built_figs = []  # list of (label, fig)
            chart_htmls = []
            for fn, lbl, data in chart_fns:
                try:
                    fig = fn(data)
                    if fig:
                        built_figs.append((lbl, fig))
                        if include_charts:
                            chart_htmls.append((lbl, _fig_to_html_div(fig)))
                except Exception:
                    pass

            # Tables for HTML
            table_htmls = []
            if include_charts:
                if risk_data:
                    df_r = pd.DataFrame(risk_data)
                    cols_r = [c for c in ["PROJECT_NAME","RISK_TITLE","SEVERITY","RISK_CATEGORY","TOTAL_FINANCIAL_EXPOSURE"] if c in df_r.columns]
                    if cols_r:
                        table_htmls.append(("Top Risk Events", _df_to_html_table(df_r[cols_r].head(15))))
                if projects:
                    df_p = pd.DataFrame(projects)
                    cols_p = [c for c in ["PROJECT_NAME","PERCENT_COMPLETE","TOTAL_RISK_EXPOSURE","COST_STATUS"] if c in df_p.columns]
                    if cols_p:
                        table_htmls.append(("Project Summary", _df_to_html_table(df_p[cols_p])))

            # Preview tabs
            prev_text, prev_data = st.tabs(["📝 AI Narrative", "📊 Charts Preview"])

            with prev_text:
                st.info(report_text.replace('\\n', '\n'))

            with prev_data:
                if built_figs:
                    pairs = [built_figs[i:i+2] for i in range(0, len(built_figs), 2)]
                    for pair in pairs:
                        cols = st.columns(len(pair))
                        for col, (lbl, fig) in zip(cols, pair):
                            col.plotly_chart(fig, use_container_width=True, key="rp_" + lbl[:8])
                else:
                    st.info("No chart data available. Run the pipeline to populate data.")

            st.divider()

            html_content = _to_html_report(
                report_text, report_title,
                chart_htmls=chart_htmls or None,
                table_htmls=table_htmls or None,
                cfg=cfg,
            )

            dl1, dl2 = st.columns(2)
            with dl1:
                st.download_button(
                    label="📥 Download Full Report (HTML)",
                    data=html_content.encode("utf-8"),
                    file_name=report_type.lower() + "_report.html",
                    mime="text/html",
                    use_container_width=True,
                )
            with dl2:
                st.download_button(
                    label="📄 Download Markdown",
                    data=report_text.replace('\\n', '\n').encode("utf-8"),
                    file_name=report_type.lower() + "_report.md",
                    mime="text/markdown",
                    use_container_width=True,
                )

        st.divider()
        st.subheader("📚 Report Registry")
        past_reports = client.query("""
            SELECT REPORT_ID, REPORT_NAME, CREATED_BY, CREATED_AT
            FROM RISK_COMMAND_CENTER.GOLD.REPORT_REGISTRY
            ORDER BY CREATED_AT DESC LIMIT 10
        """)
        if past_reports:
            st.dataframe(pd.DataFrame(past_reports), use_container_width=True)
        else:
            st.info("No reports saved to registry yet.")
