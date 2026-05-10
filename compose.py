"""Compose final TikTok-ready video using FFmpeg plus Pillow.

Captions and watermark are rendered to PNG with Pillow, then overlaid via
FFmpeg's overlay filter. This avoids the drawtext filter which is missing
from many FFmpeg builds (Homebrew default does not include libfreetype).

Word-synced captions when alignment data is provided. Falls back to static
caption when alignment is empty.
"""
import json
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def ensure_ffmpeg():
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg not found on PATH. Install: brew install ffmpeg (macOS).")
    if not shutil.which("ffprobe"):
        raise RuntimeError("ffprobe not found on PATH. Install ffmpeg.")


def get_audio_duration(audio_path):
    cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", str(audio_path)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        return 15.0
    try:
        return float(json.loads(r.stdout)["format"]["duration"])
    except (KeyError, ValueError, json.JSONDecodeError):
        return 15.0


def _safe_text(text, max_chars=80):
    cleaned = (text or "").replace("\n", " ").strip()
    if len(cleaned) > max_chars:
        cleaned = cleaned[:max_chars].rstrip() + "..."
    return cleaned


def _find_font(size):
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _hex_to_rgb(hex_color):
    """Accept #RRGGBB or RRGGBB. Returns (R, G, B). Falls back to white."""
    if not hex_color:
        return (255, 255, 255)
    h = hex_color.lstrip("#")
    if len(h) != 6:
        return (255, 255, 255)
    try:
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    except ValueError:
        return (255, 255, 255)


def _render_text_png(text, out_path, font_size=46, padding=18, max_width=940,
                     bg_alpha=190, text_color="#ffffff", bg_color="#000000"):
    """Render text into a transparent PNG with semi-transparent background box.

    text_color and bg_color accept hex strings ("#ffffff"). bg_alpha 0-255
    controls box opacity, 0 = no box.
    """
    font = _find_font(font_size)
    temp = Image.new("RGBA", (1, 1))
    measure = ImageDraw.Draw(temp)

    words = text.split() or [text]
    lines = []
    current = ""
    for word in words:
        candidate = (current + " " + word).strip()
        bbox = measure.textbbox((0, 0), candidate, font=font)
        if bbox[2] - bbox[0] > max_width and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    if not lines:
        lines = [text or "..."]

    line_spacing = 8
    line_metrics = [measure.textbbox((0, 0), line, font=font) for line in lines]
    line_widths = [bb[2] - bb[0] for bb in line_metrics]
    line_heights = [bb[3] - bb[1] for bb in line_metrics]

    text_width = max(line_widths) if line_widths else 0
    text_height = sum(line_heights) + line_spacing * max(0, len(lines) - 1)

    img_width = max(1, text_width + padding * 2)
    img_height = max(1, text_height + padding * 2)

    img = Image.new("RGBA", (img_width, img_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    if bg_alpha > 0:
        bg_rgb = _hex_to_rgb(bg_color)
        draw.rectangle([0, 0, img_width, img_height], fill=(*bg_rgb, bg_alpha))

    text_rgb = _hex_to_rgb(text_color)
    y = padding
    for line, lw, lh in zip(lines, line_widths, line_heights):
        x = (img_width - lw) // 2
        draw.text((x, y), line, fill=(*text_rgb, 255), font=font)
        y += lh + line_spacing

    img.save(out_path, "PNG")
    return out_path


def _alignment_to_phrases(alignment, target_seconds=1.6, max_words=3):
    """Group ElevenLabs character-level alignment into displayable phrases.

    Returns list of {text, start, end}. Empty list if alignment is empty/invalid.
    """
    if not alignment:
        return []
    chars = alignment.get("characters") or []
    starts = alignment.get("character_start_times_seconds") or []
    ends = alignment.get("character_end_times_seconds") or []
    if not (chars and starts and ends and len(chars) == len(starts) == len(ends)):
        return []

    # Build word list from characters
    words = []
    cur_chars = []
    cur_start = 0.0
    cur_end = 0.0
    for ch, s, e in zip(chars, starts, ends):
        if ch in (" ", "\n", "\t"):
            if cur_chars:
                words.append({"text": "".join(cur_chars), "start": cur_start, "end": cur_end})
                cur_chars = []
        else:
            if not cur_chars:
                cur_start = s
            cur_chars.append(ch)
            cur_end = e
    if cur_chars:
        words.append({"text": "".join(cur_chars), "start": cur_start, "end": cur_end})

    if not words:
        return []

    # Group words into phrases
    phrases = []
    cur_words = [words[0]]
    cur_start = words[0]["start"]
    for w in words[1:]:
        if (len(cur_words) >= max_words or
                (w["end"] - cur_start) >= target_seconds):
            phrases.append({
                "text": " ".join(x["text"] for x in cur_words),
                "start": cur_start,
                "end": cur_words[-1]["end"],
            })
            cur_words = [w]
            cur_start = w["start"]
        else:
            cur_words.append(w)
    if cur_words:
        phrases.append({
            "text": " ".join(x["text"] for x in cur_words),
            "start": cur_start,
            "end": cur_words[-1]["end"],
        })
    return phrases


_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def _is_image(path):
    return Path(path).suffix.lower() in _IMAGE_SUFFIXES


_CAPTION_Y_BY_POSITION = {
    # FFmpeg overlay: H=video_height (1920), h=overlay_height
    # We render the overlay vertically anchored to one of three zones.
    "bottom": "H-h-220",
    "center": "(H-h)/2",
    "top": "220",
}


def compose(audio_path, video_path, output_path, tmp_dir,
            alignment=None, fallback_text="", with_watermark=True,
            caption_style=None, animate_image=True):
    """Render the final 1080x1920 portrait video.

    Background can be either a video file (looped + center-cropped) or a
    still image (looped with a slow Ken-Burns zoom so it doesn't feel
    static). Detection is by file extension.

    animate_image=False disables the Ken-Burns zoom for still backgrounds.
    Use this when the background is intentionally meant to stay static
    (e.g. AI-generated image where the user wants a clean look).

    If alignment is provided and non-empty, captions are word-synced.
    Otherwise falls back to a single static caption from fallback_text.

    caption_style is a dict with optional keys:
      - text_color (hex, default "#ffffff")
      - bg_color   (hex, default "#000000")
      - bg_alpha   (0-255, default 200)
      - font_size  (px, default 64)
      - position   ("bottom"|"center"|"top", default "bottom")
    """
    ensure_ffmpeg()
    duration = get_audio_duration(audio_path)
    tmp_dir = Path(tmp_dir)
    is_image_bg = _is_image(video_path)
    style = {
        "text_color": "#ffffff",
        "bg_color": "#000000",
        "bg_alpha": 200,
        "font_size": 64,
        "position": "bottom",
    }
    if caption_style:
        style.update({k: v for k, v in caption_style.items() if v is not None})

    phrases = _alignment_to_phrases(alignment) if alignment else []
    if not phrases:
        phrases = [{
            "text": _safe_text(fallback_text) or "...",
            "start": 0.0,
            "end": duration,
        }]

    # Render each phrase as PNG
    phrase_pngs = []
    for i, ph in enumerate(phrases):
        png = tmp_dir / f"caption_{i}.png"
        _render_text_png(
            ph["text"],
            png,
            font_size=style["font_size"],
            padding=22,
            max_width=900,
            bg_alpha=style["bg_alpha"],
            text_color=style["text_color"],
            bg_color=style["bg_color"],
        )
        phrase_pngs.append(png)

    watermark_png = None
    if with_watermark:
        watermark_png = tmp_dir / "watermark.png"
        _render_text_png("Made with VoiceClip", watermark_png,
                         font_size=38, padding=16, max_width=900, bg_alpha=200)

    # Build inputs: video/image, audio, captions, optional watermark
    if is_image_bg:
        # Single image looped at 25fps for the audio duration
        inputs = [
            "-loop", "1", "-framerate", "25", "-i", str(video_path),
            "-i", str(audio_path),
        ]
    else:
        inputs = [
            "-stream_loop", "-1", "-i", str(video_path),
            "-i", str(audio_path),
        ]
    for png in phrase_pngs:
        inputs += ["-i", str(png)]
    if watermark_png:
        inputs += ["-i", str(watermark_png)]

    # Filtergraph: prepare background, then overlay each phrase, then watermark.
    # For images we apply a slow Ken-Burns zoom (zoompan) so the still has
    # gentle motion. Pre-scale to a large canvas so zoompan has resolution
    # to crop into without softening.
    if is_image_bg and animate_image:
        total_frames = max(25, int(duration * 25))
        zoom_target = 1.18  # final zoom factor at end of clip
        zoom_step = (zoom_target - 1.0) / max(1, total_frames - 1)
        bg_filter = (
            "scale=2160:3840:force_original_aspect_ratio=increase,"
            "crop=2160:3840,"
            f"zoompan=z='1+{zoom_step:.6f}*on'"
            f":x='iw/2-(iw/zoom)/2':y='ih/2-(ih/zoom)/2'"
            f":d={total_frames}:s=1080x1920:fps=25"
        )
    else:
        bg_filter = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"
    parts = [f"[0:v]{bg_filter}[bg]"]
    current_label = "bg"
    caption_y_expr = _CAPTION_Y_BY_POSITION.get(style["position"], _CAPTION_Y_BY_POSITION["bottom"])
    for i, ph in enumerate(phrases):
        png_idx = 2 + i
        next_label = f"v{i+1}"
        parts.append(
            f"[{current_label}][{png_idx}:v]overlay=(W-w)/2:{caption_y_expr}"
            f":enable='between(t,{ph['start']:.3f},{ph['end']:.3f})'"
            f"[{next_label}]"
        )
        current_label = next_label

    if watermark_png:
        wm_idx = 2 + len(phrase_pngs)
        wm_start = max(0.0, duration - 1.5)
        parts.append(
            f"[{current_label}][{wm_idx}:v]overlay=(W-w)/2:H-h-110"
            f":enable='gte(t,{wm_start:.2f})'"
            "[vfinal]"
        )
        final_label = "vfinal"
    else:
        final_label = current_label

    filtergraph = ";".join(parts)

    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filtergraph,
        "-map", f"[{final_label}]", "-map", "1:a",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-t", f"{duration:.2f}",
        "-shortest",
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg failed: {result.stderr[-1000:]}")
    return output_path
