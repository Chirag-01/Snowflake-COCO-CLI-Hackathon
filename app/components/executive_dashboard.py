# Risk Command Center Streamlit component (executive_dashboard tab).
# Co-authored with CoCo
"""
Tab 1: Executive Dashboard — Portfolio KPIs, health scores, and alerts.
"""

import streamlit as st
import pandas as pd
from app.utils.snowflake_client import SnowflakeClient

try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False


def render(client: SnowflakeClient):
    """Render the Executive Dashboard tab."""

    st.header("📊 Executive Overview")
    st.caption("Portfolio-wide intelligence at a glance")

    # ─── Portfolio Summary KPIs ───────────────────────────────────────────
    projects_risk = client.get_project_risk_summary()
    projects_financial = client.get_financial_summary()
    
    if projects_risk and projects_financial:
        total_budget = sum([p.get('CURRENT_BUDGET', 0) for p in projects_risk])
        total_variance = sum([p.get('COST_VARIANCE', 0) for p in projects_risk])
        avg_completion = sum([p.get('PERCENT_COMPLETE', 0) for p in projects_risk]) / len(projects_risk) if projects_risk else 0
        behind_schedule = sum([1 for p in projects_risk if p.get('SCHEDULE_STATUS') in ('Critical', 'At Risk')])
        over_budget = sum([1 for p in projects_risk if p.get('COST_STATUS') in ('Critical', 'At Risk') or (p.get('COST_VARIANCE') or 0) > 0])
        
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Portfolio Value", f"${total_budget:,.0f}")
        col2.metric("Forecast Variance",
                     f"${total_variance:,.0f}",
                     delta=f"{total_variance / max(total_budget, 1) * 100:.1f}%",
                     delta_color="inverse")
        col3.metric("Avg Completion", f"{avg_completion:.1f}%")
        col4.metric("Behind Schedule", f"{behind_schedule} projects")
        col5.metric("Over Budget", f"{over_budget} projects")

    st.divider()

    # ─── Project Cards ────────────────────────────────────────────────────
    if not projects_risk:
        st.info("No project data available. Upload documents and run the pipeline to begin.")
        return

    st.subheader("🏗️ Project Portfolio")

    for proj in projects_risk:
        health = proj.get("OVERALL_RISK_LEVEL", "LOW")
        health_color = "#DC2626" if health == "CRITICAL" else "#D97706" if health == "HIGH" else "#16A34A"

        with st.container():
            h_col, d_col1, d_col2, d_col3, d_col4, d_col5, d_col6 = st.columns([2, 1, 1, 1, 1, 1, 1])

            sched_st = proj.get('SCHEDULE_STATUS') or ''
            cost_st  = proj.get('COST_STATUS') or 'On Budget'
            # Build caption only from non-empty fields
            caption_parts = [p for p in [sched_st, cost_st] if p and p.lower() not in ('none','n/a','')]
            caption = " • ".join(caption_parts) if caption_parts else "On Budget"

            with h_col:
                st.markdown(f"### {proj.get('PROJECT_NAME', 'Unknown')}")
                st.caption(caption)

            d_col1.metric("Risk Level", f"{health}")
            d_col2.metric("Complete", f"{proj.get('PERCENT_COMPLETE') or 0:.0f}%")
            d_col3.metric("Contract", f"${proj.get('CURRENT_BUDGET') or 0:,.0f}")
            d_col4.metric("Open Risks", proj.get("TOTAL_RISKS") or 0)
            d_col5.metric("Risk Exposure", f"${proj.get('TOTAL_RISK_EXPOSURE') or 0:,.0f}")
            d_col6.metric("Sch Variance", f"{proj.get('SCHEDULE_VARIANCE_DAYS') or 0}d")

            # Alert badges
            alerts = []
            if proj.get("HIGH_CRITICAL_RISKS", 0) > 0:
                alerts.append(f"🔴 {proj['HIGH_CRITICAL_RISKS']} High/Critical Risks")
            
            # Find financial data for this project
            fin = next((f for f in projects_financial if f.get("PROJECT_ID") == proj.get("PROJECT_ID")), None)
            if fin:
                if fin.get("ACTIVE_SUBCONTRACTS", 0) > 0:
                    alerts.append(f"💼 {fin['ACTIVE_SUBCONTRACTS']} Subcontracts")
                if fin.get("TOTAL_CHANGE_ORDERS", 0) > 0:
                    alerts.append(f"📝 ${fin['TOTAL_CHANGE_ORDERS']:,.0f} Change Orders")

            if alerts:
                st.markdown(" • ".join(alerts))

    st.divider()

    # ─── Financial Exposure Chart ─────────────────────────────────────────
    st.subheader("💰 Financial Exposure by Project")

    if projects_risk:
        names = [d.get("PROJECT_NAME", "") for d in projects_risk]
        overrun = [d.get("COST_VARIANCE", 0) for d in projects_risk]
        risk_exp = [d.get("TOTAL_RISK_EXPOSURE", 0) for d in projects_risk]

        if HAS_PLOTLY:
            fig = go.Figure()
            fig.add_trace(go.Bar(name="Cost Variance", x=names, y=overrun, marker_color="#F59E0B"))
            fig.add_trace(go.Bar(name="Risk Exposure", x=names, y=risk_exp, marker_color="#8B5CF6"))
            fig.update_layout(
                barmode="stack",
                title="Financial Exposure Breakdown",
                yaxis_title="Exposure ($)",
                height=400,
                template=st.session_state.get("plotly_template", "plotly_dark"),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            df = pd.DataFrame({"Project": names, "Cost Variance": overrun, "Risk Exposure": risk_exp})
            st.bar_chart(df.set_index("Project"))

    # ─── Risk Signals Summary ─────────────────────────────────────────────
    st.subheader("⚠️ Active Risk Signals")

    risks = client.get_unified_risk_matrix()
    if risks:
        for r in risks[:8]:
            severity = r.get("SEVERITY") or "Low"
            sev_icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(severity.upper(), "⚪")

            st.markdown(
                f"{sev_icon} **{r.get('RISK_TITLE', 'Unknown Risk')}** — "
                f"{r.get('PROJECT_NAME', '')} • ${r.get('TOTAL_FINANCIAL_EXPOSURE', 0):,.0f} • "
                f"Category: {r.get('RISK_CATEGORY', '')}"
            )
    else:
        st.success("✅ No active risk signals. Portfolio is healthy.")
