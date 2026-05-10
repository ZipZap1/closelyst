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
FLUX_DEV = "black-forest-labs/flux-dev"
LLAMA3_8B = "meta/meta-llama-3-8b-instruct"
# Clarity Upscaler and LatentSync are not "official" Replicate models, so
# the /v1/models/{owner}/{name}/predictions shortcut returns 404. We pin a
# version hash and POST to /v1/predictions instead.
CLARITY_UPSCALER_VERSION = "dfad41707589d68ecdccd1dfa600d55a208f9310748e44bfe35b4a6291453d5e"
LATENTSYNC_VERSION = "637ce1919f807ca20da3a448ddc2743535d2853649574cd52a933120e9b9e293"


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


def text_to_visual_prompt(voiceover_text):
    """Turn a (possibly German) voiceover script into a vivid English visual
    scene description for Flux. Falls back to the original text on error.

    Flux is trained mostly on English visual captions, not spoken scripts.
    Passing a raw German voiceover sentence yields generic or off-topic
    images. Asking an LLM to extract the topic and rewrite it as one
    concrete English scene fixes that.
    """
    cleaned = (voiceover_text or "").strip()
    if len(cleaned) < 5:
        return cleaned

    system = (
        "You convert short voiceover scripts into a single English visual "
        "scene description for an AI image generator. Output ONE concrete, "
        "vivid scene that matches the topic of the script. Focus on "
        "setting, subject, mood, lighting, colors. No people speaking, no "
        "captions, no text in the image. Keep it under 30 words. "
        "Output ONLY the description sentence, nothing else, no preamble, "
        "no quotes, no explanation."
    )
    user = f"Voiceover script:\n{cleaned[:500]}\n\nVisual scene:"

    try:
        r = requests.post(
            f"{API_BASE}/models/{LLAMA3_8B}/predictions",
            headers=_headers(prefer_wait=True),
            json={
                "input": {
                    "prompt": user,
                    "system_prompt": system,
                    "max_tokens": 80,
                    "temperature": 0.7,
                }
            },
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        if data.get("status") != "succeeded":
            data = _poll_until_done(data["id"], timeout=30)
        output = data.get("output")
        if not output:
            return cleaned
        text = "".join(output) if isinstance(output, list) else str(output)
        text = text.strip()
        # Strip common LLM preambles in case the model ignored the instruction
        for prefix in ("Visual scene:", "Scene:", "Here is", "Here's"):
            if text.lower().startswith(prefix.lower()):
                text = text[len(prefix):].lstrip(":. ").strip()
        # Take first line only, keep it concise
        text = text.split("\n")[0].strip().strip('"').strip("'")
        return text or cleaned
    except Exception:
        return cleaned


def generate_image(prompt, out_path, aspect_ratio="9:16"):
    """Text-to-image via Flux Dev. Returns out_path on success."""
    styled = f"{prompt}, cinematic, vibrant colors, professional photography, sharp focus"
    r = requests.post(
        f"{API_BASE}/models/{FLUX_DEV}/predictions",
        headers=_headers(prefer_wait=True),
        json={
            "input": {
                "prompt": styled[:500],
                "aspect_ratio": aspect_ratio,
                "num_outputs": 1,
                "output_format": "png",
            }
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


SYNC_API_BASE = "https://api.sync.so"
SYNC_MODEL = "lipsync-2"  # general model; "lipsync-2-pro" for premium


def _lipsync_via_sync(video_in_path, audio_path, out_path):
    """Sync.so /v2/generate path. Uploads files via Replicate first to get
    public URLs, then posts a JSON job to sync.so and polls for completion.
    Cleaner than guessing sync.so's multipart endpoint shape."""
    api_key = os.environ.get("SYNC_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("SYNC_API_KEY not set.")

    video_url = _upload_to_replicate(video_in_path, "video/mp4")
    audio_url = _upload_to_replicate(audio_path, "audio/mpeg")

    r = requests.post(
        f"{SYNC_API_BASE}/v2/generate",
        headers={"x-api-key": api_key, "Content-Type": "application/json"},
        json={
            "model": SYNC_MODEL,
            "input": [
                {"type": "video", "url": video_url},
                {"type": "audio", "url": audio_url},
            ],
        },
        timeout=120,
    )
    r.raise_for_status()
    job = r.json()
    job_id = job.get("id")
    if not job_id:
        raise RuntimeError(f"sync.so returned no job id: {job}")

    deadline = time.time() + 300
    while time.time() < deadline:
        time.sleep(3)
        s = requests.get(
            f"{SYNC_API_BASE}/v2/generate/{job_id}",
            headers={"x-api-key": api_key},
            timeout=30,
        )
        s.raise_for_status()
        job = s.json()
        status = (job.get("status") or "").lower()
        if status in ("completed", "succeeded", "done"):
            output = job.get("output") or job.get("outputUrl") or job.get("result")
            if isinstance(output, dict):
                video_url = (
                    output.get("video_url")
                    or output.get("videoUrl")
                    or output.get("url")
                    or output.get("video")
                )
            elif isinstance(output, str):
                video_url = output
            else:
                video_url = None
            if not video_url:
                raise RuntimeError(f"sync.so done but no output URL: {job}")
            return _download(video_url, out_path)
        if status in ("failed", "error", "cancelled", "canceled"):
            raise RuntimeError(f"sync.so {status}: {job.get('error') or job}")
    raise RuntimeError("sync.so prediction timed out")


def _lipsync_via_replicate(video_in_path, audio_path, out_path):
    """Replicate bytedance/latentsync. The only video+audio lip-sync model
    currently hosted on Replicate (Wav2Lip variants returned 404 when we
    tried to swap). ~$0.07 per generation."""
    video_url = _upload_to_replicate(video_in_path, "video/mp4")
    audio_url = _upload_to_replicate(audio_path, "audio/mpeg")

    r = requests.post(
        f"{API_BASE}/predictions",
        headers=_headers(prefer_wait=True),
        json={
            "version": LATENTSYNC_VERSION,
            "input": {"video": video_url, "audio": audio_url},
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


def lipsync_video(video_in_path, audio_path, out_path):
    """Sync the lips of the person in video_in_path to audio_path's voice.

    Routes to sync.so when SYNC_API_KEY is configured (better quality,
    pay-per-use on a separate account), otherwise falls back to Replicate
    bytedance/latentsync (uses the existing Replicate token).
    """
    if os.environ.get("SYNC_API_KEY", "").strip():
        return _lipsync_via_sync(video_in_path, audio_path, out_path)
    return _lipsync_via_replicate(video_in_path, audio_path, out_path)


def enhance_image(in_path, out_path, scale=2):
    """Upscale and sharpen an image via Clarity Upscaler. Returns out_path.

    Clarity is SD-based: low creativity + high resemblance keep the output
    faithful to the source so we don't hallucinate fake details. Good for
    phone photos and product shots that need a quality boost without
    changing the subject.
    """
    import base64
    with open(in_path, "rb") as f:
        ext = os.path.splitext(in_path)[1].lstrip(".").lower() or "png"
        if ext == "jpg":
            ext = "jpeg"
        b64 = base64.b64encode(f.read()).decode("ascii")
        data_uri = f"data:image/{ext};base64,{b64}"

    r = requests.post(
        f"{API_BASE}/predictions",
        headers=_headers(prefer_wait=True),
        json={
            "version": CLARITY_UPSCALER_VERSION,
            "input": {
                "image": data_uri,
                "scale_factor": scale,
                "creativity": 0.3,
                "resemblance": 0.65,
                "output_format": "png",
            },
        },
        timeout=180,
    )
    r.raise_for_status()
    data = r.json()
    if data.get("status") != "succeeded":
        data = _poll_until_done(data["id"], timeout=240)
    output = data.get("output")
    if not output:
        raise RuntimeError("Clarity Upscaler returned no output")
    img_url = output if isinstance(output, str) else output[0]
    return _download(img_url, out_path)
