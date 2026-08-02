# Risk Command Center Streamlit component (data_quality tab).
# Co-authored with CoCo
"""
Tab 9: Data Quality Exception Center.
Identifies contract mismatches, missing notifications, and other exceptions.
"""

import streamlit as st
import pandas as pd
from app.utils.snowflake_client import SnowflakeClient

def render(client: SnowflakeClient):
    """Render the Data Quality Exception Center tab."""
    st.header("🔒 Data Quality Exception Center")
    st.caption("Identifies mismatches between structured registers and unstructured PDF documents")

    # Get data quality exceptions
    exceptions = client.get_data_quality_exceptions()

    if not exceptions:
        st.success("🎉 No active data quality exceptions detected. All records match!")
        return

    st.subheader(f"⚠️ Active Exceptions ({len(exceptions)} found)")

    # Dataframe overview
    df = pd.DataFrame(exceptions)
    st.dataframe(df, use_container_width=True)

    st.divider()
    st.subheader("🔍 Breakdown of Exceptions")

    # Detail Cards
    for item in exceptions:
        severity = item.get("SEVERITY", "Low")
        sev_color = "🔴" if severity == "Critical" else "🟠" if severity == "High" else "🟡"
        
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"### {sev_color} {item.get('CHECK_TYPE', 'Mismatch')}")
                st.markdown(f"**Project:** {item.get('PROJECT_NAME', '')} | **Ref:** `{item.get('SOURCE_REF_ID', '')}`")
                st.markdown(f"**Expected (Structured):** `{item.get('EXPECTED_VALUE', '')}`")
                st.markdown(f"**Observed (Document):** `{item.get('OBSERVED_VALUE', '')}`")
            with col2:
                st.metric("Severity", severity)
                
            st.markdown(f"**Business Impact:** {item.get('BUSINESS_IMPACT', 'N/A')}")
            st.info(f"💡 **Recommended Fix:** {item.get('RECOMMENDED_FIX', 'No fix defined')}")
            
            # Action update (advisory — checks are derived from live source tables)
            if st.button("🔄 Dismiss / Force Match", key=f"dismiss_{item.get('CHECK_ID')}"):
                st.session_state[f"dq_dismissed_{item.get('CHECK_ID')}"] = True
                st.success("Exception acknowledged. Reconcile the source records to clear it permanently.")
