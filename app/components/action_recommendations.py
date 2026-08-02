# Risk Command Center Streamlit component (action_recommendations tab) with enhanced UI.
# Co-authored with CoCo
"""
Tab 6: Recommended Actions & Tracker.
Color-coded risk cards, status pills, AI confidence bars, and action buttons.
"""

import streamlit as st
import pandas as pd
from app.utils.snowflake_client import SnowflakeClient


def _status_to_db(status: str) -> str:
    return {"PENDING": "Open", "IN_PROGRESS": "In_Progress", "COMPLETED": "Closed"}.get(status, "Open")


def _priority_badge(priority: str) -> str:
    colors = {"URGENT": "#DC2626", "HIGH": "#EA580C", "MEDIUM": "#D97706", "LOW": "#16A34A"}
    color = colors.get(priority, "#64748B")
    return f'<span style="background:{color};color:#fff;padding:2px 10px;border-radius:12px;font-size:0.75rem;font-weight:700">{priority}</span>'


def _status_badge(status: str) -> str:
    cfg = {
        "OPEN":        ("#1D4ED8", "⏳ PENDING"),
        "PENDING":     ("#1D4ED8", "⏳ PENDING"),
        "IN_PROGRESS": ("#7C3AED", "🔄 IN PROGRESS"),
        "CLOSED":      ("#15803D", "✅ COMPLETE"),
        "COMPLETED":   ("#15803D", "✅ COMPLETE"),
        "DISMISSED":   ("#6B7280", "❌ DISMISSED"),
    }
    color, label = cfg.get(status.upper(), ("#6B7280", f"⚪ {status}"))
    return f'<span style="background:{color};color:#fff;padding:2px 10px;border-radius:12px;font-size:0.75rem;font-weight:600">{label}</span>'


def render(client: SnowflakeClient):
    """Render the Recommended Actions & Tracker tab."""
    st.header("✅ Recommended Actions & Tracker")
    st.caption("AI-generated next steps, task assignments, and approval workflows")

    # ─── KPIs ────────────────────────────────────────────────────────────────
    summary = client.query("""
        SELECT
            COUNT(*)                                                                        AS total_actions,
            COUNT(CASE WHEN UPPER(COALESCE(re.STATUS,'Open')) IN ('OPEN','PENDING') THEN 1 END) AS pending,
            COUNT(CASE WHEN UPPER(re.STATUS) = 'IN_PROGRESS' THEN 1 END)                   AS in_progress,
            COUNT(CASE WHEN UPPER(re.STATUS) IN ('CLOSED','COMPLETED') THEN 1 END)          AS completed,
            COUNT(CASE WHEN m.SEVERITY IN ('High','Critical') THEN 1 END)                   AS urgent_pending,
            0                                                                               AS overdue
        FROM RISK_COMMAND_CENTER.GOLD.UNIFIED_RISK_MATRIX m
        LEFT JOIN RISK_COMMAND_CENTER.SILVER.RISK_EVENTS re ON m.RISK_ID = re.RISK_ID
    """)

    if summary:
        s = summary[0]
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("Total Actions",  s.get("TOTAL_ACTIONS", 0))
        c2.metric("Pending",        s.get("PENDING", 0))
        c3.metric("In Progress",    s.get("IN_PROGRESS", 0))
        c4.metric("Completed",      s.get("COMPLETED", 0))
        c5.metric("🚨 Urgent",      s.get("URGENT_PENDING", 0))
        c6.metric("⏰ Overdue",     s.get("OVERDUE", 0))

    st.divider()

    # ─── Filters ──────────────────────────────────────────────────────────────
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        status_filter = st.selectbox("Status", ["ALL", "PENDING", "IN_PROGRESS", "COMPLETED", "DISMISSED"])
    with fc2:
        priority_filter = st.selectbox("Priority", ["ALL", "URGENT", "HIGH", "MEDIUM", "LOW"])
    with fc3:
        projects = client.get_projects()
        proj_opts = {"All Projects": None}
        proj_opts.update({p["PROJECT_NAME"]: p["PROJECT_ID"] for p in projects})
        selected_project_id = proj_opts[st.selectbox("Project", list(proj_opts.keys()))]

    actions = client.get_action_tracker(
        status=status_filter, priority=priority_filter, project_id=selected_project_id
    )

    if not actions:
        st.info("No recommended actions match the current filters.")
    else:
        st.subheader(f"📋 Actions ({len(actions)} results)")
        for action in actions:
            priority = (action.get("PRIORITY") or "LOW").upper()
            raw_status = (action.get("STATUS") or "OPEN").upper()
            display_status = "PENDING" if raw_status in ("OPEN",) else raw_status
            action_id = action.get("ACTION_ID", "")
            risk_id   = action.get("RISK_ID", action_id)

            # Card border color by priority
            border = {"URGENT": "#DC2626", "HIGH": "#EA580C", "MEDIUM": "#D97706", "LOW": "#16A34A"}.get(priority, "#334155")

            st.markdown(
                f'<div style="border-left:4px solid {border};padding:12px 16px;'
                f'background:#1E293B;border-radius:8px;margin-bottom:4px">',
                unsafe_allow_html=True
            )

            # Title row
            title_left, title_right = st.columns([5, 2])
            with title_left:
                st.markdown(
                    _priority_badge(priority) + "&nbsp;&nbsp;" + _status_badge(display_status),
                    unsafe_allow_html=True
                )
                st.markdown(f"**{action.get('RECOMMENDED_ACTION', 'N/A')}**")
            with title_right:
                st.caption(f"🏗️ {action.get('PROJECT_NAME', 'N/A')}")
                st.caption(f"🗂️ {action.get('BUSINESS_OWNER', '')}  📅 {action.get('DUE_DATE', '')}")

            # Confidence + reasoning
            confidence = float(action.get("AI_CONFIDENCE") or 0)
            reasoning  = action.get("REASONING") or ""
            conf_col, reason_col = st.columns([1, 4])
            conf_col.markdown(
                f'<div style="text-align:center">'
                f'<div style="font-size:1.4rem;font-weight:700;color:#60A5FA">{confidence*100:.0f}%</div>'
                f'<div style="font-size:0.7rem;color:#94A3B8">AI Confidence</div></div>',
                unsafe_allow_html=True
            )
            if reasoning:
                reason_col.markdown(f"*{reasoning}*")

            # Action buttons
            if display_status in ("PENDING", "IN_PROGRESS"):
                b1, b2, _ = st.columns([1, 1, 5])
                if b1.button("▶️ Start", key=f"start_{action_id}", use_container_width=True):
                    client.execute(f"UPDATE RISK_COMMAND_CENTER.SILVER.RISK_EVENTS SET STATUS = 'In_Progress' WHERE RISK_ID = '{risk_id}'")
                    st.rerun()
                if b2.button("✅ Complete", key=f"done_{action_id}", use_container_width=True):
                    client.execute(f"UPDATE RISK_COMMAND_CENTER.SILVER.RISK_EVENTS SET STATUS = 'Closed' WHERE RISK_ID = '{risk_id}'")
                    st.rerun()

            st.markdown('</div><br>', unsafe_allow_html=True)

    # ─── Approval Queue ───────────────────────────────────────────────────────
    st.divider()
    st.subheader("⚖️ Executive Approval Queue")
    st.caption("High/Critical risks requiring executive sign-off")

    approvals = client.query("""
        SELECT m.RISK_ID, m.PROJECT_NAME, m.RISK_TITLE, m.SEVERITY,
            '$' || TO_VARCHAR(ROUND(m.TOTAL_FINANCIAL_EXPOSURE), '999,999,999') AS EXPOSURE,
            DATEADD('day', 5, CURRENT_DATE()) AS DUE_DATE,
            'AWAITING APPROVAL' AS STATUS
        FROM RISK_COMMAND_CENTER.GOLD.UNIFIED_RISK_MATRIX m
        WHERE m.SEVERITY IN ('High', 'Critical')
        ORDER BY m.TOTAL_FINANCIAL_EXPOSURE DESC NULLS LAST
    """)

    if approvals:
        st.dataframe(pd.DataFrame(approvals), use_container_width=True, hide_index=True)
    else:
        st.info("No items currently awaiting executive approval.")
