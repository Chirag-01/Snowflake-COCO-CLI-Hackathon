# Ask CoCo — conversational risk assistant with dynamic charts, domain-config driven suggestions.
# Co-authored with CoCo
"""
Tab 8: Ask CoCo — AI-powered risk assistant with RAG over documents.

Features:
- Chat with structured data (Gold layer)
- Chat with documents (vector search over Silver chunks)
- Dynamic Plotly charts from AI responses
- Document source references with file names and page numbers
- Loading animation during AI processing
"""

import streamlit as st
import plotly.graph_objects as go
from app.utils.snowflake_client import SnowflakeClient
from app.config.domain_loader import get_cfg

# Suggestions are loaded at render time from active domain config
_DEFAULT_SUGGESTIONS = [
    "What is the biggest financial risk right now?",
    "Which projects are behind schedule?",
    "Show me risk exposure by project",
    "Compare vendor performance ranking",
    "Show breakdown of risks by category",
    "Chart project completion progress",
]


def _render_chart(chart_data: dict):
    """Render a Plotly chart from programmatically-built chart data."""
    if not chart_data:
        return
    try:
        chart_type = chart_data.get("type", "bar")
        title      = chart_data.get("title", "")
        x          = chart_data.get("x", [])
        y          = chart_data.get("y", [])
        y2         = chart_data.get("y2")        # optional second series
        labels     = chart_data.get("labels", x)
        tmpl       = st.session_state.get("plotly_template", "plotly_dark")

        fig = go.Figure()

        if chart_type == "pie":
            fig.add_trace(go.Pie(labels=labels, values=y, hole=0.4,
                                 marker_colors=["#DC2626","#F97316","#FBBF24","#22C55E","#3B82F6"]))
        elif chart_type == "line":
            fig.add_trace(go.Scatter(x=x, y=y, mode="lines+markers",
                                     line=dict(color="#3B82F6", width=2)))
        else:
            # Default: bar — supports optional second series
            fig.add_trace(go.Bar(x=x, y=y, name=title,
                                 marker_color="#3B82F6"))
            if y2:
                fig.add_trace(go.Bar(x=x, y=y2, name="Spent",
                                     marker_color="#F97316"))
            fig.update_layout(barmode="group" if y2 else "relative")

        fig.update_layout(
            title=title,
            template=tmpl,
            height=350,
            margin=dict(l=40, r=40, t=50, b=80),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            xaxis=dict(tickangle=-35),
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception:
        pass


def _render_sources(sources: list):
    """Render document source references in a user-friendly format."""
    if not sources:
        return
    # Deduplicate by file name
    seen = set()
    unique_sources = []
    for src in sources:
        key = src.get('file', '')
        if key not in seen:
            seen.add(key)
            unique_sources.append(src)
    
    with st.expander(f"📎 Sources ({len(unique_sources)} documents)", expanded=True):
        for i, src in enumerate(unique_sources):
            file_name = src.get('file', 'Unknown')
            page = src.get('page', '?')
            display_name = file_name.replace('_', ' ').replace('.pdf', '').replace('.PDF', '')
            st.write(f"📄 **{display_name}** — Page {page}")


def _answer(client: SnowflakeClient, prompt: str):
    """Append a user prompt and CoCo's reply to the transcript."""
    st.session_state.coco_messages.append({"role": "user", "content": prompt})

    # Call the enhanced ask_coco that returns dict
    result = client.ask_coco(prompt)

    if isinstance(result, dict):
        answer = result.get("answer", "")
        sources = result.get("sources", [])
        chart_data = result.get("chart_data")
    else:
        answer = result
        sources = []
        chart_data = None

    st.session_state.coco_messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources,
        "chart_data": chart_data,
    })


def render(client: SnowflakeClient):
    """Render the Ask CoCo chat tab."""
    cfg         = get_cfg()
    suggestions = cfg.get("coco", {}).get("suggestions", _DEFAULT_SUGGESTIONS)

    st.header("🤖 Ask CoCo — AI Risk Intelligence")
    st.caption(
        f"Ask about risks, finances, {cfg['entity']['vendors'].lower()}, schedule, safety "
        "— or chat with your uploaded documents. CoCo searches both structured data and document content."
    )

    if "coco_messages" not in st.session_state:
        st.session_state.coco_messages = [
            {"role": "assistant",
             "content": f"Hi! I'm **CoCo**, your AI risk assistant. I can answer questions from your "
                        f"structured {cfg['entity']['project'].lower()} data AND uploaded documents. Try asking me anything!",
             "sources": [], "chart_data": None}
        ]

    # Suggested questions (domain-specific)
    st.markdown("**💡 Quick questions:**")
    cols = st.columns(3)
    for i, q in enumerate(suggestions):
        if cols[i % 3].button(q, use_container_width=True, key=f"sugg_{i}"):
            _answer(client, q)
            st.rerun()

    # Controls row
    if st.button("🗑️ Clear Chat", key="coco_clear"):
        st.session_state.coco_messages = [
            {"role": "assistant",
             "content": "Chat cleared! Ask me a new question.",
             "sources": [], "chart_data": None}
        ]
        st.rerun()

    st.divider()

    # Chat transcript with enhanced rendering
    for msg in st.session_state.coco_messages:
        if msg["role"] == "assistant":
            st.markdown("🤖 **CoCo:**")
            # Clean up literal \n and render properly
            content = msg['content'].replace('\\n', '\n').replace('\n\n\n', '\n\n')
            # Wrap in a quote block for cleaner visual separation
            st.info(content)
            # Render chart if available
            if msg.get("chart_data"):
                _render_chart(msg["chart_data"])
            # Render sources if available
            if msg.get("sources"):
                _render_sources(msg["sources"])
        else:
            st.markdown(f"🧑 **You:** {msg['content']}")

    st.markdown("---")

    # Input form
    with st.form("coco_form", clear_on_submit=True):
        prompt = st.text_input(
            "Your question",
            placeholder="e.g. What is the contract value of Phoenix? / Summarize the uploaded PDF",
            label_visibility="collapsed"
        )
        submitted = st.form_submit_button("🚀 Ask CoCo", use_container_width=True)

    if submitted and prompt.strip():
        with st.spinner("🧠 Thinking..."):
            _answer(client, prompt.strip())
        st.rerun()
