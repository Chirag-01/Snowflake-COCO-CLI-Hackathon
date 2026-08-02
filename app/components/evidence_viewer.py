# Evidence viewer component — document evidence viewer with domain-aware filtering.
# Co-authored with CoCo
"""
Tab 4: Evidence Viewer — Document proof for every AI finding.
Uses evidence_links + semantic search for traceability.
"""

import streamlit as st
from app.utils.snowflake_client import SnowflakeClient


def render(client: SnowflakeClient):
    """Render the Evidence Viewer tab."""

    st.header("📄 Evidence Viewer")
    st.caption("Every risk finding is backed by document evidence — click to trace")

    # ─── Search Mode ──────────────────────────────────────────────────────
    search_mode = st.radio(
        "Search mode:",
        ["Browse by Reference", "Semantic Search"],
        horizontal=True,
    )

    if search_mode == "Semantic Search":
        query = st.text_input("🔍 Search documents:", placeholder="e.g., contract value mismatch PRJ-001")
        if query:
            with st.spinner("Searching..."):
                results = client.search_evidence_semantic(query, top_k=8)

            if results:
                st.success(f"Found {len(results)} relevant evidence chunks")
                for i, r in enumerate(results):
                    similarity = r.get("SIMILARITY", 0)
                    strength = "🟢 Strong" if similarity > 0.8 else "🟡 Moderate" if similarity > 0.6 else "🔴 Weak"

                    with st.expander(
                        f"{strength} | {r.get('FILE_NAME', 'Unknown')} ({r.get('DOCUMENT_TYPE', '')}) — "
                        f"Similarity: {similarity:.2%}",
                        expanded=(i < 3),
                    ):
                        st.markdown(
                            f'<div style="background-color: #1E293B; border-left: 4px solid #3B82F6; '
                            f'padding: 12px; border-radius: 4px; font-family: monospace; font-size: 0.85em; '
                            f'white-space: pre-wrap; color: #E2E8F0;">{r.get("CHUNK_TEXT", "")}</div>',
                            unsafe_allow_html=True,
                        )
                        st.caption(f"Document: {r.get('FILE_NAME', '')} | Type: {r.get('DOCUMENT_TYPE', '')} | Project: {r.get('PROJECT_ID', '')}")
            else:
                st.info("No matching evidence found. Try different search terms.")
        return

    # ─── Browse by Reference ──────────────────────────────────────────────
    st.divider()

    # Project filter
    projects = client.get_projects()
    project_options = {"All Projects": None}
    project_options.update({p["PROJECT_NAME"]: p["PROJECT_ID"] for p in projects})
    selected_project_name = st.selectbox("Filter by project:", list(project_options.keys()))
    selected_project = project_options[selected_project_name]

    # Get evidence links
    evidence = client.get_evidence(project_id=selected_project)

    if not evidence:
        st.info("Structured evidence links are not populated in this deployment. "
                "Browse the parsed document registry below, or use Semantic Search "
                "to trace findings back to source text.")
    else:
        # ─── Evidence by Reference Type ───────────────────────────────────────
        ref_types = sorted(set(e.get("LINKED_REF_TYPE", "Unknown") for e in evidence))

        for ref_type in ref_types:
            type_evidence = [e for e in evidence if e.get("LINKED_REF_TYPE") == ref_type]
            icon_map = {
                "Risk": "⚠️", "RFI": "❓", "ChangeOrder": "📝",
                "Invoice": "💳", "Task": "📋", "Safety": "🦺",
                "Environmental": "🌿", "Quality": "🔬",
            }
            icon = icon_map.get(ref_type, "📄")

            with st.expander(f"{icon} {ref_type} ({len(type_evidence)} evidence links)", expanded=(ref_type == "Risk")):
                for ev in type_evidence:
                    strength = ev.get("EVIDENCE_STRENGTH", "Unknown")
                    strength_icon = {"Strong": "🟢", "Moderate": "🟡", "Weak": "🔴"}.get(strength, "⚪")

                    with st.container():
                        col1, col2, col3 = st.columns([3, 1, 1])

                        col1.markdown(
                            f"**{ev.get('DOC_TITLE', ev.get('FILE_NAME', 'Unknown'))}**\n\n"
                            f"📎 `{ev.get('FILE_NAME', '')}` ({ev.get('FILE_TYPE', '')}) • {ev.get('DOCUMENT_TYPE', '')}"
                        )
                        col2.markdown(f"{strength_icon} **{strength}**\n\nPage/Section: {ev.get('PAGE_OR_SECTION', 'N/A')}")
                        col3.markdown(f"Ref: **{ev.get('LINKED_REF_ID', '')}**\n\n{ev.get('PROJECT_NAME', '')}")

                        if ev.get("RELEVANCE_NOTE"):
                            st.caption(f"💡 {ev['RELEVANCE_NOTE']}")

    # ─── Document Registry ────────────────────────────────────────────────
    st.divider()
    st.subheader("📁 Document Registry")
    st.caption("Showing documents for the active domain. Use the top filter to narrow by project.")

    # Reuse the project already selected above — no second filter widget needed
    # Simple, reliable query — no correlated subqueries
    if selected_project:
        docs = client.query(f"""
            SELECT DISTINCT d.DOCUMENT_ID, d.FILE_NAME, d.FILE_TYPE,
                   d.FILE_SIZE, d.STATUS, d.UPLOADED_AT,
                   COALESCE(d.DOMAIN, 'construction') AS DOMAIN
            FROM RISK_COMMAND_CENTER.BRONZE.DOCUMENT_REGISTRY d
            JOIN RISK_COMMAND_CENTER.SILVER.CHUNKS c ON c.DOCUMENT_ID = d.DOCUMENT_ID
            JOIN RISK_COMMAND_CENTER.SILVER.RISK_EVENTS re ON re.SOURCE_CHUNK_ID = c.CHUNK_ID
            WHERE re.PROJECT_ID = '{selected_project}'
            ORDER BY d.UPLOADED_AT DESC LIMIT 50
        """)
        # Fallback: match on file name pattern
        if not docs:
            proj_fragment = selected_project.replace("PRJ-", "")
            docs = client.query(f"""
                SELECT DOCUMENT_ID, FILE_NAME, FILE_TYPE, FILE_SIZE, STATUS, UPLOADED_AT,
                       COALESCE(DOMAIN, 'construction') AS DOMAIN
                FROM RISK_COMMAND_CENTER.BRONZE.DOCUMENT_REGISTRY
                WHERE UPPER(FILE_NAME) LIKE UPPER('%{proj_fragment}%')
                   OR UPPER(FILE_NAME) LIKE UPPER('%{selected_project_name[:12]}%')
                ORDER BY UPLOADED_AT DESC LIMIT 50
            """)
    else:
        docs = client.get_document_registry(limit=50)

    if docs:
        import pandas as pd
        df_docs = pd.DataFrame(docs)
        df_docs["File Size"] = df_docs.get("FILE_SIZE", pd.Series([0] * len(df_docs))).apply(
            lambda x: f"{(x or 0)/1024:.1f} KB"
        )
        df_docs["Status"] = df_docs.get("STATUS", pd.Series([""] * len(df_docs))).apply(
            lambda s: "✅ Parsed" if str(s).upper() in ("PARSED","PROCESSED","SUCCESS")
                      else "⏳ Pending" if str(s).upper() == "UPLOADED"
                      else f"❌ {s}"
        )
        display_cols = {
            "FILE_NAME": "Document",
            "FILE_TYPE": "Type",
            "File Size": "Size",
            "Status": "Status",
            "DOMAIN": "Domain",
            "UPLOADED_AT": "Uploaded",
        }
        available = [c for c in display_cols if c in df_docs.columns or c in ("File Size", "Status")]
        df_show = df_docs[[c for c in available if c in df_docs.columns]].rename(columns=display_cols)
        st.dataframe(df_show, use_container_width=True, hide_index=True)
    else:
        st.info("No documents found for this filter.")
