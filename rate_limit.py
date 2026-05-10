"""Free-tier daily rate limiter backed by Supabase Postgres.

Tracks daily video generations per visitor fingerprint and caps the free
tier at FREE_DAILY_LIMIT per day, reset at UTC midnight. Pro users are
not affected.

Identifies visitors by a sha256 hash of (IP, User-Agent). Streamlit
Cloud puts the real client IP in X-Forwarded-For. We hash before storing
so the DB never holds a raw IP, which lowers DSGVO sensitivity.

Failsafe: if Supabase is unreachable or unconfigured, the limiter falls
through and allows the action. Better to lose a few cents on rare DB
outages than to block real users.
"""
import hashlib
import os
from datetime import datetime, timezone

import requests
import streamlit as st

FREE_DAILY_LIMIT = 3


def _supabase_url():
    return (os.environ.get("SUPABASE_URL", "") or "").rstrip("/")


def _supabase_key():
    return os.environ.get("SUPABASE_KEY", "").strip()


def _enabled():
    return bool(_supabase_url() and _supabase_key())


def _headers():
    key = _supabase_key()
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }


def _fingerprint():
    """sha256 of (IP, User-Agent), truncated. Stable per visitor per day,
    safe to store, not personally identifying once hashed.
    """
    ip = ""
    ua = ""
    try:
        headers = st.context.headers
        ip = headers.get("x-forwarded-for", "").split(",")[0].strip()
        if not ip:
            ip = headers.get("remote-addr", "")
        ua = headers.get("user-agent", "")
    except Exception:
        pass
    raw = f"{ip}|{ua}".strip("|")
    if not raw:
        # Fallback: per-session pseudo-id so the limiter still does
        # something locally where headers are unavailable.
        sid = st.session_state.get("_rl_session_id")
        if not sid:
            sid = hashlib.sha256(os.urandom(16)).hexdigest()[:16]
            st.session_state["_rl_session_id"] = sid
        raw = f"session|{sid}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def get_free_quota():
    """Return (used, remaining, limit) for today's UTC date."""
    limit = FREE_DAILY_LIMIT
    if not _enabled():
        return 0, limit, limit
    today = datetime.now(timezone.utc).date().isoformat()
    fp = _fingerprint()
    try:
        r = requests.get(
            f"{_supabase_url()}/rest/v1/free_usage",
            headers=_headers(),
            params={
                "fingerprint": f"eq.{fp}",
                "day": f"eq.{today}",
                "select": "count",
            },
            timeout=10,
        )
        if r.status_code == 200:
            rows = r.json()
            used = rows[0]["count"] if rows else 0
            return used, max(0, limit - used), limit
    except requests.RequestException:
        pass
    return 0, limit, limit


def consume_free_quota():
    """Increment today's counter atomically for this fingerprint.
    Returns the new count after increment, or None on failure.
    """
    if not _enabled():
        return None
    fp = _fingerprint()
    try:
        r = requests.post(
            f"{_supabase_url()}/rest/v1/rpc/increment_free_usage",
            headers=_headers(),
            json={"fp": fp},
            timeout=10,
        )
        if r.status_code == 200:
            return int(r.json())
    except requests.RequestException:
        pass
    return None
