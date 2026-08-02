# Admin panel tab — live corpus/pipeline stats and real breakdown charts.
# Co-authored with CoCo
"""
Tab 10: Admin Panel — Configuration and live processing statistics.
All charts are built from real GOLD/SILVER/BRONZE tables (no mock data).
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from app.utils.snowflake_client import SnowflakeClient

DB = "RISK_COMMAND_CENTER"


def render(client: SnowflakeClient):
    st.header("⚙️ Admin & Configuration")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Domain Configuration")
        st.caption("Active analytical domain for this deployment")
        st.info("**Construction Lifecycle** — the medallion schema, risk "
                "categories, and entities below are configured for this domain.")

        with st.expander("View Active Config"):
            st.json({
                "domain": "Construction Lifecycle",
                "database": DB,
                "layers": ["BRONZE", "SILVER", "GOLD"],
                "entities_tracked": ["Project", "Vendor", "Contract", "Invoice", "Risk Event"],
                "gold_views": ["PROJECT_RISK_SUMMARY", "FINANCIAL_SUMMARY",
                               "UNIFIED_RISK_MATRIX", "VENDOR_SCORECARD", "SAFETY_DASHBOARD"],
            })

        st.divider()
        st.subheader("Pipeline Status")
        status = client.get_pipeline_status()
        if status:
            df_status = pd.DataFrame(status)
            display_cols = ["PROCEDURE_NAME", "STATUS", "RECORDS_PROCESSED"]
            available = [c for c in display_cols if c in df_status.columns]
            if available:
                df_status = df_status[available]
            df_status.columns = [c.replace("_", " ").title() for c in df_status.columns]
            # st.table renders the full table with no scrollbar (small row count)
            st.table(df_status)

    with col2:
        st.subheader("📊 Live Processing Statistics")
        stats = client.get_ai_usage_stats()

        if stats:
            s_col1, s_col2, s_col3, s_col4 = st.columns(4)
            s_col1.metric("Documents", stats.get('TOTAL_CALLS', 0))
            s_col2.metric("Chunks Parsed", stats.get('CACHE_HITS', 0))
            s_col3.metric("Risk Events", stats.get('DISTINCT_OPERATIONS', 0))
            s_col4.metric("Est. Tokens", f"{stats.get('TOTAL_INPUT_TOKENS', 0):,}")

        template = st.session_state.get("plotly_template", "plotly_dark")

        # Real chart 1: documents by file type
        doc_rows = client.query(
            f"SELECT COALESCE(FILE_TYPE, 'other') AS FILE_TYPE, COUNT(*) AS N "
            f"FROM {DB}.BRONZE.DOCUMENT_REGISTRY GROUP BY 1 ORDER BY N DESC"
        )
        if doc_rows:
            st.markdown("**Documents by Type** (live from BRONZE.DOCUMENT_REGISTRY)")
            ddf = pd.DataFrame(doc_rows)
            fig1 = px.bar(ddf, x="FILE_TYPE", y="N", template=template,
                          color="N", color_continuous_scale="Blues")
            fig1.update_layout(height=280, showlegend=False,
                               paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                               coloraxis_showscale=False, margin=dict(t=10, b=10))
            st.plotly_chart(fig1, use_container_width=True)

        # Real chart 2: risk events by category
        risk_rows = client.query(
            f"SELECT RISK_CATEGORY, COUNT(*) AS N, "
            f"SUM(TOTAL_FINANCIAL_EXPOSURE) AS EXPOSURE "
            f"FROM {DB}.GOLD.UNIFIED_RISK_MATRIX GROUP BY 1 ORDER BY N DESC"
        )
        if risk_rows:
            st.markdown("**Risk Events by Category** (live from GOLD.UNIFIED_RISK_MATRIX)")
            rdf = pd.DataFrame(risk_rows)
            fig2 = px.bar(rdf, x="RISK_CATEGORY", y="N", template=template,
                          color="EXPOSURE", color_continuous_scale="Reds")
            fig2.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)",
                               plot_bgcolor="rgba(0,0,0,0)", margin=dict(t=10, b=10))
            st.plotly_chart(fig2, use_container_width=True)
