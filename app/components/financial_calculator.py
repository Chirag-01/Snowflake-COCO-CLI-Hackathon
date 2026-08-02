# Financial Impact Calculator component — domain-config driven labels and descriptions.
# Co-authored with CoCo
"""
Tab 5: Financial Impact Calculator — Full financial exposure analysis.
Uses real LD rates, cost overruns, scenario projections, and claim values.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from app.utils.snowflake_client import SnowflakeClient
from app.config.domain_loader import get_cfg


def render(client: SnowflakeClient):
    """Render the Financial Impact Calculator tab."""
    cfg = get_cfg()

    st.header(cfg["ui"]["financial_tab_header"])
    st.caption(cfg["ui"]["financial_tab_caption"])

    # ─── Portfolio Financial KPIs ─────────────────────────────────────────
    exposure_data = client.get_financial_exposure()

    if not exposure_data:
        st.info("No financial data available. Load structured data first.")
        return

    total_overrun = sum(d.get("COST_OVERRUN", 0) or 0 for d in exposure_data)
    total_ld = sum(d.get("LD_EXPOSURE", 0) or 0 for d in exposure_data)
    total_risk = sum(d.get("TOTAL_RISK_EXPOSURE", 0) or 0 for d in exposure_data)
    total_combined = sum(d.get("TOTAL_COMBINED_EXPOSURE", 0) or 0 for d in exposure_data)
    total_held = sum(d.get("PAYMENT_HELD_AMOUNT", 0) or 0 for d in exposure_data)

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Cost Overrun",               f"${total_overrun:,.0f}",
                help="Actual cost exceeding the approved budget")
    col2.metric(cfg["ui"]["ld_label"],        f"${total_ld:,.0f}",
                help=cfg["ui"]["ld_metric_help"])
    col3.metric("Risk Event Exposure",        f"${total_risk:,.0f}",
                help="Financial impact of open risk events")
    col4.metric("Payment Held",               f"${total_held:,.0f}",
                help="Amounts withheld (retention / disputes)")
    col5.metric("⚠️ Total Exposure",          f"${total_combined:,.0f}",
                help="Sum of all financial exposure categories")

    st.divider()

    # ─── Project Selector ─────────────────────────────────────────────────
    st.subheader(f"📊 {cfg['entity']['project'].title()}-Level Financial Analysis")

    project_options = {
        f"{d['PROJECT_NAME']} (Exposure: ${d.get('TOTAL_COMBINED_EXPOSURE') or 0:,.0f})": d["PROJECT_ID"]
        for d in exposure_data
    }

    selected_label = st.selectbox(f"Select {cfg['entity']['project'].lower()}:", list(project_options.keys()))
    selected_project = project_options[selected_label]

    # Get project detail
    proj = next((d for d in exposure_data if d["PROJECT_ID"] == selected_project), {})

    # ─── Project Financial Breakdown ──────────────────────────────────────
    with st.container():
        st.markdown("### 📐 Financial Breakdown")

        r1, r2, r3, r4 = st.columns(4)
        r1.metric("Contract Value",
                  f"${proj.get('CURRENT_CONTRACT_VALUE') or 0:,.0f}",
                  help="Approved contract amount")
        r2.metric("Approved Budget",
                  f"${proj.get('CURRENT_BUDGET') or 0:,.0f}",
                  help="Internal cost budget (may differ from contract value)")
        r3.metric("Forecast at Completion",
                  f"${proj.get('FORECAST_COST_AT_COMPLETION') or 0:,.0f}",
                  help="Estimated total cost when project is finished")
        cost_overrun = proj.get('COST_OVERRUN') or 0
        current_budget = proj.get('CURRENT_BUDGET') or 1
        r4.metric("Cost Overrun",
                  f"${cost_overrun:,.0f}",
                  delta=f"{cost_overrun / max(current_budget, 1) * 100:.1f}% of budget",
                  delta_color="inverse",
                  help="Amount by which forecast exceeds budget")

    st.divider()

    # ─── Penalty Calculator ────────────────────────────────────────────────
    st.subheader(cfg["ui"]["ld_section_header"])

    ld_rate    = float(proj.get("LD_PER_DAY", 0) or 0)
    float_days = float(proj.get("CRITICAL_PATH_FLOAT_DAYS", 0) or 0)
    delay_days = int(abs(float_days)) if float_days < 0 else 0

    with st.container():
        st.markdown(f"**How this works:** {cfg['ui']['ld_description']}")
        st.caption(
            f"📐 Calculated {cfg['ui']['schedule_slack_label']}: **{float_days:+.0f} days** "
            f"({'behind' if float_days < 0 else 'ahead / on track'})"
        )

        # Interactive adjustments
        adj_col1, adj_col2 = st.columns(2)
        with adj_col1:
            adj_delay = st.number_input("Delay / Non-Compliance Days", value=delay_days, min_value=0, step=1)
        with adj_col2:
            adj_rate = st.number_input(f"{cfg['ui']['ld_label']} Rate ($/day)", value=ld_rate, min_value=0.0, step=1000.0)

        ld_total = adj_delay * adj_rate

        calc_col1, calc_col2, calc_col3, calc_col4 = st.columns(4)
        calc_col1.metric("Days", f"{adj_delay}")
        calc_col2.metric(f"{cfg['ui']['ld_label']} Rate", f"${adj_rate:,.0f}/day")
        calc_col3.metric(f"Gross {cfg['ui']['ld_label']}", f"${ld_total:,.0f}")

        # Waiver risk adjustment
        waiver_pct = st.slider("Waiver/Dispute Risk (%)", 0, 50, 10, 5)
        adjusted_ld = ld_total * (1 - waiver_pct / 100)
        calc_col4.metric(f"Risk-Adjusted {cfg['ui']['ld_label']}", f"${adjusted_ld:,.0f}")

        st.caption(f"📐 Formula: {adj_delay} days × ${adj_rate:,.0f}/day = ${ld_total:,.0f} gross → {waiver_pct}% dispute risk → ${adjusted_ld:,.0f} net")

    st.divider()

    # ─── Scenario Projections (What-If) ───────────────────────────────────
    st.subheader("🔮 Risk Scenario Projections")

    scenarios = client.get_risk_scenarios(selected_project)

    if scenarios:
        df_scenarios = pd.DataFrame(scenarios)

        # Group by scenario day
        if "SCENARIO_DAY" in df_scenarios.columns:
            grouped = df_scenarios.groupby("SCENARIO_DAY").agg({
                "ESTIMATED_COST_EXPOSURE": "sum",
                "ESTIMATED_SCHEDULE_SLIP_DAYS": "max",
            }).reset_index()

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=grouped["SCENARIO_DAY"],
                y=grouped["ESTIMATED_COST_EXPOSURE"],
                mode="lines+markers",
                name="Cost Exposure",
                line=dict(color="#EF4444", width=3),
                fill="tozeroy",
                fillcolor="rgba(239,68,68,0.1)",
            ))

            fig.update_layout(
                title="Cost Exposure if Risks Remain Unresolved",
                xaxis_title="Days Unresolved",
                yaxis_title="Estimated Cost Exposure ($)",
                height=350,
                template=st.session_state.get("plotly_template", "plotly_dark"),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig, use_container_width=True)

        # Scenario detail table
        for s in scenarios[:10]:
            trigger = s.get("TRIGGER_CONDITION", "")
            escalation = s.get("RECOMMENDED_ESCALATION", "")
            cost = s.get("ESTIMATED_COST_EXPOSURE", 0)
            slip = s.get("ESTIMATED_SCHEDULE_SLIP_DAYS", 0)

            with st.container():
                sc1, sc2, sc3 = st.columns([3, 1, 1])
                sc1.markdown(f"**{s.get('RISK_TITLE', 'Unknown')}** — Day {s.get('SCENARIO_DAY', 0)}")
                sc2.metric("Cost", f"${cost:,.0f}")
                sc3.metric("Schedule Slip", f"{slip} days")
                if trigger:
                    st.caption(f"Trigger: {trigger}")
                if escalation:
                    st.caption(f"Escalation: {escalation}")
    else:
        st.info("No high or critical risks to project for this selection.")

    st.divider()

    # ─── Exposure Waterfall Chart ─────────────────────────────────────────
    st.subheader("📈 Exposure Waterfall")

    labels = ["Budget", "Cost Overrun", "LD Exposure", "Risk Events", "Pending COs", "Payment Holds", "Total Exposure"]
    values = [
        proj.get("CURRENT_BUDGET", 0),
        proj.get("COST_OVERRUN", 0),
        proj.get("LD_EXPOSURE", 0),
        proj.get("TOTAL_RISK_EXPOSURE", 0),
        proj.get("PENDING_CO_TOTAL", 0),
        proj.get("PAYMENT_HELD_AMOUNT", 0),
        proj.get("TOTAL_COMBINED_EXPOSURE", 0),
    ]
    measures = ["absolute", "relative", "relative", "relative", "relative", "relative", "total"]

    fig2 = go.Figure(go.Waterfall(
        x=labels,
        y=values,
        measure=measures,
        text=[f"${v:,.0f}" for v in values],
        textposition="outside",
        connector={"line": {"color": "#64748B"}},
        increasing={"marker": {"color": "#EF4444"}},
        decreasing={"marker": {"color": "#22C55E"}},
        totals={"marker": {"color": "#8B5CF6"}},
    ))

    fig2.update_layout(
        title="Financial Exposure Waterfall",
        yaxis_title="Amount ($)",
        height=400,
        template=st.session_state.get("plotly_template", "plotly_dark"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig2, use_container_width=True)
