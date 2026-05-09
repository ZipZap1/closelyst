"""Replicate AI image helpers: text-to-image and image enhancement.

Two entry points:
  - generate_image(prompt, out_path)  -> Flux Schnell, fast and cheap
  - enhance_image(in_path, out_path)  -> Real-ESRGAN upscale + clean up

Both block until the prediction is done. Replicate's Prefer:wait header
keeps a single request open for up to 60s, which is plenty for these
models. We fall back to a polling loop if the sync path doesn't return.
"""
import os
import time
import requests

API_BASE = "https://api.replicate.com/v1"
FLUX_SCHNELL = "black-forest-labs/flux-schnell"
REAL_ESRGAN = "nightmareai/real-esrgan"
REAL_ESRGAN_VERSION = (
    "f121d640bd286e1fdc67f9799164c1d5be36ff74576ee11c803ae5b665dd46aa"
)
LATENTSYNC = "bytedance/latentsync"


def _token():
    token = os.environ.get("REPLICATE_API_TOKEN", "").strip()
    if not token:
        raise RuntimeError(
            "REPLICATE_API_TOKEN not set. Sign up at replicate.com, "
            "create an API token, then add it to .env or Streamlit secrets."
        )
    return token


def _headers(prefer_wait=False):
    h = {
        "Authorization": f"Bearer {_token()}",
        "Content-Type": "application/json",
    }
    if prefer_wait:
        h["Prefer"] = "wait=60"
    return h


def _poll_until_done(prediction_id, timeout=120):
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(2)
        r = requests.get(
            f"{API_BASE}/predictions/{prediction_id}",
            headers=_headers(),
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        status = data.get("status")
        if status == "succeeded":
            return data
        if status in ("failed", "canceled"):
            raise RuntimeError(f"Replicate prediction {status}: {data.get('error')}")
    raise RuntimeError("Replicate prediction timed out")


def _download(url, out_path):
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    with open(out_path, "wb") as f:
        f.write(r.content)
    return out_path


def generate_image(prompt, out_path, aspect_ratio="9:16"):
    """Text-to-image via Flux Schnell. Returns out_path on success."""
    styled = f"{prompt}, cinematic, vibrant colors, professional photography, sharp focus"
    r = requests.post(
        f"{API_BASE}/models/{FLUX_SCHNELL}/predictions",
        headers=_headers(prefer_wait=True),
        json={
            "input": {
                "prompt": styled[:500],
                "aspect_ratio": aspect_ratio,
                "num_outputs": 1,
                "output_format": "png",
                "go_fast": True,
            }
        },
        timeout=90,
    )
    r.raise_for_status()
    data = r.json()
    if data.get("status") != "succeeded":
        data = _poll_until_done(data["id"])
    output = data.get("output")
    if not output:
        raise RuntimeError("Replicate returned no output")
    img_url = output[0] if isinstance(output, list) else output
    return _download(img_url, out_path)


def _upload_to_replicate(file_path, content_type):
    """Upload a binary file via Replicate's /v1/files API. Returns a URL string.

    Used for inputs too large to embed as base64 data URIs comfortably
    (videos in particular). Replicate's files endpoint accepts multipart
    uploads and returns a URL we can reference in subsequent predictions.
    """
    with open(file_path, "rb") as f:
        files = {"content": (os.path.basename(file_path), f, content_type)}
        r = requests.post(
            f"{API_BASE}/files",
            headers={"Authorization": f"Bearer {_token()}"},
            files=files,
            timeout=300,
        )
    r.raise_for_status()
    data = r.json()
    url = data.get("urls", {}).get("get") or data.get("url")
    if not url:
        raise RuntimeError(f"Replicate file upload returned no URL: {data}")
    return url


def lipsync_video(video_in_path, audio_path, out_path):
    """Sync the lips of the person in video_in_path to audio_path's voice.

    Uses bytedance/latentsync via Replicate. The model returns a new video
    file with lip movements aligned to the audio. Uses the file-upload
    endpoint for both inputs because base64 data URIs are too heavy for
    typical 5-30s phone videos.
    """
    video_url = _upload_to_replicate(video_in_path, "video/mp4")
    audio_url = _upload_to_replicate(audio_path, "audio/mpeg")

    r = requests.post(
        f"{API_BASE}/models/{LATENTSYNC}/predictions",
        headers=_headers(prefer_wait=True),
        json={
            "input": {
                "video": video_url,
                "audio": audio_url,
            }
        },
        timeout=300,
    )
    r.raise_for_status()
    data = r.json()
    if data.get("status") != "succeeded":
        data = _poll_until_done(data["id"], timeout=300)
    output = data.get("output")
    if not output:
        raise RuntimeError("LatentSync returned no output")
    out_url = output if isinstance(output, str) else output[0]
    return _download(out_url, out_path)


def enhance_image(in_path, out_path, scale=2):
    """Upscale and clean an image via Real-ESRGAN. Returns out_path on success."""
    with open(in_path, "rb") as f:
        # Replicate takes a URL or a base64 data URI as input. Use base64.
        import base64
        ext = os.path.splitext(in_path)[1].lstrip(".").lower() or "png"
        if ext == "jpg":
            ext = "jpeg"
        b64 = base64.b64encode(f.read()).decode("ascii")
        data_uri = f"data:image/{ext};base64,{b64}"

    r = requests.post(
        f"{API_BASE}/predictions",
        headers=_headers(prefer_wait=True),
        json={
            "version": REAL_ESRGAN_VERSION,
            "input": {
                "image": data_uri,
                "scale": scale,
                "face_enhance": False,
            },
        },
        timeout=120,
    )
    r.raise_for_status()
    data = r.json()
    if data.get("status") != "succeeded":
        data = _poll_until_done(data["id"])
    output = data.get("output")
    if not output:
        raise RuntimeError("Replicate returned no output")
    img_url = output if isinstance(output, str) else output[0]
    return _download(img_url, out_path)
