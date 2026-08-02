# Domain config loader — auto-discovers JSON domain profiles from the domains/ directory.
# Co-authored with CoCo
"""
Domain configuration loader.

Drop a new <domain_id>.json file in app/config/domains/ and it is
automatically discoverable — zero Python changes required.
"""

import json
import os

import streamlit as st

_DOMAINS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "domains")
_DEFAULT_DOMAIN = "construction"


def list_domains() -> list[dict]:
    """Return [{id, display_name, icon}, ...] for every JSON file in domains/."""
    results = []
    try:
        for fname in sorted(os.listdir(_DOMAINS_DIR)):
            if fname.endswith(".json"):
                domain_id = fname[:-5]
                try:
                    cfg = _read_file(domain_id)
                    results.append({
                        "id":           domain_id,
                        "display_name": cfg.get("display_name", domain_id.title()),
                        "icon":         cfg.get("icon", "🔷"),
                    })
                except Exception:
                    pass
    except Exception:
        # Fallback: return construction only
        results = [{"id": "construction", "display_name": "Construction Risk Intelligence", "icon": "🏗️"}]
    return results if results else [{"id": "construction", "display_name": "Construction Risk Intelligence", "icon": "🏗️"}]


def _read_file(domain_id: str) -> dict:
    path = os.path.join(_DOMAINS_DIR, f"{domain_id}.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_domain(domain_id: str) -> dict:
    """Load and return a domain config dict by ID."""
    try:
        return _read_file(domain_id)
    except Exception:
        return _read_file(_DEFAULT_DOMAIN)


def get_cfg() -> dict:
    """Return the currently active domain config (from session state)."""
    if "domain_cfg" not in st.session_state:
        st.session_state["domain_cfg"] = load_domain(_DEFAULT_DOMAIN)
        st.session_state["domain_id"]  = _DEFAULT_DOMAIN
    return st.session_state["domain_cfg"]


def set_domain(domain_id: str) -> None:
    """Switch the active domain and store in session state."""
    cfg = load_domain(domain_id)
    st.session_state["domain_cfg"] = cfg
    st.session_state["domain_id"]  = domain_id
