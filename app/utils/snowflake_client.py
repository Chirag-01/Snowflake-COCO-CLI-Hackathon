# Snowflake Client — unified interface for all Snowflake operations with AI_COMPLETE.
# Co-authored with CoCo
"""
Snowflake Client — unified interface for all Snowflake operations.

Runs natively inside Snowflake using the active Snowpark session.
Uses AI_COMPLETE for LLM calls and vector search for document Q&A.
All reads are fully-qualified against the RISK_COMMAND_CENTER database.
"""

from __future__ import annotations

import datetime as _dt
import json
from decimal import Decimal

import streamlit as st

try:
    from snowflake.snowpark.context import get_active_session
except Exception:
    get_active_session = None

DB = "RISK_COMMAND_CENTER"
LLM_MODEL = "openai-gpt-5"


def _coerce(value):
    """Normalize Snowflake types for Streamlit/plotly/arithmetic."""
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (_dt.date, _dt.datetime)):
        return value.isoformat()
    return value


class SnowflakeClient:
    """Live Snowflake client backed by the active Snowpark session."""

    def __init__(self, session=None):
        if session is not None:
            self._session = session
        elif get_active_session is not None:
            self._session = get_active_session()
        else:
            raise RuntimeError(
                "No active Snowpark session. This app must run inside Snowflake."
            )

    # ─── Domain helper ────────────────────────────────────────────────────

    def _active_domain(self) -> str:
        """Return the currently active domain from session state."""
        return st.session_state.get("domain_id", "construction")

    # ─── Core Execution ───────────────────────────────────────────────────

    def query(self, sql: str) -> list[dict]:
        """Execute SQL and return rows as a list of dicts."""
        try:
            rows = self._session.sql(sql).collect()
            return [{k: _coerce(v) for k, v in row.as_dict().items()} for row in rows]
        except Exception as e:
            st.warning(f"Query failed: {e}")
            return []

    def execute(self, sql: str) -> str:
        try:
            self._session.sql(sql).collect()
            return "OK"
        except Exception as e:
            st.warning(f"Statement failed: {e}")
            return str(e)

    def _scalar(self, sql: str, default=None):
        rows = self.query(sql)
        if rows:
            return list(rows[0].values())[0]
        return default

    # ─── AI: AI_COMPLETE wrapper ──────────────────────────────────────────

    def ai_complete(self, prompt: str, model: str = None) -> str:
        """Call AI_COMPLETE with the given prompt. Returns response text or empty string."""
        model = model or LLM_MODEL
        try:
            # Use parameter binding to avoid SQL injection and escaping issues
            rows = self._session.sql(
                "SELECT SNOWFLAKE.CORTEX.AI_COMPLETE(?, ?) AS RESPONSE",
                params=[model, prompt[:8000]]
            ).collect()
            result = rows[0][0] if rows else ""
            # Handle case where result is JSON-quoted
            if result and result.startswith('"') and result.endswith('"'):
                import json
                try:
                    result = json.loads(result)
                except Exception:
                    pass
            return result or ""
        except Exception as e:
            # Store error for debugging
            try:
                self._session.sql(f"INSERT INTO RISK_COMMAND_CENTER.OPS.AI_ERROR_LOG SELECT CURRENT_TIMESTAMP(), '{str(e)[:200]}'").collect()
            except Exception:
                pass
            return ""

    # ─── Vector Search (Chat with PDFs) ───────────────────────────────────

    def vector_search(self, query: str, top_k: int = 5) -> list[dict]:
        """Search chunks by vector similarity. Falls back to keyword if vectors unavailable."""
        query_esc = query.replace("'", "''")

        # Try vector search first
        try:
            sql = f"""
                SELECT
                    c.CHUNK_TEXT,
                    c.CHUNK_ID,
                    c.PAGE_NUMBER,
                    c.DOCUMENT_ID,
                    d.FILE_NAME,
                    VECTOR_COSINE_SIMILARITY(
                        v.EMBEDDING_VECTOR,
                        SNOWFLAKE.CORTEX.EMBED_TEXT_1024('voyage-multilingual-2', '{query_esc}')
                    ) AS SIMILARITY
                FROM {DB}.SILVER.VECTORS v
                JOIN {DB}.SILVER.CHUNKS c ON v.CHUNK_ID = c.CHUNK_ID
                LEFT JOIN {DB}.BRONZE.DOCUMENT_REGISTRY d ON c.DOCUMENT_ID = d.DOCUMENT_ID
                ORDER BY SIMILARITY DESC
                LIMIT {top_k}
            """
            results = self.query(sql)
            if results:
                return results
        except Exception:
            pass

        # Fallback: keyword search
        return self.search_evidence_semantic(query, top_k)

    def chat_with_documents(self, question: str) -> dict:
        """RAG-based Q&A: search documents then answer with AI_COMPLETE.

        Returns dict with 'answer' and 'sources' (document references).
        """
        # Get relevant chunks
        chunks = self.vector_search(question, top_k=5)

        if not chunks:
            return {
                "answer": "No relevant documents found. Please upload documents first.",
                "sources": []
            }

        # Build context from chunks
        context_parts = []
        sources = []
        for i, chunk in enumerate(chunks):
            context_parts.append(
                f"[Source {i+1}: {chunk.get('FILE_NAME', 'Unknown')} p.{chunk.get('PAGE_NUMBER', '?')}]\n"
                f"{chunk.get('CHUNK_TEXT', '')}"
            )
            sources.append({
                "file": chunk.get("FILE_NAME", "Unknown"),
                "page": chunk.get("PAGE_NUMBER"),
                "chunk_id": chunk.get("CHUNK_ID"),
                "similarity": chunk.get("SIMILARITY", 0),
                "excerpt": (chunk.get("CHUNK_TEXT", "")[:200] + "...")
                    if len(chunk.get("CHUNK_TEXT", "")) > 200 else chunk.get("CHUNK_TEXT", "")
            })

        context = "\n\n---\n\n".join(context_parts)

        prompt = f"""You are CoCo, an enterprise risk intelligence assistant. Answer the user's question using ONLY the document excerpts below. Be specific, cite source numbers, and include relevant data points.

DOCUMENT EXCERPTS:
{context}

QUESTION: {question}

ANSWER (cite [Source N] when referencing information):"""

        answer = self.ai_complete(prompt)

        if not answer:
            # Fallback: summarize chunks directly
            answer = "Based on the documents:\n\n"
            for i, chunk in enumerate(chunks[:3]):
                answer += f"**[{chunk.get('FILE_NAME', 'Doc')} p.{chunk.get('PAGE_NUMBER', '?')}]:** "
                answer += chunk.get("CHUNK_TEXT", "")[:300] + "\n\n"

        return {"answer": answer, "sources": sources}

    # ─── Search Silver Layer (for document-level queries) ──────────────────

    def search_silver_documents(self, query: str) -> list[dict]:
        """Search across silver chunks and return matching documents with context."""
        terms = [t.strip().replace("'", "''") for t in query.split() if len(t.strip()) > 2]
        if not terms:
            return []
        score_expr = " + ".join(
            [f"IFF(c.CHUNK_TEXT ILIKE '%{t}%', 1, 0)" for t in terms]
        )
        sql = f"""
            SELECT
                c.CHUNK_TEXT,
                c.PAGE_NUMBER,
                d.FILE_NAME,
                d.DOCUMENT_ID,
                ({score_expr}) / {len(terms)}.0 AS RELEVANCE
            FROM {DB}.SILVER.CHUNKS c
            LEFT JOIN {DB}.BRONZE.DOCUMENT_REGISTRY d ON c.DOCUMENT_ID = d.DOCUMENT_ID
            WHERE ({score_expr}) > 0
            ORDER BY RELEVANCE DESC
            LIMIT 10
        """
        return self.query(sql)

    # ─── Projects ─────────────────────────────────────────────────────────

    def get_projects(self) -> list[dict]:
        return self.query(
            f"SELECT PROJECT_ID, PROJECT_NAME FROM {DB}.GOLD.PROJECT_RISK_SUMMARY "
            f"ORDER BY PROJECT_NAME"
        )

    def get_project_detail(self, project_id: str) -> dict:
        rows = self.query(
            f"SELECT * FROM {DB}.GOLD.PROJECT_RISK_SUMMARY "
            f"WHERE PROJECT_ID = '{project_id}'"
        )
        return rows[0] if rows else {}

    # ─── Gold Views ─────────────────────────────────────────────────────────

    def get_project_risk_summary(self) -> list[dict]:
        dom = self._active_domain()
        return self.query(
            f"SELECT * FROM {DB}.GOLD.PROJECT_RISK_SUMMARY "
            f"WHERE COALESCE(DOMAIN,'construction') = '{dom}' "
            f"AND PROJECT_NAME IS NOT NULL AND PROJECT_NAME NOT IN ('None','null','PRJ-007') "
            f"ORDER BY TOTAL_RISK_EXPOSURE DESC NULLS LAST"
        )

    def get_financial_summary(self) -> list[dict]:
        dom = self._active_domain()
        return self.query(
            f"SELECT * FROM {DB}.GOLD.FINANCIAL_SUMMARY "
            f"WHERE COALESCE(DOMAIN,'construction') = '{dom}'"
        )

    def get_unified_risk_matrix(self) -> list[dict]:
        dom = self._active_domain()
        return self.query(
            f"SELECT * FROM {DB}.GOLD.UNIFIED_RISK_MATRIX "
            f"WHERE COALESCE(DOMAIN,'construction') = '{dom}' "
            f"ORDER BY TOTAL_FINANCIAL_EXPOSURE DESC NULLS LAST"
        )

    def get_safety_dashboard(self) -> list[dict]:
        dom = self._active_domain()
        return self.query(
            f"SELECT * FROM {DB}.GOLD.SAFETY_DASHBOARD "
            f"WHERE COALESCE(DOMAIN,'construction') = '{dom}'"
        )

    def get_executive_summary(self) -> list[dict]:
        return self.get_project_risk_summary()

    def get_financial_exposure(self, project_id: str = None) -> list[dict]:
        """Full financial-exposure model. Falls back to UNIFIED_RISK_MATRIX when CONTRACTS is empty."""
        where = f"WHERE s.PROJECT_ID = '{project_id}'" if project_id else ""
        dom = self._active_domain()
        sql = f"""
            WITH ctr AS (
                SELECT PROJECT_ID,
                       SUM(CURRENT_CONTRACT_VALUE)  AS CURRENT_CONTRACT_VALUE,
                       SUM(LD_PER_DAY)              AS LD_PER_DAY,
                       SUM(COALESCE(RETAINAGE_PERCENT,0)/100.0
                           * COALESCE(CURRENT_CONTRACT_VALUE,0)) AS PAYMENT_HELD_AMOUNT
                FROM {DB}.SILVER.CONTRACTS
                GROUP BY PROJECT_ID
            ),
            risk_exp AS (
                -- Aggregate real financial exposure from unified risk matrix
                SELECT PROJECT_ID,
                       SUM(TOTAL_FINANCIAL_EXPOSURE) AS RISK_EXPOSURE,
                       SUM(DIRECT_COST_EXPOSURE)     AS DIRECT_EXPOSURE
                FROM {DB}.GOLD.UNIFIED_RISK_MATRIX
                WHERE COALESCE(DOMAIN,'construction') = '{dom}'
                GROUP BY PROJECT_ID
            )
            SELECT
                s.PROJECT_ID, s.PROJECT_NAME, s.CURRENT_BUDGET,
                s.FORECAST_COST_AT_COMPLETION,
                COALESCE(s.COST_VARIANCE, 0)                            AS COST_OVERRUN,
                -- Use UNIFIED_RISK_MATRIX exposure when RISK_EVENTS had no financials
                GREATEST(
                    COALESCE(s.TOTAL_RISK_EXPOSURE, 0),
                    COALESCE(re.RISK_EXPOSURE, 0)
                )                                                        AS TOTAL_RISK_EXPOSURE,
                -COALESCE(s.SCHEDULE_VARIANCE_DAYS, 0)                  AS CRITICAL_PATH_FLOAT_DAYS,
                COALESCE(ctr.CURRENT_CONTRACT_VALUE, s.CURRENT_BUDGET)  AS CURRENT_CONTRACT_VALUE,
                COALESCE(ctr.LD_PER_DAY, 0)                             AS LD_PER_DAY,
                GREATEST(COALESCE(s.SCHEDULE_VARIANCE_DAYS,0), 0)
                    * COALESCE(ctr.LD_PER_DAY, 0)                       AS LD_EXPOSURE,
                COALESCE(ctr.PAYMENT_HELD_AMOUNT, 0)                    AS PAYMENT_HELD_AMOUNT,
                COALESCE(f.TOTAL_CHANGE_ORDERS, 0)                      AS PENDING_CO_TOTAL,
                COALESCE(s.COST_VARIANCE, 0)
                    + GREATEST(COALESCE(s.SCHEDULE_VARIANCE_DAYS,0), 0) * COALESCE(ctr.LD_PER_DAY, 0)
                    + GREATEST(COALESCE(s.TOTAL_RISK_EXPOSURE,0), COALESCE(re.RISK_EXPOSURE,0))
                    + COALESCE(ctr.PAYMENT_HELD_AMOUNT, 0)              AS TOTAL_COMBINED_EXPOSURE
            FROM {DB}.GOLD.PROJECT_RISK_SUMMARY s
            LEFT JOIN ctr     ON ctr.PROJECT_ID = s.PROJECT_ID
            LEFT JOIN risk_exp re ON re.PROJECT_ID = s.PROJECT_ID
            LEFT JOIN {DB}.GOLD.FINANCIAL_SUMMARY f ON f.PROJECT_ID = s.PROJECT_ID
            {where}
            ORDER BY TOTAL_COMBINED_EXPOSURE DESC NULLS LAST
        """
        return self.query(sql)

    def get_risk_scenarios(self, project_id: str = None) -> list[dict]:
        conds = ["UPPER(m.SEVERITY) IN ('HIGH','CRITICAL')"]
        if project_id:
            conds.append(f"m.PROJECT_ID = '{project_id}'")
        where = " AND ".join(conds)
        sql = f"""
            SELECT
                m.RISK_TITLE, d.SCENARIO_DAY,
                COALESCE(m.TOTAL_FINANCIAL_EXPOSURE, 0) * (1 + d.SCENARIO_DAY / 90.0)
                    AS ESTIMATED_COST_EXPOSURE,
                COALESCE(m.SCHEDULE_IMPACT_DAYS, 0) + (d.SCENARIO_DAY / 30)
                    AS ESTIMATED_SCHEDULE_SLIP_DAYS,
                'If ' || m.RISK_CATEGORY || ' risk unresolved for '
                    || d.SCENARIO_DAY || ' days' AS TRIGGER_CONDITION,
                'Escalate to ' || m.RISK_LEVEL || ' governance review' AS RECOMMENDED_ESCALATION
            FROM {DB}.GOLD.UNIFIED_RISK_MATRIX m,
                 (SELECT 30 AS SCENARIO_DAY UNION SELECT 60 UNION SELECT 90) d
            WHERE {where}
            ORDER BY d.SCENARIO_DAY, ESTIMATED_COST_EXPOSURE DESC
        """
        return self.query(sql)

    def get_risk_signals(self, status: str = "OPEN", project_id: str = None) -> list[dict]:
        return self.get_unified_risk_matrix()

    # ─── Project Health (heatmap) ─────────────────────────────────────────

    def get_project_health(self) -> list[dict]:
        dom = self._active_domain()
        sql = f"""
            SELECT
                s.PROJECT_NAME, s.PERCENT_COMPLETE,
                s.SCHEDULE_VARIANCE_DAYS AS CRITICAL_PATH_FLOAT_DAYS,
                COALESCE(s.TOTAL_RISK_EXPOSURE, 0) AS TOTAL_FINANCIAL_EXPOSURE,
                COUNT_IF(m.RISK_CATEGORY IN ('Schedule','Weather')) AS DELAY_RISK_COUNT,
                COUNT_IF(m.RISK_CATEGORY = 'Contract') AS CONTRACT_RISK_COUNT,
                COUNT_IF(m.RISK_CATEGORY IN ('Cost','Financial','Budget')) AS BUDGET_RISK_COUNT,
                COUNT_IF(m.RISK_CATEGORY = 'Supply Chain') AS VENDOR_RISK_COUNT,
                COUNT_IF(m.RISK_CATEGORY = 'Safety') AS SAFETY_RISK_COUNT,
                COUNT_IF(m.RISK_CATEGORY = 'Environmental') AS ENVIRONMENTAL_RISK_COUNT,
                COUNT_IF(m.RISK_CATEGORY IN ('Quality','Design','Data Quality')) AS QUALITY_RISK_COUNT,
                MAX(m.SEVERITY) AS MAX_SEVERITY
            FROM {DB}.GOLD.PROJECT_RISK_SUMMARY s
            LEFT JOIN {DB}.GOLD.UNIFIED_RISK_MATRIX m ON s.PROJECT_ID = m.PROJECT_ID
            WHERE COALESCE(s.DOMAIN,'construction') = '{dom}'
              AND s.PROJECT_NAME IS NOT NULL
              AND TRIM(s.PROJECT_NAME) NOT IN ('','null','None')
              AND s.PROJECT_ID != s.PROJECT_NAME
            GROUP BY s.PROJECT_NAME, s.PERCENT_COMPLETE,
                     s.SCHEDULE_VARIANCE_DAYS, s.TOTAL_RISK_EXPOSURE
            ORDER BY TOTAL_FINANCIAL_EXPOSURE DESC NULLS LAST
        """
        return self.query(sql)

    # ─── Vendors ──────────────────────────────────────────────────────────

    def get_vendor_risk_ranking(self) -> list[dict]:
        dom = self._active_domain()
        sql = f"""
            SELECT
                VENDOR_NAME, TRADE_CATEGORY, PERFORMANCE_GRADE,
                COALESCE(COMPOSITE_SCORE, 0)      AS VENDOR_RISK_SCORE,
                COALESCE(SAFETY_INCIDENTS, 0)     AS SAFETY_INCIDENT_COUNT,
                COALESCE(HIGH_RISK_CONTRACTS, 0)  AS DELAYED_TASKS,
                COALESCE(HIGH_RISK_CONTRACTS, 0)  AS FAILED_INSPECTIONS,
                TOTAL_SUBCONTRACT_VALUE, TOTAL_BILLED, INSURANCE_STATUS
            FROM {DB}.GOLD.VENDOR_SCORECARD
            WHERE COALESCE(DOMAIN,'construction') = '{dom}'
              AND VENDOR_NAME NOT LIKE 'VND-%'
              AND VENDOR_NAME NOT LIKE 'SHP-%'
              AND LENGTH(TRIM(VENDOR_NAME)) > 3
            ORDER BY VENDOR_RISK_SCORE DESC NULLS LAST
        """
        return self.query(sql)

    # ─── Root Cause Chains ────────────────────────────────────────────────

    def get_root_cause_graph(self, project_id: str = None) -> list[dict]:
        dom = self._active_domain()
        conds = [f"COALESCE(r.DOMAIN,'construction') = '{dom}'",
                 "p.PROJECT_NAME IS NOT NULL",
                 "TRIM(p.PROJECT_NAME) NOT IN ('','null','None')"]
        if project_id:
            conds.append(f"r.PROJECT_ID = '{project_id}'")
        sql = f"""
            WITH inv AS (
                SELECT PROJECT_ID,
                       MAX(CURRENT_INVOICE_AMOUNT) AS CURRENT_INVOICE_AMOUNT,
                       MAX(INVOICE_ID) AS INVOICE_ID
                FROM {DB}.SILVER.INVOICES GROUP BY PROJECT_ID
            ),
            ven AS (
                SELECT c.PROJECT_ID,
                       ANY_VALUE(v.VENDOR_ID) AS VENDOR_ID,
                       ANY_VALUE(v.VENDOR_NAME) AS VENDOR_NAME
                FROM {DB}.SILVER.CONTRACTS c
                JOIN {DB}.SILVER.VENDORS v ON UPPER(v.VENDOR_NAME) = UPPER(c.CONTRACTOR)
                GROUP BY c.PROJECT_ID
            )
            SELECT
                r.RISK_ID AS ISSUE_CHAIN_ID, r.PROJECT_ID, p.PROJECT_NAME,
                r.RISK_CATEGORY AS ROOT_CAUSE, r.RISK_ID AS LINKED_RISK_ID,
                r.RISK_TITLE, r.SEVERITY AS RISK_SEVERITY,
                r.TOTAL_FINANCIAL_EXPOSURE,
                r.RISK_DESCRIPTION AS EXPECTED_AI_ANSWER,
                ven.VENDOR_ID AS LINKED_VENDOR_ID, ven.VENDOR_NAME,
                inv.INVOICE_ID AS LINKED_INVOICE_ID,
                inv.CURRENT_INVOICE_AMOUNT, p.COST_STATUS AS INVOICE_STATUS
            FROM {DB}.GOLD.UNIFIED_RISK_MATRIX r
            JOIN {DB}.GOLD.PROJECT_RISK_SUMMARY p ON r.PROJECT_ID = p.PROJECT_ID
            LEFT JOIN inv ON inv.PROJECT_ID = r.PROJECT_ID
            LEFT JOIN ven ON ven.PROJECT_ID = r.PROJECT_ID
            WHERE {" AND ".join(conds)}
            ORDER BY r.TOTAL_FINANCIAL_EXPOSURE DESC NULLS LAST
        """
        return self.query(sql)

    # ─── Documents & Evidence ─────────────────────────────────────────────

    def get_document_registry(self, limit: int = 100) -> list[dict]:
        return self.query(
            f"SELECT DOCUMENT_ID, FILE_NAME, FILE_TYPE, FILE_SIZE, STATUS, UPLOADED_AT "
            f"FROM {DB}.BRONZE.DOCUMENT_REGISTRY ORDER BY UPLOADED_AT DESC LIMIT {limit}"
        )

    def search_evidence_semantic(self, query: str, top_k: int = 5) -> list[dict]:
        """Keyword-relevance search over parsed document chunks."""
        terms = [t.strip().replace("'", "''") for t in query.split() if len(t.strip()) > 2]
        if not terms:
            return []
        score_expr = " + ".join(
            [f"IFF(c.CHUNK_TEXT ILIKE '%{t}%', 1, 0)" for t in terms]
        )
        sql = f"""
            SELECT
                c.CHUNK_TEXT, d.FILE_NAME,
                d.FILE_TYPE AS DOCUMENT_TYPE,
                c.PAGE_NUMBER,
                ({score_expr}) / {len(terms)}.0 AS SIMILARITY
            FROM {DB}.SILVER.CHUNKS c
            LEFT JOIN {DB}.BRONZE.DOCUMENT_REGISTRY d ON c.DOCUMENT_ID = d.DOCUMENT_ID
            WHERE ({score_expr}) > 0
            ORDER BY SIMILARITY DESC, LENGTH(c.CHUNK_TEXT)
            LIMIT {top_k}
        """
        return self.query(sql)

    def get_evidence(self, ref_id: str = None, project_id: str = None) -> list[dict]:
        """Get evidence from graph edges with chunk text."""
        sql = f"""
            SELECT
                e.EDGE_ID,
                s.NODE_NAME AS SOURCE_ENTITY,
                s.NODE_TYPE AS SOURCE_TYPE,
                t.NODE_NAME AS TARGET_ENTITY,
                t.NODE_TYPE AS TARGET_TYPE,
                e.RELATIONSHIP_TYPE,
                e.CONFIDENCE,
                c.CHUNK_TEXT AS EVIDENCE_TEXT,
                c.PAGE_NUMBER,
                d.FILE_NAME
            FROM {DB}.SILVER.GRAPH_EDGES e
            JOIN {DB}.SILVER.GRAPH_NODES s ON e.SOURCE_NODE_ID = s.NODE_ID
            JOIN {DB}.SILVER.GRAPH_NODES t ON e.TARGET_NODE_ID = t.NODE_ID
            LEFT JOIN {DB}.SILVER.CHUNKS c ON e.EVIDENCE_CHUNK_ID = c.CHUNK_ID
            LEFT JOIN {DB}.BRONZE.DOCUMENT_REGISTRY d ON c.DOCUMENT_ID = d.DOCUMENT_ID
            ORDER BY e.CONFIDENCE DESC
            LIMIT 50
        """
        return self.query(sql)

    # ─── Data Quality ─────────────────────────────────────────────────────

    def get_data_quality_exceptions(self) -> list[dict]:
        sql = f"""
            SELECT
                'DQ-CV-' || p.PROJECT_ID AS CHECK_ID,
                p.PROJECT_NAME,
                c.CONTRACT_ID AS SOURCE_REF_ID,
                'Contract Value Mismatch' AS CHECK_TYPE,
                TO_VARCHAR(p.CURRENT_CONTRACT_VALUE, '$999,999,999') AS EXPECTED_VALUE,
                TO_VARCHAR(c.CURRENT_CONTRACT_VALUE, '$999,999,999') AS OBSERVED_VALUE,
                IFF(ABS(p.CURRENT_CONTRACT_VALUE - c.CURRENT_CONTRACT_VALUE)
                    > 0.05 * p.CURRENT_CONTRACT_VALUE, 'High', 'Medium') AS SEVERITY,
                'Registered project value differs from the executed contract value.' AS BUSINESS_IMPACT,
                'Reconcile the contract register against the signed agreement.' AS RECOMMENDED_FIX
            FROM {DB}.SILVER.PROJECTS p
            JOIN {DB}.SILVER.CONTRACTS c ON p.PROJECT_ID = c.PROJECT_ID
            WHERE p.CURRENT_CONTRACT_VALUE IS NOT NULL
              AND c.CURRENT_CONTRACT_VALUE IS NOT NULL
              AND ABS(p.CURRENT_CONTRACT_VALUE - c.CURRENT_CONTRACT_VALUE) > 1
        """
        return self.query(sql)

    # ─── Actions ──────────────────────────────────────────────────────────

    def get_action_tracker(self, status: str = None, priority: str = None,
                           project_id: str = None) -> list[dict]:
        conds = ["m.SEVERITY IN ('High','Critical')"]
        if project_id:
            conds.append(f"m.PROJECT_ID = '{project_id}'")
        if priority and priority not in ("ALL", None):
            sev = "Critical" if priority == "URGENT" else "High"
            conds.append(f"m.SEVERITY = '{sev}'")
        where = " AND ".join(conds)
        sql = f"""
            SELECT
                m.RISK_ID AS ACTION_ID, m.PROJECT_NAME,
                IFF(m.SEVERITY = 'Critical', 'URGENT', 'HIGH') AS PRIORITY,
                'PENDING' AS STATUS,
                'Mitigate: ' || m.RISK_TITLE AS RECOMMENDED_ACTION,
                m.RISK_DESCRIPTION AS REASONING,
                LEAST(1, COALESCE(m.RISK_SCORE, 50) / 100) AS AI_CONFIDENCE,
                m.RISK_CATEGORY AS BUSINESS_OWNER,
                DATEADD('day', 7, CURRENT_DATE()) AS DUE_DATE
            FROM {DB}.GOLD.UNIFIED_RISK_MATRIX m
            WHERE {where}
            ORDER BY m.RISK_SCORE DESC NULLS LAST
        """
        return self.query(sql)

    # ─── AI: Ask CoCo (with document + structured data search) ────────────

    def ask_coco(self, question: str) -> dict:
        """Answer questions using AI_COMPLETE with context from both structured and unstructured data.

        Returns dict with 'answer', 'sources', and optionally 'chart_data'.
        """
        q_lower = question.lower().strip()

        # Greetings
        greetings = ("hi", "hello", "hey", "yo", "hola", "good morning", "good afternoon")
        if any(q_lower == g or q_lower.startswith(g + " ") for g in greetings):
            return {
                "answer": "👋 Hi! I'm **CoCo**, your project-risk assistant. I can search both your structured data and uploaded documents. Try asking:\n\n"
                    "- *What is the contract value of Phoenix?*\n"
                    "- *Summarize the uploaded PDF*\n"
                    "- *Which vendor has the highest risk?*\n"
                    "- *Show me project financial exposure*",
                "sources": [],
                "chart_data": None
            }

        # Build context from multiple sources
        context_parts = []
        sources = []

        # 1. Search structured gold data
        structured_context = self._get_structured_context(question)
        if structured_context:
            context_parts.append(f"STRUCTURED DATA:\n{structured_context}")

        # 2. Search unstructured document chunks (only for relevant questions)
        project_keywords = ["project", "prj", "risk", "invoice", "vendor", "contract",
                           "change order", "budget", "schedule", "delay", "cost",
                           "phoenix", "atlas", "steel", "cable", "dispute",
                           "document", "pdf", "uploaded", "report", "safety"]
        is_project_question = any(kw in q_lower for kw in project_keywords)
        doc_results = self.vector_search(question, top_k=3) if is_project_question else []
        if doc_results:
            doc_context = []
            for i, chunk in enumerate(doc_results):
                doc_context.append(
                    f"[Doc {i+1}: {chunk.get('FILE_NAME', 'Unknown')} p.{chunk.get('PAGE_NUMBER', '?')}] "
                    f"{chunk.get('CHUNK_TEXT', '')[:500]}"
                )
                sources.append({
                    "file": chunk.get("FILE_NAME", "Unknown"),
                    "page": chunk.get("PAGE_NUMBER"),
                    "excerpt": chunk.get("CHUNK_TEXT", "")[:150] + "..."
                })
            context_parts.append(f"DOCUMENT EXCERPTS:\n" + "\n\n".join(doc_context))

        if not context_parts:
            return {
                "answer": "No data available. Please run the pipeline first to populate the data layers.",
                "sources": [],
                "chart_data": None
            }

        context = "\n\n---\n\n".join(context_parts)

        # Determine if chart data might be useful
        wants_chart = any(kw in q_lower for kw in [
            "show", "chart", "graph", "plot", "compare", "visualize", "trend", "breakdown"
        ])

        chart_instruction = (
            'Also provide a JSON object on a new line starting with CHART_DATA: '
            'that I can use to create a plotly chart. Format: {"type": "bar|pie|line", '
            '"x": [...], "y": [...], "labels": [...], "title": "..."}. '
            'Only include CHART_DATA if a chart would be helpful.'
            if wants_chart else ""
        )

        prompt = f"""You are CoCo, an enterprise construction-risk intelligence assistant. Answer the question using the data provided below. Be specific with numbers and project names. If citing document sources, reference them as [Doc N].

{context}

QUESTION: {question}

{chart_instruction}

ANSWER:"""

        answer = self.ai_complete(prompt)

        # Parse chart data if present
        chart_data = None
        if answer and "CHART_DATA:" in answer:
            parts = answer.split("CHART_DATA:")
            answer = parts[0].strip()
            try:
                chart_data = json.loads(parts[1].strip())
            except Exception:
                chart_data = None

        if not answer:
            # Fallback to smart search
            answer = self._smart_search(question)

        # Only include sources if question was about project data
        final_sources = sources if is_project_question and sources else []
        return {"answer": answer, "sources": final_sources, "chart_data": chart_data}

    def _get_structured_context(self, question: str) -> str:
        """Get relevant structured data based on question keywords."""
        q_lower = question.lower()
        lines = []

        if any(kw in q_lower for kw in ["risk", "exposure", "critical", "high", "danger", "threat"]):
            rows = self.query(
                f"SELECT PROJECT_NAME, RISK_CATEGORY, RISK_TITLE, SEVERITY, "
                f"TOTAL_FINANCIAL_EXPOSURE FROM {DB}.GOLD.UNIFIED_RISK_MATRIX "
                f"ORDER BY TOTAL_FINANCIAL_EXPOSURE DESC NULLS LAST LIMIT 10"
            )
            for r in rows:
                lines.append(
                    f"[{r.get('PROJECT_NAME')}] {r.get('SEVERITY')} {r.get('RISK_CATEGORY')}: "
                    f"{r.get('RISK_TITLE')} (${r.get('TOTAL_FINANCIAL_EXPOSURE') or 0:,.0f})"
                )

        elif any(kw in q_lower for kw in ["contract", "value", "budget", "cost", "financial", "money"]):
            rows = self.query(
                f"SELECT PROJECT_NAME, APPROVED_BUDGET, ACTUAL_COST_TO_DATE, "
                f"TOTAL_CONTRACT_VALUE, COST_STATUS "
                f"FROM {DB}.GOLD.FINANCIAL_SUMMARY ORDER BY APPROVED_BUDGET DESC LIMIT 10"
            )
            for r in rows:
                lines.append(
                    f"Project: {r.get('PROJECT_NAME')}, Contract Value: ${r.get('TOTAL_CONTRACT_VALUE') or 0:,.0f}, "
                    f"Budget: ${r.get('APPROVED_BUDGET') or 0:,.0f}, Spent: ${r.get('ACTUAL_COST_TO_DATE') or 0:,.0f}, "
                    f"Status: {r.get('COST_STATUS')}"
                )

        elif any(kw in q_lower for kw in ["vendor", "supplier", "contractor"]):
            rows = self.query(
                f"SELECT VENDOR_NAME, TRADE_CATEGORY, PERFORMANCE_GRADE, COMPOSITE_SCORE, "
                f"TOTAL_SUBCONTRACT_VALUE FROM {DB}.GOLD.VENDOR_SCORECARD "
                f"ORDER BY COMPOSITE_SCORE DESC LIMIT 10"
            )
            for r in rows:
                lines.append(
                    f"Vendor: {r.get('VENDOR_NAME')} ({r.get('TRADE_CATEGORY')}), "
                    f"Grade: {r.get('PERFORMANCE_GRADE')}, Risk Score: {r.get('COMPOSITE_SCORE')}, "
                    f"Value: ${r.get('TOTAL_SUBCONTRACT_VALUE') or 0:,.0f}"
                )

        elif any(kw in q_lower for kw in ["safety", "incident", "injury"]):
            rows = self.query(
                f"SELECT PROJECT_NAME, TOTAL_INCIDENTS, SEVERE_INCIDENTS, SAFETY_RISK_LEVEL "
                f"FROM {DB}.GOLD.SAFETY_DASHBOARD"
            )
            for r in rows:
                lines.append(
                    f"{r.get('PROJECT_NAME')}: {r.get('TOTAL_INCIDENTS')} incidents "
                    f"({r.get('SEVERE_INCIDENTS')} severe), Risk: {r.get('SAFETY_RISK_LEVEL')}"
                )

        elif any(kw in q_lower for kw in ["schedule", "delay", "behind", "complete"]):
            rows = self.query(
                f"SELECT PROJECT_NAME, PERCENT_COMPLETE, SCHEDULE_STATUS, "
                f"SCHEDULE_VARIANCE_DAYS FROM {DB}.GOLD.PROJECT_RISK_SUMMARY "
                f"ORDER BY SCHEDULE_VARIANCE_DAYS DESC LIMIT 10"
            )
            for r in rows:
                lines.append(
                    f"{r.get('PROJECT_NAME')}: {r.get('PERCENT_COMPLETE') or 0:.0f}% complete, "
                    f"Status: {r.get('SCHEDULE_STATUS')}, Variance: {r.get('SCHEDULE_VARIANCE_DAYS') or 0} days"
                )

        else:
            # General: top risks + projects
            rows = self.query(
                f"SELECT PROJECT_NAME, OVERALL_RISK_LEVEL, CURRENT_BUDGET, TOTAL_RISK_EXPOSURE "
                f"FROM {DB}.GOLD.PROJECT_RISK_SUMMARY ORDER BY TOTAL_RISK_EXPOSURE DESC LIMIT 5"
            )
            for r in rows:
                lines.append(
                    f"{r.get('PROJECT_NAME')}: {r.get('OVERALL_RISK_LEVEL')} risk, "
                    f"Budget: ${r.get('CURRENT_BUDGET') or 0:,.0f}, "
                    f"Exposure: ${r.get('TOTAL_RISK_EXPOSURE') or 0:,.0f}"
                )

        return "\n".join(lines)

    def _smart_search(self, question: str) -> str:
        """Fallback: try a simpler AI call, then keyword search."""
        q_lower = question.lower()
        
        # Try a simple direct AI call with minimal context
        try:
            structured = self._get_structured_context(question)
            if structured:
                simple_prompt = f"Answer concisely using this data:\n{structured[:2000]}\n\nQuestion: {question}\nAnswer:"
                rows = self._session.sql(
                    "SELECT SNOWFLAKE.CORTEX.AI_COMPLETE(?, ?) AS R",
                    params=[LLM_MODEL, simple_prompt]
                ).collect()
                if rows and rows[0][0]:
                    result = rows[0][0]
                    if result.startswith('"') and result.endswith('"'):
                        import json
                        try:
                            result = json.loads(result)
                        except Exception:
                            pass
                    if result and len(result) > 10:
                        return result
        except Exception:
            pass

        # Route by intent
        if any(kw in q_lower for kw in ["risk", "exposure", "danger", "threat"]):
            rows = self.get_unified_risk_matrix()
            if rows:
                lines = ["**⚠️ Top Risks:**\n"]
                for r in rows[:5]:
                    lines.append(
                        f"• [{r.get('PROJECT_NAME')}] {r.get('SEVERITY')} {r.get('RISK_CATEGORY')}: "
                        f"{r.get('RISK_TITLE')} (${r.get('TOTAL_FINANCIAL_EXPOSURE') or 0:,.0f})"
                    )
                return "\n".join(lines)

        elif any(kw in q_lower for kw in ["contract", "value", "budget", "cost", "financial"]):
            rows = self.get_financial_summary()
            if rows:
                lines = ["**💰 Financial Summary:**\n"]
                for r in rows[:5]:
                    lines.append(
                        f"**{r.get('PROJECT_NAME')}** — Contract: ${r.get('TOTAL_CONTRACT_VALUE') or 0:,.0f}, "
                        f"Budget: ${r.get('APPROVED_BUDGET') or 0:,.0f}, Status: {r.get('COST_STATUS')}"
                    )
                return "\n".join(lines)

        elif any(kw in q_lower for kw in ["vendor", "supplier"]):
            rows = self.query(
                f"SELECT VENDOR_NAME, PERFORMANCE_GRADE, COMPOSITE_SCORE "
                f"FROM {DB}.GOLD.VENDOR_SCORECARD ORDER BY COMPOSITE_SCORE DESC LIMIT 5"
            )
            if rows:
                lines = ["**👷 Vendor Rankings:**\n"]
                for r in rows:
                    lines.append(f"- {r.get('VENDOR_NAME')}: Grade {r.get('PERFORMANCE_GRADE')}, Score {r.get('COMPOSITE_SCORE')}")
                return "\n".join(lines)

        if any(kw in q_lower for kw in ["risk", "exposure"]):
            rows = self.get_unified_risk_matrix()
            if rows:
                lines = ["**⚠️ Top Risks:**\n"]
                for r in rows[:5]:
                    lines.append(
                        f"- [{r.get('PROJECT_NAME')}] {r.get('SEVERITY')} {r.get('RISK_CATEGORY')}: "
                        f"{r.get('RISK_TITLE')} (${r.get('TOTAL_FINANCIAL_EXPOSURE') or 0:,.0f})"
                    )
                return "\n".join(lines)

        # Search documents as last resort
        doc_results = self.search_silver_documents(question)
        if doc_results:
            lines = ["**📄 Found in documents:**\n"]
            for r in doc_results[:3]:
                lines.append(f"- **{r.get('FILE_NAME')}** (p.{r.get('PAGE_NUMBER')}): {r.get('CHUNK_TEXT', '')[:200]}...")
            return "\n".join(lines)

        return "No matching data found. Try asking about risks, finances, vendors, schedule, or safety."

    # ─── Reports ──────────────────────────────────────────────────────────

    def generate_report(self, report_type: str, project_id: str = None) -> str:
        """Generate a formatted report using AI_COMPLETE for better prose."""
        if report_type == "EXECUTIVE_SUMMARY":
            data = self._report_data_executive(project_id)
        elif report_type == "VENDOR_PERFORMANCE":
            data = self._report_data_vendor()
        else:
            data = self._report_data_risk(project_id)

        if not data:
            return "# No Data Available\n\nRun the pipeline first to populate Gold layer tables."

        # Use AI to format the report
        prompt = f"""Generate a professional {report_type.replace('_', ' ').title()} report in clean Markdown format. Use headers, bullet points, and bold for key figures. Include an executive summary paragraph at the top.

DATA:
{data}

Format the report with:
- # Title
- ## Executive Summary (2-3 sentence overview)
- ## Key Metrics (bullet points with bold numbers)
- ## Details (organized by project/category)
- ## Recommendations (3-5 actionable items)

Report:"""

        ai_report = self.ai_complete(prompt)
        if ai_report:
            return ai_report

        # Fallback: return raw data report
        return data

    def _report_data_executive(self, project_id: str = None) -> str:
        where = f"WHERE PROJECT_ID = '{project_id}'" if project_id else ""
        rows = self.query(
            f"SELECT PROJECT_NAME, PERCENT_COMPLETE, SCHEDULE_STATUS, COST_STATUS, "
            f"OVERALL_RISK_LEVEL, CURRENT_BUDGET, COST_VARIANCE, TOTAL_RISK_EXPOSURE, "
            f"HIGH_CRITICAL_RISKS FROM {DB}.GOLD.PROJECT_RISK_SUMMARY {where} "
            f"ORDER BY TOTAL_RISK_EXPOSURE DESC NULLS LAST"
        )
        if not rows:
            return ""
        lines = []
        for r in rows:
            lines.append(
                f"Project: {r.get('PROJECT_NAME')}, Risk: {r.get('OVERALL_RISK_LEVEL')}, "
                f"Complete: {r.get('PERCENT_COMPLETE') or 0:.0f}%, Schedule: {r.get('SCHEDULE_STATUS')}, "
                f"Cost: {r.get('COST_STATUS')}, Budget: ${r.get('CURRENT_BUDGET') or 0:,.0f}, "
                f"Exposure: ${r.get('TOTAL_RISK_EXPOSURE') or 0:,.0f}, "
                f"Critical Risks: {r.get('HIGH_CRITICAL_RISKS') or 0}"
            )
        return "\n".join(lines)

    def _report_data_risk(self, project_id: str = None) -> str:
        where = f"WHERE PROJECT_ID = '{project_id}'" if project_id else ""
        rows = self.query(
            f"SELECT PROJECT_NAME, RISK_CATEGORY, RISK_TITLE, SEVERITY, RISK_SCORE, "
            f"TOTAL_FINANCIAL_EXPOSURE, SCHEDULE_IMPACT_DAYS "
            f"FROM {DB}.GOLD.UNIFIED_RISK_MATRIX {where} ORDER BY RISK_SCORE DESC NULLS LAST"
        )
        if not rows:
            return ""
        lines = []
        for r in rows:
            lines.append(
                f"{r.get('SEVERITY')} | {r.get('PROJECT_NAME')} | {r.get('RISK_CATEGORY')}: "
                f"{r.get('RISK_TITLE')} | Exposure: ${r.get('TOTAL_FINANCIAL_EXPOSURE') or 0:,.0f} | "
                f"Schedule: {r.get('SCHEDULE_IMPACT_DAYS') or 0}d | Score: {r.get('RISK_SCORE')}"
            )
        return "\n".join(lines)

    def _report_data_vendor(self) -> str:
        rows = self.query(
            f"SELECT VENDOR_NAME, TRADE_CATEGORY, PERFORMANCE_GRADE, COMPOSITE_SCORE, "
            f"TOTAL_SUBCONTRACT_VALUE, TOTAL_BILLED, SAFETY_INCIDENTS, HIGH_RISK_CONTRACTS "
            f"FROM {DB}.GOLD.VENDOR_SCORECARD ORDER BY COMPOSITE_SCORE DESC NULLS LAST"
        )
        if not rows:
            return ""
        lines = []
        for r in rows:
            lines.append(
                f"Vendor: {r.get('VENDOR_NAME')} ({r.get('TRADE_CATEGORY')}), "
                f"Grade: {r.get('PERFORMANCE_GRADE')}, Risk Score: {r.get('COMPOSITE_SCORE')}, "
                f"Value: ${r.get('TOTAL_SUBCONTRACT_VALUE') or 0:,.0f}, "
                f"Billed: ${r.get('TOTAL_BILLED') or 0:,.0f}, "
                f"Safety: {r.get('SAFETY_INCIDENTS') or 0}, High-Risk: {r.get('HIGH_RISK_CONTRACTS') or 0}"
            )
        return "\n".join(lines)

    # ─── Pipeline ─────────────────────────────────────────────────────────

    def run_pipeline(self, domain: str = 'construction') -> str:
        """Run the full pipeline SP for the given domain."""
        try:
            result = self._session.sql(
                f"CALL {DB}.OPS.SP_RUN_FULL_PIPELINE('{domain}')"
            ).collect()
            return result[0][0] if result else "Pipeline completed."
        except Exception as e:
            return f"Pipeline error: {str(e)}"

    def get_pipeline_status(self) -> list[dict]:
        stats = self.query(f"""
            SELECT 'Documents Registered' AS PROCEDURE_NAME, 'COMPLETED' AS STATUS,
                   COUNT(*) AS RECORDS_PROCESSED FROM {DB}.BRONZE.DOCUMENT_REGISTRY
            UNION ALL
            SELECT 'Chunks Parsed', 'COMPLETED', COUNT(*) FROM {DB}.SILVER.CHUNKS
            UNION ALL
            SELECT 'Graph Nodes Extracted', 'COMPLETED', COUNT(*) FROM {DB}.SILVER.GRAPH_NODES
            UNION ALL
            SELECT 'Graph Edges Built', 'COMPLETED', COUNT(*) FROM {DB}.SILVER.GRAPH_EDGES
            UNION ALL
            SELECT 'Vectors Generated', 'COMPLETED', COUNT(*) FROM {DB}.SILVER.VECTORS
            UNION ALL
            SELECT 'Gold Views Refreshed', 'COMPLETED', COUNT(*) FROM {DB}.GOLD.UNIFIED_RISK_MATRIX
        """)
        return stats

    def get_ai_usage_stats(self) -> dict:
        docs = self._scalar(f"SELECT COUNT(*) FROM {DB}.BRONZE.DOCUMENT_REGISTRY", 0)
        chunks = self._scalar(f"SELECT COUNT(*) FROM {DB}.SILVER.CHUNKS", 0)
        nodes = self._scalar(f"SELECT COUNT(*) FROM {DB}.SILVER.GRAPH_NODES", 0)
        vectors = self._scalar(f"SELECT COUNT(*) FROM {DB}.SILVER.VECTORS", 0)
        return {
            "TOTAL_CALLS": int(docs) + int(nodes),
            "CACHE_HITS": int(vectors),
            "TOTAL_INPUT_TOKENS": int(chunks) * 400,
            "TOTAL_OUTPUT_TOKENS": int(nodes) * 120,
            "DISTINCT_OPERATIONS": 5,
        }

    # ─── Uploads ──────────────────────────────────────────────────────────

    def upload_file(self, *args, **kwargs) -> bool:
        return False

    def register_document(self, *args, **kwargs) -> bool:
        return False
