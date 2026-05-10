"""Polar License Key validation and checkout URL helpers."""
import functools
import os

import requests

API_BASE = "https://api.polar.sh/v1"


@functools.lru_cache(maxsize=1)
def _organization_id():
    token = os.environ.get("POLAR_API_TOKEN", "").strip()
    if not token:
        raise RuntimeError("POLAR_API_TOKEN not set")
    r = requests.get(
        f"{API_BASE}/organizations",
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )
    r.raise_for_status()
    items = r.json().get("items", [])
    if not items:
        raise RuntimeError("No Polar organization found for this token")
    return items[0]["id"]


def _validate_with_polar(license_key, increment_usage=False):
    """Raw POST to Polar validate. Returns parsed JSON or {"_error": ...}."""
    try:
        org_id = _organization_id()
    except Exception as exc:
        return {"_error": f"Cannot resolve organization: {exc}"}
    payload = {"key": license_key.strip(), "organization_id": org_id}
    if increment_usage:
        payload["increment_usage"] = 1
    try:
        r = requests.post(
            f"{API_BASE}/customer-portal/license-keys/validate",
            json=payload,
            timeout=15,
        )
        if r.status_code == 200:
            return r.json()
        return {"_error": f"HTTP {r.status_code}", "_status": r.status_code}
    except requests.RequestException as exc:
        return {"_error": str(exc)}


def validate_license_key(license_key):
    """Validate a Polar license key.

    Returns dict (same contract as the previous LS implementation):
        valid, activation_limit, activation_usage, key_id, renews_at, reason

    Polar mapping:
        activation_limit  <- limit_usage    (max validations a.k.a. exports)
        activation_usage  <- usage          (current count, server-side)
        renews_at         <- expires_at     (subscription end / key expiry)

    Polar invalidates Pro-subscription keys server-side when the subscription
    cancels or expires, so no client-side billing-cycle reset is needed.
    """
    if not license_key or len(license_key.strip()) < 10:
        return {"valid": False, "reason": "Empty or too short"}

    data = _validate_with_polar(license_key)
    if "_error" in data:
        if data.get("_status") == 404:
            return {"valid": False, "reason": "Key nicht gefunden"}
        return {"valid": False, "reason": data["_error"]}

    status = data.get("status", "")
    if status != "granted":
        return {"valid": False, "reason": f"Key {status or 'invalid'}"}

    return {
        "valid": True,
        "activation_limit": data.get("limit_usage"),
        "activation_usage": data.get("usage", 0) or 0,
        "key_id": data.get("id"),
        "renews_at": data.get("expires_at"),
    }


def activate_license_key(license_key, instance_name):
    """Consume one usage slot.

    Polar tracks consumption via increment_usage on the validate endpoint.
    instance_name is accepted for signature compatibility with the previous
    LS implementation but is not used by Polar.
    """
    if not license_key:
        return {"activated": False, "reason": "Empty key"}

    data = _validate_with_polar(license_key, increment_usage=True)
    if "_error" in data:
        if data.get("_status") == 404:
            return {"activated": False, "reason": "Key nicht gefunden"}
        return {"activated": False, "reason": data["_error"]}

    status = data.get("status", "")
    if status != "granted":
        return {"activated": False, "reason": f"Key {status or 'invalid'}"}

    limit = data.get("limit_usage")
    usage = data.get("usage", 0) or 0
    if limit is not None and limit > 0 and usage > limit:
        return {"activated": False, "reason": "Usage-Limit ueberschritten"}

    return {"activated": True}


def get_buy_url(env_var_name):
    """Return the Polar checkout URL stored in the named env var.

    For Polar we keep the full checkout URL in the env var directly (created
    once in the Polar dashboard) instead of building it from a product ID.
    """
    return os.environ.get(env_var_name, "").strip()
