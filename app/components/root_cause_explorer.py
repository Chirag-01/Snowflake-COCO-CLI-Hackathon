# Risk Command Center Streamlit component (root_cause_explorer tab).
# Co-authored with CoCo
"""
Tab 3: Root Cause Explorer — interactive causal chain visualization.

Renders project → vendor → invoice → risk chains as an interactive Plotly
network graph (Plotly is available in Snowflake; streamlit-agraph is not).
"""

import streamlit as st
import plotly.graph_objects as go
from app.utils.snowflake_client import SnowflakeClient

TYPE_COLOR = {
    "project": "#3B82F6",
    "vendor": "#F97316",
    "invoice": "#EC4899",
    "risk": "#DC2626",
}


def _build_graph(chains):
    """Assemble node/edge lists (with simple layered positions) from chains."""
    nodes = {}   # id -> dict(label, type, x, y, hover)
    edges = []   # list of (src_id, dst_id)

    def add(node_id, label, ntype, x, y, hover=""):
        if node_id and node_id not in nodes:
            nodes[node_id] = dict(label=label, type=ntype, x=x, y=y, hover=hover or label)

    risk_rows = [c for c in chains if c.get("LINKED_RISK_ID")]
    n = max(len(risk_rows), 1)

    for i, chain in enumerate(chains):
        proj_id = chain.get("PROJECT_ID")
        add(proj_id, chain.get("PROJECT_NAME", "Project")[:28], "project", 0, 0,
            hover=chain.get("PROJECT_NAME", "Project"))

        vendor_id = chain.get("LINKED_VENDOR_ID")
        add(vendor_id, (chain.get("VENDOR_NAME") or "Vendor")[:24], "vendor", 1, 0.6,
            hover=chain.get("VENDOR_NAME", "Vendor"))

        inv_id = chain.get("LINKED_INVOICE_ID")
        inv_amt = chain.get("CURRENT_INVOICE_AMOUNT") or 0
        add(inv_id, f"${inv_amt:,.0f}", "invoice", 2, -0.6,
            hover=f"Invoice {inv_id}: ${inv_amt:,.0f}")

        # Risk nodes fan out on the right
        y = (i - (n - 1) / 2) * 1.2
        risk_id = chain.get("LINKED_RISK_ID")
        exposure = chain.get("TOTAL_FINANCIAL_EXPOSURE") or 0
        label = f"⚠️ ${exposure:,.0f}"
        add(risk_id, label, "risk", 3.2, y,
            hover=f"{chain.get('RISK_TITLE', 'Risk')} ({chain.get('RISK_SEVERITY', '')}) "
                  f"— ${exposure:,.0f}")

        # Chain edges (fall back to project when an intermediate is missing)
        chain_seq = [x for x in [proj_id, vendor_id, inv_id, risk_id] if x]
        for a, b in zip(chain_seq, chain_seq[1:]):
            edges.append((a, b))

    return nodes, edges


def _plot(nodes, edges):
    fig = go.Figure()

    # Edges
    for src, dst in edges:
        if src in nodes and dst in nodes:
            fig.add_trace(go.Scatter(
                x=[nodes[src]["x"], nodes[dst]["x"]],
                y=[nodes[src]["y"], nodes[dst]["y"]],
                mode="lines", line=dict(color="#94A3B8", width=1.5),
                hoverinfo="skip", showlegend=False,
            ))

    # Nodes grouped by type (so the legend is meaningful)
    for ntype, color in TYPE_COLOR.items():
        pts = [n for n in nodes.values() if n["type"] == ntype]
        if not pts:
            continue
        fig.add_trace(go.Scatter(
            x=[p["x"] for p in pts], y=[p["y"] for p in pts],
            mode="markers+text",
            marker=dict(size=26, color=color, line=dict(width=2, color="#FFFFFF")),
            text=[p["label"] for p in pts], textposition="middle right",
            textfont=dict(size=11),
            hovertext=[p["hover"] for p in pts], hoverinfo="text",
            name=ntype.title(),
        ))

    fig.update_layout(
        height=520,
        template=st.session_state.get("plotly_template", "plotly_dark"),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False,
                   range=[-0.5, 4.5]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    return fig


def render(client: SnowflakeClient):
    """Render the Root Cause Explorer tab."""
    st.header("🔍 Root Cause Explorer")
    st.caption("Trace the chain of causation from issue to financial impact")

    projects = client.get_projects()
    if not projects:
        st.info("No projects available.")
        return

    project_options = {p["PROJECT_NAME"]: p["PROJECT_ID"] for p in projects}
    selected_name = st.selectbox("Select a project to explore:", list(project_options.keys()))
    selected_project = project_options[selected_name]

    st.divider()

    chains = client.get_root_cause_graph(selected_project)
    if not chains:
        st.info("No root cause chains found for this project.")
        return

    # ─── Interactive Graph ────────────────────────────────────────────────
    st.subheader("🌳 Causal Chain Graph")
    nodes, edges = _build_graph(chains)
    if nodes:
        st.plotly_chart(_plot(nodes, edges), use_container_width=True)
    else:
        st.info("Not enough linked data to draw a graph.")

    st.divider()

    # ─── Chain Table View ─────────────────────────────────────────────────
    st.subheader("📋 Issue Chain Details")
    for chain in chains:
        with st.container():
            st.markdown(
                f"**🔗 {chain.get('ISSUE_CHAIN_ID', '')}** — Root Cause: "
                f"_{chain.get('ROOT_CAUSE', 'Unknown')}_"
            )
            trace_parts = []
            if chain.get("PROJECT_NAME"):
                trace_parts.append(f"🏗️ {chain['PROJECT_NAME']}")
            if chain.get("VENDOR_NAME"):
                trace_parts.append(f"👷 {chain['VENDOR_NAME']}")
            if chain.get("LINKED_INVOICE_ID"):
                trace_parts.append(f"💳 ${chain.get('CURRENT_INVOICE_AMOUNT', 0):,.0f}")
            if chain.get("RISK_TITLE"):
                trace_parts.append(
                    f"⚠️ {chain['RISK_TITLE']} "
                    f"({chain.get('RISK_SEVERITY', '')} — ${chain.get('TOTAL_FINANCIAL_EXPOSURE', 0):,.0f})"
                )
            st.markdown(" → ".join(trace_parts))
            if chain.get("EXPECTED_AI_ANSWER"):
                st.caption(f"💡 {chain['EXPECTED_AI_ANSWER']}")
