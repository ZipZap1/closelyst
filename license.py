"""Lemon Squeezy License Key validation and checkout URL helpers."""
import os
import requests

API_BASE = "https://api.lemonsqueezy.com/v1"


def validate_license_key(license_key):
    """Validate a license key against Lemon Squeezy.

    Returns dict: {"valid": bool, "reason": str (optional), "meta": dict (optional)}.
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
            return {"valid": bool(data.get("valid", False)), "meta": data}
        return {"valid": False, "reason": f"HTTP {r.status_code}"}
    except requests.RequestException as e:
        return {"valid": False, "reason": str(e)}


def get_checkout_url(product_id):
    """Build a Lemon Squeezy hosted-checkout URL for a product.

    Format: https://<store-subdomain>.lemonsqueezy.com/buy/<product-id>
    """
    subdomain = os.environ.get("LEMONSQUEEZY_STORE_SUBDOMAIN", "").strip()
    if not subdomain or not product_id:
        return ""
    return f"https://{subdomain}.lemonsqueezy.com/buy/{product_id}"
