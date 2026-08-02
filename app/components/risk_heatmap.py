# Risk heatmap component — domain-config driven labels and categories.
# Co-authored with CoCo
"""
Tab 2: Risk Heatmap — Visual risk comparison across projects and categories.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from app.utils.snowflake_client import SnowflakeClient
from app.config.domain_loader import get_cfg


def render(client: SnowflakeClient):
    """Render the Risk Heatmap tab."""
    cfg = get_cfg()

    st.header("🗺️ Risk Heatmap")
    st.caption(f"Compare risk dimensions across all active {cfg['entity']['projects'].lower()}")

    # ─── Heatmap Data ─────────────────────────────────────────────────────
    heatmap_data = client.get_project_health()

    if not heatmap_data:
        st.info("No project risk data available. Upload documents to begin analysis.")
        return

    df = pd.DataFrame(heatmap_data)

    # ─── Interactive Heatmap ──────────────────────────────────────────────
    # Risk category columns and labels come from domain config
    risk_cat_cfg   = cfg["risk_categories"]                      # {COL: label}
    risk_categories = list(risk_cat_cfg.keys())
    category_labels = list(risk_cat_cfg.values())

    z_data = []
    for cat in risk_categories:
        z_data.append(df.get(cat, pd.Series([0] * len(df))).fillna(0).tolist())

    fig = go.Figure(data=go.Heatmap(
        z=z_data,
        x=df.get("PROJECT_NAME", pd.Series([])).tolist(),
        y=category_labels,
        colorscale="RdYlGn_r",
        showscale=True,
        hovertemplate="Project: %{x}<br>Category: %{y}<br>Risk Count: %{z}<extra></extra>",
        colorbar=dict(title="Risk Count"),
    ))

    fig.update_layout(
        title=f"Risk Heatmap — {cfg['entity']['projects']} × Risk Categories",
        height=400,
        template=st.session_state.get("plotly_template", "plotly_dark"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ─── Financial Exposure Bubble Chart ──────────────────────────────────
    st.subheader("💰 Financial Exposure by Project")

    fig2 = go.Figure()
    for _, row in df.iterrows():
        exposure = row.get("TOTAL_FINANCIAL_EXPOSURE", 0)
        severity = row.get("MAX_SEVERITY", "Low")
        color_map = {"Critical": "#EF4444", "High": "#F97316", "Medium": "#EAB308", "Low": "#22C55E"}

        fig2.add_trace(go.Scatter(
            x=[row.get("PERCENT_COMPLETE", 0)],
            y=[exposure],
            mode="markers+text",
            text=[row.get("PROJECT_NAME", "")],
            textposition="top center",
            marker=dict(
                size=max(20, min(80, exposure / 50000)),
                color=color_map.get(severity, "#6B7280"),
                opacity=0.8,
                line=dict(width=2, color="#FFFFFF"),
            ),
            name=row.get("PROJECT_NAME", ""),
            showlegend=False,
        ))

    fig2.update_layout(
        title="Completion vs Risk Exposure",
        xaxis_title="Percent Complete (%)",
        yaxis_title="Financial Exposure ($)",
        height=400,
        template=st.session_state.get("plotly_template", "plotly_dark"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    # ─── Risk Detail Table ────────────────────────────────────────────────
    st.subheader("📋 Detailed Risk Matrix")

    risk_cat_cfg = cfg["risk_categories"]

    # Build ordered (col, label) pairs for every column that actually exists in df
    col_label_map = {
        "PROJECT_NAME":              cfg["entity"]["project"].title(),
        "PERCENT_COMPLETE":          "% Complete",
        "CRITICAL_PATH_FLOAT_DAYS":  cfg["ui"]["schedule_slack_label"],
    }
    # Add risk category columns from config
    for col, lbl in risk_cat_cfg.items():
        col_label_map[col] = lbl
    col_label_map["TOTAL_FINANCIAL_EXPOSURE"] = "Total Exposure ($)"
    col_label_map["MAX_SEVERITY"] = "Worst Severity"

    # Only keep columns present in df — order matches the map insertion order
    present_pairs = [(col, lbl) for col, lbl in col_label_map.items() if col in df.columns]
    sel_cols   = [c for c, _ in present_pairs]
    new_names  = [l for _, l in present_pairs]

    display_df = df[sel_cols].copy()
    display_df.columns = new_names  # guaranteed same length

    # Format values
    for col, fmt in [
        ("Total Exposure ($)",           lambda x: f"${float(x):,.0f}" if pd.notna(x) and x else "$0"),
        ("% Complete",                   lambda x: f"{float(x):.0f}%" if pd.notna(x) else "0%"),
        (cfg["ui"]["schedule_slack_label"], lambda x: f"{float(x):+.0f}d" if pd.notna(x) and x else "—"),
    ]:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(fmt)

    st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.divider()

    # ─── Vendor Risk Ranking ──────────────────────────────────────────────
    st.subheader(cfg["ui"]["vendor_section"])

    vendor_data = client.get_vendor_risk_ranking()

    if vendor_data:
        vendor_df = pd.DataFrame(vendor_data[:10])

        fig3 = go.Figure(go.Bar(
            x=vendor_df.get("VENDOR_RISK_SCORE", pd.Series([])).tolist(),
            y=vendor_df.get("VENDOR_NAME", pd.Series([])).tolist(),
            orientation="h",
            marker=dict(
                color=vendor_df.get("VENDOR_RISK_SCORE", pd.Series([])).tolist(),
                colorscale="RdYlGn_r",
                showscale=False,
            ),
            text=vendor_df.get("VENDOR_RISK_SCORE", pd.Series([])).apply(lambda x: f"Score: {x:.0f}").tolist(),
            textposition="auto",
        ))

        fig3.update_layout(
            title=cfg["ui"]["vendor_chart_title"],
            xaxis_title="Risk Score",
            height=400,
            template=st.session_state.get("plotly_template", "plotly_dark"),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig3, use_container_width=True)

        # Vendor detail cards
        for v in vendor_data[:5]:
            score = v.get("VENDOR_RISK_SCORE", 0)
            icon = "🔴" if score >= 50 else "🟠" if score >= 25 else "🟡" if score >= 10 else "🟢"
            st.markdown(
                f"{icon} **{v.get('VENDOR_NAME', '')}** ({v.get('TRADE_CATEGORY', 'General')}) — "
                f"Grade: **{v.get('PERFORMANCE_GRADE', 'N/A')}** &nbsp;•&nbsp; "
                f"High-Risk {cfg['entity']['contract']}s: {v.get('HIGH_RISK_CONTRACTS', 0)} &nbsp;•&nbsp; "
                f"Safety Incidents: {v.get('SAFETY_INCIDENT_COUNT', 0)}"
            )
    else:
        st.info(f"No {cfg['entity']['vendor'].lower()} data available.")

    # ─── Team Credits Banner ────────────────────────────────────────────────
    st.divider()
    st.markdown(
        """
<div style="
  background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 50%, #0c4a6e 100%);
  border-radius: 16px;
  padding: 28px 40px;
  margin-top: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  flex-wrap: wrap;
  border: 1px solid #1e3a5f;
  box-shadow: 0 4px 20px rgba(0,0,0,0.4);
">
  <!-- Snowflake badge -->
  <div style="display:flex;align-items:center;gap:16px">
    <div style="
      background: radial-gradient(circle, #38bdf8, #0284c7);
      width: 52px; height: 52px; border-radius: 14px;
      display: flex; align-items: center; justify-content: center;
      font-size: 1.8rem; box-shadow: 0 0 20px rgba(56,189,248,0.4);
      flex-shrink:0;
    ">❄️</div>
    <div>
      <div style="font-size:.65rem;font-weight:700;color:#38bdf8;letter-spacing:.12em;
                  text-transform:uppercase;margin-bottom:3px">Powered by</div>
      <div style="font-size:1.1rem;font-weight:700;color:#e2e8f0;line-height:1.2">
        Snowflake Cortex AI</div>
      <div style="font-size:.72rem;color:#64748b;margin-top:2px">
        Enterprise Risk Intelligence Platform</div>
    </div>
  </div>

  <!-- Divider -->
  <div style="width:1px;height:52px;background:#334155;flex-shrink:0"></div>

  <!-- Team -->
  <div style="display:flex;align-items:center;gap:14px">
    <div style="
      background: linear-gradient(135deg, #7c3aed, #a855f7);
      width: 48px; height: 48px; border-radius: 14px;
      display: flex; align-items: center; justify-content: center;
      font-size: 1.6rem; box-shadow: 0 0 16px rgba(168,85,247,0.4);
      flex-shrink:0;
    ">⚗️</div>
    <div>
      <div style="font-size:.65rem;font-weight:700;color:#a855f7;letter-spacing:.12em;
                  text-transform:uppercase;margin-bottom:3px">Built with ❤️ by</div>
      <div style="font-size:1.1rem;font-weight:700;color:#e2e8f0;line-height:1.2">
        Team Data Alchemists</div>
      <div style="font-size:.75rem;color:#94a3b8;margin-top:4px;line-height:1.6">
        Chirag Lalwani &nbsp;·&nbsp; Pratik Kanade &nbsp;·&nbsp; Abhishek Bhardwaj
      </div>
    </div>
  </div>

  <!-- Right chip -->
  <div style="
    background: rgba(56,189,248,0.08);
    border: 1px solid rgba(56,189,248,0.2);
    border-radius: 10px;
    padding: 10px 18px;
    text-align: center;
    flex-shrink:0;
  ">
    <div style="font-size:.65rem;color:#38bdf8;font-weight:600;
                text-transform:uppercase;letter-spacing:.08em">Hackathon</div>
    <div style="font-size:1.4rem;margin:2px 0">🏆</div>
    <div style="font-size:.65rem;color:#64748b">Data Intelligence</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
