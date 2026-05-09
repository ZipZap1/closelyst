"""Lemon Squeezy License Key validation and checkout URL helpers."""
import os
from datetime import datetime, timezone

import requests

API_BASE = "https://api.lemonsqueezy.com/v1"


def _api_headers():
    api_key = os.environ.get("LEMONSQUEEZY_API_KEY", "").strip()
    return {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/vnd.api+json",
        "Content-Type": "application/vnd.api+json",
    }


def _fetch_subscription_for_order(order_id):
    """Return the subscription attributes dict for a given order, or None.

    One-shot purchases have no subscription, in which case the filtered list
    comes back empty and we return None. Pro Monthly purchases have one.
    """
    api_key = os.environ.get("LEMONSQUEEZY_API_KEY", "").strip()
    if not api_key or not order_id:
        return None
    try:
        r = requests.get(
            f"{API_BASE}/subscriptions",
            headers={"Authorization": f"Bearer {api_key}", "Accept": "application/vnd.api+json"},
            params={"filter[order_id]": order_id},
            timeout=15,
        )
        if r.status_code != 200:
            return None
        items = r.json().get("data") or []
        if not items:
            return None
        return items[0].get("attributes")
    except requests.RequestException:
        return None


def _parse_iso(ts):
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return None


def _maybe_reset_billing_cycle(license_id, current_expires_at, sub_attrs):
    """If the subscription has rolled into a new period, zero the activation_usage
    and push expires_at to the upcoming renews_at so we recognise the new cycle.

    Returns the updated license_key attributes dict if a reset happened, else None.
    """
    if not sub_attrs or sub_attrs.get("status") not in ("active", "on_trial"):
        return None
    renews_at = sub_attrs.get("renews_at")
    if not renews_at:
        return None
    now = datetime.now(timezone.utc)
    expires = _parse_iso(current_expires_at)
    if expires and expires > now:
        return None  # still inside the current cycle, nothing to do
    try:
        r = requests.patch(
            f"{API_BASE}/license-keys/{license_id}",
            headers=_api_headers(),
            json={
                "data": {
                    "type": "license-keys",
                    "id": str(license_id),
                    "attributes": {
                        "activation_usage": 0,
                        "expires_at": renews_at,
                    },
                }
            },
            timeout=15,
        )
        if r.status_code == 200:
            return r.json().get("data", {}).get("attributes", {})
    except requests.RequestException:
        pass
    return None


def validate_license_key(license_key):
    """Validate a license key against Lemon Squeezy.

    Returns dict: {
        "valid": bool,
        "activation_limit": int|None,   # None means unlimited
        "activation_usage": int,
        "key_id": int|None,
        "renews_at": str|None,          # ISO timestamp of next subscription renewal
        "reason": str (optional),
    }

    Also auto-resets activation_usage to 0 when the subscription has rolled
    into a new billing cycle, so a Pro user who hit the cap last month
    starts fresh once their bank charge goes through. Detection is by
    comparing license_key.expires_at to now: when expires_at is missing or
    past, push it to subscription.renews_at and zero the usage.
    """
    if not license_key or len(license_key.strip()) < 10:
        return {"valid": False, "reason": "Empty or too short"}

    try:
        r = requests.post(
            f"{API_BASE}/licenses/validate",
            data={"license_key": license_key.strip()},
            timeout=15,
        )
        if r.status_code != 200:
            return {"valid": False, "reason": f"HTTP {r.status_code}"}
        data = r.json()
        if not bool(data.get("valid", False)):
            return {"valid": False, "reason": data.get("error") or "License invalid"}
        lk = data.get("license_key") or {}
        meta = data.get("meta") or {}

        # Try auto-reset on subscription renewal
        renews_at = None
        license_id = lk.get("id")
        order_id = meta.get("order_id")
        if license_id and order_id:
            sub_attrs = _fetch_subscription_for_order(order_id)
            if sub_attrs:
                renews_at = sub_attrs.get("renews_at")
                updated = _maybe_reset_billing_cycle(
                    license_id, lk.get("expires_at"), sub_attrs
                )
                if updated:
                    lk["activation_usage"] = updated.get("activation_usage", 0) or 0
                    lk["expires_at"] = updated.get("expires_at")

        return {
            "valid": True,
            "activation_limit": lk.get("activation_limit"),
            "activation_usage": lk.get("activation_usage", 0) or 0,
            "key_id": license_id,
            "renews_at": renews_at,
        }
    except requests.RequestException as e:
        return {"valid": False, "reason": str(e)}


def activate_license_key(license_key, instance_name):
    """Consume one activation slot. Returns dict: {"activated": bool, "reason": str}.

    Used for one-shot keys (Watermark Remove). Each successful activation
    increments activation_usage; once usage >= activation_limit, further
    activations fail and the key is effectively spent.
    """
    if not license_key:
        return {"activated": False, "reason": "Empty key"}
    try:
        r = requests.post(
            f"{API_BASE}/licenses/activate",
            data={
                "license_key": license_key.strip(),
                "instance_name": instance_name,
            },
            timeout=15,
        )
        if r.status_code in (200, 201):
            data = r.json()
            if data.get("activated"):
                return {"activated": True}
            return {"activated": False, "reason": data.get("error") or "Activation failed"}
        return {"activated": False, "reason": f"HTTP {r.status_code}"}
    except requests.RequestException as e:
        return {"activated": False, "reason": str(e)}


def get_buy_url(product_id):
    """Fetch the canonical buy_now_url for a product via Lemon Squeezy API.

    Earlier versions tried to hand-build the URL from a store subdomain plus
    product ID. That broke for stores with a custom domain and uses the wrong
    path/format anyway (LS uses /checkout/buy/<variant-uuid>, not
    /buy/<product-id>). Asking the API for the canonical URL avoids both
    issues and follows whatever the store's current domain config is.
    """
    api_key = os.environ.get("LEMONSQUEEZY_API_KEY", "").strip()
    pid = str(product_id).strip()
    if not api_key or not pid:
        return ""
    try:
        r = requests.get(
            f"{API_BASE}/products/{pid}",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/vnd.api+json",
            },
            timeout=15,
        )
        if r.status_code == 200:
            return (
                r.json()
                .get("data", {})
                .get("attributes", {})
                .get("buy_now_url", "")
            )
    except requests.RequestException:
        pass
    return ""
