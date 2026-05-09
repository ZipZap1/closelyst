"""Lemon Squeezy License Key validation and checkout URL helpers."""
import os
import requests

API_BASE = "https://api.lemonsqueezy.com/v1"


def validate_license_key(license_key):
    """Validate a license key against Lemon Squeezy.

    Returns dict: {
        "valid": bool,
        "activation_limit": int|None,   # None means unlimited
        "activation_usage": int,
        "reason": str (optional),
    }
    """
    if not license_key or len(license_key.strip()) < 10:
        return {"valid": False, "reason": "Empty or too short"}

    try:
        r = requests.post(
            f"{API_BASE}/licenses/validate",
            data={"license_key": license_key.strip()},
            timeout=15,
        )
        if r.status_code == 200:
            data = r.json()
            valid = bool(data.get("valid", False))
            if not valid:
                return {"valid": False, "reason": data.get("error") or "License invalid"}
            lk = data.get("license_key") or {}
            return {
                "valid": True,
                "activation_limit": lk.get("activation_limit"),
                "activation_usage": lk.get("activation_usage", 0) or 0,
                "key_id": lk.get("id"),
            }
        return {"valid": False, "reason": f"HTTP {r.status_code}"}
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
